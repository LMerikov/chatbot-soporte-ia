# 🤖 Chatbot de Soporte Técnico - OpenAI Version

## 📋 Descripción

Widget flotante de chatbot para soporte técnico usando **OpenAI GPT-4o Mini**.

### ✨ Características

- ✅ Widget flotante estilo Chatbase
- ✅ Diseño personalizado (botón negro, header gris, fondo blanco)
- ✅ Links azules clicables
- ✅ Formato markdown (negritas, listas, saltos de línea)
- ✅ Búsqueda por keywords (sin embeddings)
- ✅ Streaming de respuestas en tiempo real
- ✅ Sistema de caché
- ✅ Respuestas predefinidas
- ✅ Logging automático

---

## 💰 Costos Estimados

### OpenAI GPT-4o Mini
- **Input:** $0.150 / 1M tokens
- **Output:** $0.600 / 1M tokens

**Para 1000 consultas/mes:**
- Input promedio: 200 tokens = 0.2M tokens × $0.150 = **$0.03**
- Output promedio: 300 tokens = 0.3M tokens × $0.600 = **$0.18**
- **Total: ~$0.21/mes** ($2.52/año)

---

## 🚀 Instalación

### 1. Requisitos

- Python 3.8+
- Cuenta de OpenAI
- API Key de OpenAI

### 2. Obtener API Key

1. Ir a: https://platform.openai.com/api-keys
2. Click en "Create new secret key"
3. Copiar la key (empieza con `sk-...`)

### 3. Instalar

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install httpx==0.27.2

# Configurar API key
cp .env.example .env
nano .env
# Agregar: OPENAI_API_KEY=sk-...
```

### 4. Ejecutar

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar backend
python3 app.py
```

### 5. Abrir Frontend

```bash
# En tu navegador, abrir:
open index.html

# O con servidor HTTP:
python3 -m http.server 8000
# Ir a: http://localhost:8000
```

---

## 📁 Estructura de Archivos

```
chatbot-openai-widget/
├── app.py                      # Backend con OpenAI
├── index.html                  # Frontend (widget)
├── conocimiento.txt            # Base de conocimiento (29 temas)
├── requirements.txt            # Dependencias Python
├── .env                        # Configuración (no incluido)
├── .env.example               # Plantilla de configuración
├── respuestas_exactas.json    # Respuestas predefinidas
├── response_cache.json        # Caché de respuestas
├── logs/                      # Logs de conversaciones
└── README.md                  # Esta documentación
```

---

## 🎨 Diseño del Widget

### Colores

- **Botón flotante:** Negro (#1a1a1a)
- **Header:** Gris oscuro (#2c2c2c)
- **Fondo mensajes:** Blanco (#ffffff)
- **Mensaje bot:** Gris (#e8e8e8) con texto negro
- **Mensaje usuario:** Negro con texto blanco
- **Links:** Azul (#0066cc) subrayados
- **Input área:** Blanco (#ffffff)

### Formato Soportado

- ✅ **Negritas:** `**texto**`
- ✅ **Cursiva:** `*texto*`
- ✅ **Links:** `[texto](url)` o URLs directas
- ✅ **Listas:** `* item` o `- item`
- ✅ **Saltos de línea:** `\n`

---

## 🔧 Configuración

### Archivo .env

```bash
OPENAI_API_KEY=sk-your-key-here
PORT=5050
```

### Cambiar Puerto

```bash
# En .env
PORT=8080
```

### Base de Conocimiento

Editar `conocimiento.txt` con formato:

```
### Título del Tema
Keywords: palabra1, palabra2, palabra3

Contenido del tema aquí...
Puede incluir múltiples líneas.
```

---

## 🧪 Pruebas

```bash
# Consulta de prueba
curl -X POST http://localhost:5050/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "canvas"}'

# Health check
curl http://localhost:5050/health
```

---

## 📊 Comparación vs Gemini

| Característica | OpenAI GPT-4o Mini | Gemini 2.5 Flash |
|----------------|-------------------|------------------|
| **Costo/1000 consultas** | ~$0.21/mes | GRATIS |
| **Calidad** | Excelente | Excelente |
| **Latencia** | ~500ms | ~300ms |
| **Límites** | Alta cuota | 1,500 req/día gratis |
| **Embedding** | No usado | No usado |

---

## 🆘 Troubleshooting

### Error: API key not valid

```bash
# Verificar .env
cat .env

# Debe tener:
OPENAI_API_KEY=sk-...

# NO:
OPENAI_API_KEY=your_api_key_here
```

### Error: Module not found

```bash
# Activar entorno virtual
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Widget no se conecta

```bash
# Verificar backend corriendo
curl http://localhost:5050/health

# Debe responder:
{"status": "ok", ...}
```

---

## 📝 Licencia

Uso interno - Universidad de los Andes / Clínica Uandes

---

## 🤝 Soporte

Para problemas o preguntas, contactar al equipo de soporte técnico.
