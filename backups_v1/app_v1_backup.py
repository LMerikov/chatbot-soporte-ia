from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os
from datetime import datetime
import unicodedata
import re
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# ====================
# CONFIGURACIÓN
# ====================
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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
LOG_DIR = 'logs'

# ====================
# INICIALIZACIÓN
# ====================
os.makedirs(LOG_DIR, exist_ok=True)

# Base de conocimiento (SIN embeddings)
knowledge_base = []

print("🚀 Iniciando chatbot con OpenAI GPT-4o Mini...")
print("💰 Modelo: gpt-4o-mini")
print("🔍 Búsqueda por keywords (SIN embeddings para evitar costos)")

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

# ====================
# CARGA DE BASE DE CONOCIMIENTO (SIN EMBEDDINGS)
# ====================
def load_knowledge_base():
    """Carga el archivo de conocimiento SIN generar embeddings"""
    global knowledge_base
    
    if not os.path.exists(KNOWLEDGE_FILE):
        print(f"❌ No se encontró {KNOWLEDGE_FILE}")
        return
    
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parsear secciones
    sections = re.split(r'###\s+', content)
    
    print(f"📚 Cargando base de conocimiento...")
    
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
    
    print(f"✅ Base de conocimiento cargada: {len(knowledge_base)} documentos")

# ====================
# BÚSQUEDA POR KEYWORDS (SIN EMBEDDINGS)
# ====================
def keyword_search(query, threshold=0.3):
    """Busca documentos relevantes usando solo keywords"""
    query_norm = normalize_text(query)
    query_words = set(query_norm.split())
    
    results = []
    
    for doc in knowledge_base:
        score = 0.0
        
        # Buscar en título (peso 3.0)
        titulo_words = set(doc['titulo_norm'].split())
        titulo_match = len(query_words & titulo_words) / max(len(query_words), 1)
        score += titulo_match * 3.0
        
        # Buscar en temas/keywords (peso 2.0)
        if doc['temas_norm']:
            temas_words = set(doc['temas_norm'].split())
            temas_match = len(query_words & temas_words) / max(len(query_words), 1)
            score += temas_match * 2.0
        
        # Buscar en contenido (peso 0.5)
        contenido_words = set(doc['contenido_norm'].split())
        contenido_match = len(query_words & contenido_words) / max(len(query_words), 1)
        score += contenido_match * 0.5
        
        # Bonus por substring match
        if query_norm in doc['titulo_norm']:
            score += 1.0
        if query_norm in doc['temas_norm']:
            score += 0.8
        if query_norm in doc['contenido_norm']:
            score += 0.3
        
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
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    """Guarda caché de respuestas"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def load_exact_responses():
    """Carga respuestas exactas predefinidas"""
    if os.path.exists(EXACT_RESPONSES_FILE):
        with open(EXACT_RESPONSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
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
# LOGGING
# ====================
def log_conversation(query, response, context_used):
    """Guarda log de la conversación"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': response,
        'context_used': context_used
    }
    
    log_file = os.path.join(LOG_DIR, f"chat_{datetime.now().strftime('%Y%m%d')}.jsonl")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

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
    
    # 3. Buscar en base de conocimiento (KEYWORDS ONLY)
    relevant_docs = keyword_search(query)
    
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
- Si hay URLs o links en el contexto, inclúyelos en tu respuesta
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
        error_msg = f"❌ Error generando respuesta: {str(e)}"
        print(error_msg)
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
        'cache_size': len(response_cache)
    })

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Endpoint principal del chat"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query vacío'}), 400
        
        # Generar respuesta
        response_text = generate_response(query)
        
        # Streaming response
        def generate():
            for char in response_text:
                yield json.dumps({'token': char}) + '\n'
        
        return Response(generate(), mimetype='application/json')
        
    except Exception as e:
        print(f"❌ Error en /chat: {e}")
        return jsonify({'error': str(e)}), 500

# ====================
# INICIALIZACIÓN Y EJECUCIÓN
# ====================
if __name__ == '__main__':
    # Cargar base de conocimiento
    load_knowledge_base()
    
    # Obtener puerto
    port = int(os.getenv('PORT', 5050))
    
    print(f"\n✅ Servidor iniciado correctamente")
    print(f"🌐 Accede en: http://localhost:{port}")
    print(f"📱 Abre index.html en tu navegador para usar el widget\n")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=port, debug=False)
