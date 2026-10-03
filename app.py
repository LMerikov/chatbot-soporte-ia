from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI
import json
import os
from datetime import datetime
import unicodedata
import re
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from rapidfuzz import fuzz

# Cargar variables de entorno
load_dotenv()

# ====================
# CONFIGURACIÓN
# ====================
app = Flask(__name__)

# CORS mejorado (más seguro)
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, resources={
    r"/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY no encontrada en el archivo .env")
    print("📝 Por favor configura tu API key en el archivo .env")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# Archivos
KNOWLEDGE_FILE = 'conocimiento.txt'
CACHE_FILE = 'response_cache.json'
EXACT_RESPONSES_FILE = 'respuestas_exactas.json'
FEEDBACK_FILE = 'feedback.jsonl'
LOG_DIR = 'logs'

# ====================
# LOGGING ESTRUCTURADO
# ====================
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logger
handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=10000000,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# También log a consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(console_handler)

# ====================
# INICIALIZACIÓN
# ====================
knowledge_base = []
analytics = {
    'total_queries': 0,
    'total_feedback': 0,
    'positive_feedback': 0,
    'negative_feedback': 0,
    'start_time': datetime.now().isoformat()
}

logger.info("🚀 Iniciando chatbot con OpenAI GPT-4o Mini...")
logger.info("💰 Modelo: gpt-4o-mini")
logger.info("🔍 Búsqueda mejorada con Fuzzy Matching")

# ====================
# FUNCIONES DE NORMALIZACIÓN
# ====================
def normalize_text(text):
    """Normaliza texto para búsqueda"""
    text = text.lower().strip()
    # Remover acentos
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text

def sanitize_query(query):
    """Limpia y valida el input del usuario"""
    if not query or not isinstance(query, str):
        return None

    # Remover HTML tags
    query = re.sub(r'<[^>]+>', '', query)

    # Limitar longitud
    query = query[:500]

    # Remover caracteres peligrosos
    query = re.sub(r'[<>{}\\]', '', query)

    return query.strip()

# ====================
# CARGA DE BASE DE CONOCIMIENTO
# ====================
def load_knowledge_base():
    """Carga el archivo de conocimiento SIN generar embeddings"""
    global knowledge_base

    if not os.path.exists(KNOWLEDGE_FILE):
        logger.error(f"❌ No se encontró {KNOWLEDGE_FILE}")
        return

    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ignorar comentarios ("# ..."), pero conservar los encabezados "### Título"
    content = '\n'.join(
        l for l in content.splitlines()
        if not l.lstrip().startswith('#') or l.lstrip().startswith('###')
    )

    # Parsear secciones
    sections = re.split(r'###\s+', content)

    logger.info(f"📚 Cargando base de conocimiento...")

    for section in sections:
        if not section.strip():
            continue

        lines = section.strip().split('\n')
        titulo = lines[0].strip()

        # Buscar línea de temas (keywords:)
        temas = ""
        contenido_lines = []
        for line in lines[1:]:
            if line.lower().startswith('keywords:'):
                temas = line.split(':', 1)[1].strip()
            else:
                contenido_lines.append(line)

        contenido = '\n'.join(contenido_lines).strip()

        if not contenido:
            continue

        # Guardar SIN embeddings
        knowledge_base.append({
            'titulo': titulo,
            'temas': temas,
            'contenido': contenido,
            'titulo_norm': normalize_text(titulo),
            'temas_norm': normalize_text(temas),
            'contenido_norm': normalize_text(contenido)
        })

    logger.info(f"✅ Base de conocimiento cargada: {len(knowledge_base)} documentos")

