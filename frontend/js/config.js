/**
 * Configuración del Chatbot
 */

const config = {
    // API Configuration
    // Si se abre con file:// o localhost, usar localhost:5050
    API_URL: window.location.protocol === 'file:' ||
             window.location.hostname === 'localhost' ||
             window.location.hostname === '127.0.0.1' ||
             window.location.hostname === ''
        ? 'http://localhost:5050'
        : 'https://api.uandes.cl',

    // Timeouts y Retry
    REQUEST_TIMEOUT: 30000, // 30 segundos
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000, // 1 segundo inicial

    // LocalStorage
    STORAGE_KEY_HISTORY: 'chatbot_history',
    STORAGE_KEY_THEME: 'chatbot_theme',
    STORAGE_KEY_NOTIFICATIONS: 'chatbot_notifications',
    MAX_HISTORY_MESSAGES: 100,

    // UI
    TYPING_SPEED: 8, // ms por carácter (más bajo = más rápido)
    TYPING_VARIATION: 8, // variación aleatoria en ms
    CONNECTION_CHECK_INTERVAL: 30000, // 30 segundos

    // Preguntas frecuentes
    QUICK_QUESTIONS: [
        {
            icon: '🔧',
            text: 'BiosLIS',
            query: '¿Cómo instalar BiosLIS?'
        },
        {
            icon: '📧',
            text: 'Outlook',
            query: 'Problemas con Outlook'
        },
        {
            icon: '📞',
            text: 'Anexos',
            query: '¿Cómo configurar un anexo?'
        },
        {
            icon: '🔐',
            text: 'VPN',
            query: '¿Cómo instalar la VPN?'
        },
        {
            icon: '💼',
            text: 'SAP',
            query: '¿Cómo acceder a SAP?'
        },
        {
            icon: '📚',
            text: 'Canvas',
            query: 'Problemas con Canvas'
        }
    ],

    // Temas conocidos para sugerencias
    KNOWN_TOPICS: [
        'BiosLIS', 'SAP', 'Canvas', 'Outlook', 'Anexo', 'VPN',
        'Power BI', 'Totalpack', 'QMS', 'SKED', 'Reflex',
        'Fractal', 'Buk', 'CESA', 'Avaya', 'SmartView',
        'Banner ADP', 'Mi Uandes', 'Success Factors', 'Astra'
    ]
};

// Hacer config disponible globalmente
window.chatConfig = config;
