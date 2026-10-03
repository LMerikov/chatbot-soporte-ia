# 📦 GUÍA DE MIGRACIÓN - Chatbot v1.0 → v2.0

## 🎯 Resumen

Esta guía te ayudará a migrar de la versión básica a la **versión profesional** del chatbot.

---

## 📋 PASO 1: Backup de Archivos Actuales

```bash
# Crear backup del index.html actual
cp index.html index.html.backup

# Crear backup de app.py actual
cp app.py app.py.backup

echo "✅ Backup creado"
```

---

## 📋 PASO 2: Instalar Nuevas Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar nuevas dependencias
pip install -r requirements_new.txt

# Verificar instalación
pip list | grep -E "flask-limiter|rapidfuzz|bleach"
```

**Dependencias nuevas:**
- `flask-limiter` → Rate limiting
- `rapidfuzz` → Fuzzy search
- `bleach` → Sanitización de inputs

---

## 📋 PASO 3: Mover Archivos Frontend

```bash
# Los archivos ya están en frontend/
# Solo necesitas actualizar la ruta en tu servidor

# Si usabas index.html en la raíz:
# Ahora usa: frontend/index.html

# Estructura nueva:
# frontend/
#   ├── index.html
#   ├── css/styles.css
#   ├── js/config.js
#   └── js/chat.js
```

---

## 📋 PASO 4: Actualizar Backend

### Opción A: Reemplazar app.py (Recomendado)

```bash
# Renombrar el actual
mv app.py app_old.py

# Usar el nuevo
mv app_improved.py app.py

echo "✅ Backend actualizado"
```

### Opción B: Mantener ambos (para testing)

```bash
# Ejecutar la versión nueva en otro puerto
PORT=5051 python app_improved.py

# Probar con:
# http://localhost:5051/health
```

---

## 📋 PASO 5: Actualizar .env

```bash
# Copiar el nuevo ejemplo
cp .env.example.new .env

# Editar con tu API key
nano .env
```

**Contenido mínimo del .env:**
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
PORT=5050
ALLOWED_ORIGINS=*
```

---

## 📋 PASO 6: Actualizar requirements.txt

```bash
# Reemplazar requirements.txt
cp requirements_new.txt requirements.txt

echo "✅ Requirements actualizado"
```

---

## 📋 PASO 7: Probar la Nueva Versión

### 7.1 Iniciar Backend

```bash
python app.py
```

**Deberías ver:**
```
🚀 Iniciando chatbot con OpenAI GPT-4o Mini...
💰 Modelo: gpt-4o-mini
🔍 Búsqueda mejorada con Fuzzy Matching
📚 Cargando base de conocimiento...
✅ Base de conocimiento cargada: 29 documentos
✅ Servidor iniciado correctamente
🌐 Accede en: http://localhost:5050
```

### 7.2 Abrir Frontend

```bash
# Opción 1: Doble click en el archivo
open frontend/index.html

# Opción 2: Servidor HTTP
cd frontend
python3 -m http.server 8000
# Ir a: http://localhost:8000
```

### 7.3 Verificar Endpoints

```bash
# Health check
curl http://localhost:5050/health

# Debería responder:
# {
#   "status": "ok",
#   "knowledge_base_size": 29,
#   "cache_size": X,
#   "total_queries": 0,
#   "uptime": X.X
# }
```

---

## 📋 PASO 8: Verificar Funcionalidades

### Checklist de Verificación

- [ ] Widget se abre/cierra correctamente
- [ ] Mensajes se guardan en historial
- [ ] Botón "Borrar historial" funciona
- [ ] Botón de tema oscuro funciona
- [ ] Efecto de escritura se ve realista
- [ ] Botón de copiar funciona
- [ ] Feedback 👍👎 funciona
- [ ] Exportar conversación funciona
- [ ] Estado de conexión se muestra
- [ ] Preguntas frecuentes aparecen
- [ ] Rate limiting funciona (hacer 11 requests en 1 min)

### Probar Rate Limiting

```bash
# Script para probar rate limit
for i in {1..12}; do
    echo "Request $i"
    curl -X POST http://localhost:5050/chat \
        -H "Content-Type: application/json" \
        -d '{"query": "test"}' \
        -w "\nStatus: %{http_code}\n\n"
    sleep 3
done

# Los primeros 10 deberían funcionar
# El 11 y 12 deberían devolver 429
```