# ====================
# BÚSQUEDA MEJORADA CON FUZZY MATCHING
# ====================
def improved_keyword_search(query, threshold=30):
    """Búsqueda mejorada usando fuzzy matching y keywords"""
    query_norm = normalize_text(query)
    query_words = set(query_norm.split())

    results = []

    for doc in knowledge_base:
        score = 0.0

        # 1. Fuzzy match en título (peso alto)
        title_ratio = fuzz.ratio(query_norm, doc['titulo_norm'])
        score += title_ratio * 0.4

        # 2. Fuzzy partial ratio en título
        title_partial = fuzz.partial_ratio(query_norm, doc['titulo_norm'])
        score += title_partial * 0.3

        # 3. Fuzzy match en temas/keywords
        if doc['temas_norm']:
            temas_ratio = fuzz.partial_ratio(query_norm, doc['temas_norm'])
            score += temas_ratio * 0.5

        # 4. Keywords exactos en título
        titulo_words = set(doc['titulo_norm'].split())
        titulo_match = len(query_words & titulo_words) / max(len(query_words), 1)
        score += titulo_match * 80

        # 5. Keywords exactos en temas
        if doc['temas_norm']:
            temas_words = set(doc['temas_norm'].split())
            temas_match = len(query_words & temas_words) / max(len(query_words), 1)
            score += temas_match * 60

        # 6. Búsqueda en contenido (peso menor)
        contenido_words = set(doc['contenido_norm'].split())
        contenido_match = len(query_words & contenido_words) / max(len(query_words), 1)
        score += contenido_match * 20

        # 7. Bonus por substring match exacto
        if query_norm in doc['titulo_norm']:
            score += 100
        if query_norm in doc['temas_norm']:
            score += 80
        if query_norm in doc['contenido_norm']:
            score += 30

        if score > threshold:
            results.append((score, doc))

    # Ordenar por score descendente
    results.sort(key=lambda x: x[0], reverse=True)

    return [doc for score, doc in results[:3]]  # Top 3 resultados

