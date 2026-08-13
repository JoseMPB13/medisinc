---
trigger: always_on
---

REGLAS DEL AGENTE DE IA (ANTI-GRAVITY IDE) - PROYECTO MEDISINC-IA
1. Misión y Contexto del Proyecto
Eres el asistente de desarrollo del proyecto MediSinc-IA, un sistema inteligente de pre-triaje clínico y resumen asistido por IA para centros de salud en Santa Cruz de la Sierra, Bolivia. Toda la especificación técnica funcional, arquitectura de software, stack de tecnologías y modelos de datos se encuentran detallados en el archivo local ESPECIFICACIÓN TÉCNICA DEFINITIVA DE SOFTWARE.md (o README.md). Debes consultar este archivo como la fuente de verdad absoluta para guiarte en cada tarea.

2. Principios de Arquitectura y Buenas Prácticas
Código Mantenible, Sostenible y Flexible:

Sigue principios SOLID, DRY (Don't Repeat Yourself) y Clean Code.
Aplica una arquitectura por capas en el Backend FastAPI (api/, core/, models/, schemas/, services/, providers/, workers/).
Aplica el patrón Adapter / Factory para la capa de Inteligencia Artificial (AI Provider Abstraction), permitiendo alternar entre proveedores (Gemini 1.5 Flash, Groq, OpenAI) mediante variables de entorno sin alterar la lógica de negocio.
Mantén los componentes del Frontend React organizados, reutilizables y tipados/estructurados modularmente (components/, pages/, services/, hooks/, layouts/).
Comentarios y Documentación:

TODO el código debe estar comentado en español.
Explica brevemente la responsabilidad de cada función, clase, módulo o endpoint clave, detallando qué hace, cuáles son sus entradas, salidas y consideraciones de seguridad.
Gestión de Entorno y Seguridad (.env y .gitignore):

NUNCA subas o expongas credenciales, llaves API, tokens o secretos en el código fuente.
Utiliza siempre archivos .env para la lectura de variables de entorno (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GEMINI_API_KEY, AES_SECRET_KEY, HMAC_PEPPER_KEY, etc.).
Asegúrate de mantener un archivo .gitignore robusto que ignore .env, node_modules/, venv/, __pycache__/, build folders y archivos temporales. Proporciona un archivo .env.example con variables de plantilla sin valores sensibles.
3. Control de Versiones y Git (GitHub Workflow)
Configuración del Repositorio Remoto:
URL del repositorio objetivo: https://github.com/JoseMPB13/medisinc.git
Antes de iniciar el desarrollo, verifica y configura el origen remoto del repositorio local:
git remote add origin https.://github.com/JoseMPB13/medisinc.git  # o git remote set-url origin
Flujo de Commits:
Después de completar cada cambio, módulo o funcionalidad lógica, debes realizar un commit y push al repositorio.
Todos los mensajes de commit deben escribirse en español, siguiendo la convención de Conventional Commits:
feat: ... (nuevas características)
fix: ... (corrección de errores)
docs: ... (documentación o archivo MD)
style: ... (formato, CSS, diseño)
refactor: ... (mejora de código sin cambiar funcionalidad)
chore: ... (configuración de repo, gitignore, env)
Ejemplo de flujo de comandos:
git add .
git commit -m "feat: implementar formulario hibrido de captura con soporte QR"
git push origin main
4. Estructura Básica del Proyecto
Garantiza que la estructura del directorio se mantenga ordenada:

medisinc/
├── .gitignore
├── .env.example
├── ESPECIFICACIÓN TÉCNICA DEFINITIVA DE SOFTWARE.md
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── providers/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   ├── hooks/
    │   └── App.jsx
    ├── package.json
    └── vite.config.js