---

## 📋 PASO 9: Migración de Datos (Opcional)

### Si tenías logs antiguos

```bash
# Los nuevos logs se guardan en logs/
# Si quieres migrar logs antiguos:

mkdir -p logs
mv logs/chat_*.jsonl logs/  # Si ya existían

echo "✅ Logs migrados"
```

### Si tenías caché

```bash
# El caché es compatible
# Solo asegúrate que response_cache.json existe
# La nueva versión lo usará automáticamente
```

---

## 🐛 TROUBLESHOOTING

### Error: Module 'flask_limiter' not found

```bash
pip install flask-limiter==3.5.0
```

### Error: Module 'rapidfuzz' not found

```bash
pip install rapidfuzz==3.6.1
```

### Error: CORS not working

**Solución:** Actualiza ALLOWED_ORIGINS en .env

```bash
# Para desarrollo
ALLOWED_ORIGINS=*

# Para producción
ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
```

### Error: CSS/JS no se cargan

**Problema:** Rutas relativas

**Solución:**
1. Abre `frontend/index.html` con un servidor HTTP
2. No abras el archivo directamente con `file://`

```bash
cd frontend
python3 -m http.server 8000
# Ir a http://localhost:8000
```

### El efecto de escritura es muy lento/rápido

**Solución:** Ajusta la velocidad en `frontend/js/config.js`

```javascript
TYPING_SPEED: 20,        // Aumentar = más lento
TYPING_VARIATION: 15,    // Variación aleatoria
```

### Rate limiting muy estricto

**Solución:** Ajusta límites en `app.py`

```python
@app.route('/chat', methods=['POST'])
@limiter.limit("20 per minute")  # Cambiar de 10 a 20
def chat():
    ...
```

---

## 📊 COMPARACIÓN DE ARCHIVOS

| Archivo | Versión Antigua | Versión Nueva | Cambios |
|---------|----------------|---------------|---------|
| `index.html` | 577 líneas | 140 líneas | Modularizado |
| `app.py` | 354 líneas | 450 líneas | +Rate limit, +Fuzzy, +Analytics |
| `requirements.txt` | 5 deps | 9 deps | +flask-limiter, +rapidfuzz, +bleach |

---

## ✅ VERIFICACIÓN FINAL

### Checklist de Migración Completa

- [ ] Backend ejecutándose en puerto 5050
- [ ] Frontend abre sin errores en consola
- [ ] `/health` endpoint responde OK
- [ ] Puedes enviar mensajes
- [ ] Mensajes se guardan en historial
- [ ] Feedback funciona
- [ ] Exportar funciona
- [ ] Tema oscuro funciona
- [ ] Rate limiting funciona
- [ ] Analytics endpoint responde

### Comando de Verificación

```bash
# Verificar que todo funciona
curl http://localhost:5050/health && \
curl http://localhost:5050/analytics && \
echo "✅ Backend funcionando correctamente"
```

---

## 🚀 DEPLOYMENT A PRODUCCIÓN

### Antes de ir a producción:

1. **Actualizar ALLOWED_ORIGINS**
```bash
ALLOWED_ORIGINS=https://tu-dominio.com
```

2. **Usar servidor WSGI**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5050 app:app
```

3. **Configurar HTTPS**
```bash
# Usar nginx como reverse proxy
# Configurar certificado SSL
```

4. **Habilitar logging en producción**
```python
# En app.py
logger.setLevel(logging.WARNING)  # Solo warnings y errores
```

5. **Configurar rate limits apropiados**
```python
# Según tu tráfico esperado
@limiter.limit("100 per hour")
```

---

## 📞 SOPORTE

Si encuentras problemas durante la migración:

1. Revisa los logs en `logs/app.log`
2. Verifica la consola del navegador (F12)
3. Consulta `IMPROVEMENTS.md` para detalles técnicos

---

## 🎉 MIGRACIÓN COMPLETADA

¡Felicidades! Ahora tienes un chatbot de nivel **profesional** con:

✅ Historial persistente
✅ Feedback de usuarios
✅ Rate limiting
✅ Búsqueda mejorada
✅ Modo oscuro
✅ Exportar conversaciones
✅ Analytics
✅ Y mucho más...

**Versión:** 2.0 Professional
**Última actualización:** Noviembre 2025