# ====================
# CACHÉ Y RESPUESTAS EXACTAS
# ====================
def load_cache():
    """Carga caché de respuestas"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}
    return {}

def save_cache(cache_data):
    """Guarda caché de respuestas"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def load_exact_responses():
    """Carga respuestas exactas predefinidas"""
    if os.path.exists(EXACT_RESPONSES_FILE):
        try:
            with open(EXACT_RESPONSES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading exact responses: {e}")
            return {}
    return {}

response_cache = load_cache()
exact_responses = load_exact_responses()

def get_exact_response(query):
    """Busca respuesta exacta predefinida"""
    query_norm = normalize_text(query)

    for key, response in exact_responses.items():
        if normalize_text(key) == query_norm:
            return response
    return None

# ====================
# LOGGING DE CONVERSACIONES
# ====================
def log_conversation(query, response, context_used):
    """Guarda log de la conversación"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': response[:200],  # Solo primeros 200 chars
        'context_used': context_used
    }

    log_file = os.path.join(LOG_DIR, f"chat_{datetime.now().strftime('%Y%m%d')}.jsonl")
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.error(f"Error logging conversation: {e}")

# ====================
# GENERACIÓN DE RESPUESTA
# ====================
def generate_response(query):
    """Genera respuesta usando OpenAI GPT-4o Mini"""

    # 1. Verificar respuestas exactas
    exact_response = get_exact_response(query)
    if exact_response:
        log_conversation(query, exact_response, "Respuesta exacta")
        return exact_response

    # 2. Verificar caché
    query_norm = normalize_text(query)
    if query_norm in response_cache:
        cached_response = response_cache[query_norm]
        log_conversation(query, cached_response, "Caché")
        return cached_response

    # 3. Buscar en base de conocimiento (FUZZY MATCHING)
    relevant_docs = improved_keyword_search(query)

    # 4. Construir contexto
    context = ""
    if relevant_docs:
        context = "\n\n".join([
            f"### {doc['titulo']}\n{doc['contenido']}"
            for doc in relevant_docs
        ])

    # 5. Construir prompt
    if context:
        prompt = f"""Eres un asistente de soporte técnico para la Universidad de los Andes y Clínica Uandes.

Contexto relevante de la base de conocimiento:
{context}

Pregunta del usuario: {query}

Instrucciones:
- Responde de forma clara, concisa y profesional
- Usa SOLO la información del contexto proporcionado
- Si hay URLs o links en el contexto, inclúyelos en tu respuesta con formato [texto](url)
- Usa negritas **texto** para resaltar información importante
- Si la pregunta no se puede responder con el contexto, di que no tienes esa información
- Sé amable y servicial

Respuesta:"""
    else:
        prompt = f"""Eres un asistente de soporte técnico para la Universidad de los Andes y Clínica Uandes.

Pregunta del usuario: {query}

No encontré información específica en la base de conocimiento sobre este tema.
Por favor, proporciona una respuesta general y amable, sugiriendo contactar al área de soporte correspondiente.

Respuesta:"""

    # 6. Generar respuesta con OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente de soporte técnico profesional y amable."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )

        answer = response.choices[0].message.content.strip()

        # Guardar en caché
        response_cache[query_norm] = answer
        save_cache(response_cache)

        # Log
        context_info = f"{len(relevant_docs)} documentos" if relevant_docs else "Sin contexto"
        log_conversation(query, answer, context_info)

        return answer

    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}", exc_info=True)
        return "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta nuevamente."

# ====================
# RUTAS DE LA API
# ====================
@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    return jsonify({
        'status': 'ok',
        'knowledge_base_size': len(knowledge_base),
        'cache_size': len(response_cache),
        'total_queries': analytics['total_queries'],
        'uptime': (datetime.now() - datetime.fromisoformat(analytics['start_time'])).total_seconds()
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
@limiter.limit("10 per minute")
def chat():
    """Endpoint principal del chat"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        # Validar y sanitizar
        query = sanitize_query(query)

        if not query:
            return jsonify({'error': 'Query vacío o inválido'}), 400

        if len(query) < 3:
            return jsonify({'error': 'Query muy corto (mínimo 3 caracteres)'}), 400

        logger.info(f"Query recibida: {query[:100]}")

        # Actualizar analytics
        analytics['total_queries'] += 1

        # Generar respuesta
        response_text = generate_response(query)

        # Streaming response
        def generate():
            for char in response_text:
                yield json.dumps({'token': char}) + '\n'

        return Response(generate(), mimetype='application/json')

    except Exception as e:
        logger.error(f"Error en /chat: {e}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/feedback', methods=['POST', 'OPTIONS'])
@limiter.limit("20 per minute")
def feedback():
    """Endpoint para recibir feedback del usuario"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        feedback_type = data.get('feedback')
        message = data.get('message', '')
        timestamp = data.get('timestamp', datetime.now().isoformat())

        if feedback_type not in ['positive', 'negative']:
            return jsonify({'error': 'Feedback inválido'}), 400

        # Guardar feedback
        feedback_entry = {
            'timestamp': timestamp,
            'feedback': feedback_type,
            'message': message[:100]
        }

        with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')

        # Actualizar analytics
        analytics['total_feedback'] += 1
        if feedback_type == 'positive':
            analytics['positive_feedback'] += 1
        else:
            analytics['negative_feedback'] += 1

        logger.info(f"Feedback recibido: {feedback_type}")

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Error en /feedback: {e}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Endpoint de analytics (solo para admin)"""
    try:
        satisfaction_rate = 0
        if analytics['total_feedback'] > 0:
            satisfaction_rate = (analytics['positive_feedback'] / analytics['total_feedback']) * 100

        return jsonify({
            'total_queries': analytics['total_queries'],
            'total_feedback': analytics['total_feedback'],
            'positive_feedback': analytics['positive_feedback'],
            'negative_feedback': analytics['negative_feedback'],
            'satisfaction_rate': f"{satisfaction_rate:.1f}%",
            'knowledge_base_docs': len(knowledge_base),
            'cache_size': len(response_cache),
            'uptime_hours': (datetime.now() - datetime.fromisoformat(analytics['start_time'])).total_seconds() / 3600
        })
    except Exception as e:
        logger.error(f"Error en /analytics: {e}", exc_info=True)
        return jsonify({'error': 'Error interno del servidor'}), 500

# ====================
# ERROR HANDLERS
# ====================
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handler para rate limit"""
    logger.warning(f"Rate limit excedido: {request.remote_addr}")
    return jsonify({'error': 'Demasiadas solicitudes. Por favor espera un momento.'}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handler para errores internos"""
    logger.error(f"Error interno: {str(e)}", exc_info=True)
    return jsonify({'error': 'Error interno del servidor'}), 500

# ====================
# INICIALIZACIÓN Y EJECUCIÓN
# ====================
if __name__ == '__main__':
    # Cargar base de conocimiento
    load_knowledge_base()

    # Obtener puerto
    port = int(os.getenv('PORT', 5050))

    logger.info(f"\n✅ Servidor iniciado correctamente")
    logger.info(f"🌐 Accede en: http://localhost:{port}")
    logger.info(f"📱 Abre frontend/index.html en tu navegador para usar el widget\n")

    # Iniciar servidor
    app.run(host='0.0.0.0', port=port, debug=False)
