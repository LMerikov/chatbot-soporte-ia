#!/bin/bash

echo "🚀 INICIANDO MIGRACIÓN A CHATBOT v2.0 PROFESIONAL"
echo "=================================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paso 1: Backup
echo "📦 Paso 1: Creando backup de archivos actuales..."
if [ -f "index.html" ]; then
    cp index.html index.html.backup
    echo -e "${GREEN}✅ Backup de index.html creado${NC}"
fi

if [ -f "app.py" ]; then
    cp app.py app.py.backup
    echo -e "${GREEN}✅ Backup de app.py creado${NC}"
fi

if [ -f "requirements.txt" ]; then
    cp requirements.txt requirements.txt.backup
    echo -e "${GREEN}✅ Backup de requirements.txt creado${NC}"
fi

echo ""

# Paso 2: Crear archivo de feedback si no existe
echo "📝 Paso 2: Creando archivos necesarios..."
if [ ! -f "feedback.jsonl" ]; then
    touch feedback.jsonl
    echo -e "${GREEN}✅ feedback.jsonl creado${NC}"
fi

echo ""

# Paso 3: Actualizar requirements
echo "📋 Paso 3: Actualizando requirements.txt..."
if [ -f "requirements_new.txt" ]; then
    cp requirements_new.txt requirements.txt
    echo -e "${GREEN}✅ requirements.txt actualizado${NC}"
fi

echo ""

# Paso 4: Actualizar backend
echo "🔧 Paso 4: Actualizando backend..."
if [ -f "app_improved.py" ]; then
    # Renombrar el viejo
    if [ -f "app.py" ]; then
        mv app.py app_old.py
        echo -e "${YELLOW}⚠️  app.py antiguo renombrado a app_old.py${NC}"
    fi

    # Copiar el nuevo
    cp app_improved.py app.py
    echo -e "${GREEN}✅ Backend actualizado a versión 2.0${NC}"
fi

echo ""

# Paso 5: Verificar .env
echo "⚙️  Paso 5: Verificando configuración..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example.new" ]; then
        cp .env.example.new .env
        echo -e "${YELLOW}⚠️  .env creado desde template${NC}"
        echo -e "${RED}⚠️  IMPORTANTE: Edita .env y agrega tu OPENAI_API_KEY${NC}"
    else
        echo -e "${RED}❌ No se encontró .env.example.new${NC}"
    fi
else
    echo -e "${GREEN}✅ .env ya existe${NC}"
fi

echo ""

# Paso 6: Verificar estructura de carpetas
echo "📁 Paso 6: Verificando estructura de carpetas..."
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}✅ Carpeta logs creada${NC}"
fi

if [ -d "frontend" ]; then
    echo -e "${GREEN}✅ Carpeta frontend existe${NC}"
else
    echo -e "${RED}❌ Carpeta frontend no encontrada${NC}"
fi

echo ""

# Paso 7: Verificar que Python tiene los módulos necesarios
echo "🐍 Paso 7: Verificando dependencias Python..."
echo -e "${YELLOW}Instalando dependencias...${NC}"

if command -v pip3 &> /dev/null; then
    pip3 install -q -r requirements.txt 2>&1 | grep -i "error" || echo -e "${GREEN}✅ Dependencias instaladas${NC}"
elif command -v pip &> /dev/null; then
    pip install -q -r requirements.txt 2>&1 | grep -i "error" || echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${RED}❌ pip no encontrado${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ MIGRACIÓN COMPLETADA${NC}"
echo "=================================================="
echo ""
echo "📝 Próximos pasos:"
echo "1. Edita .env y agrega tu OPENAI_API_KEY"
echo "2. Ejecuta: python app.py (o python3 app.py)"
echo "3. Abre: frontend/index.html en tu navegador"
echo ""
echo "📚 Documentación:"
echo "- IMPROVEMENTS.md    → Lista de todas las mejoras"
echo "- MIGRATION_GUIDE.md → Guía detallada de migración"
echo ""
echo "🔍 Verificación rápida:"
echo "curl http://localhost:5050/health"
echo ""
