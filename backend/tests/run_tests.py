"""
Puente de retrocompatibilidad hacia backend/pruebas/ejecutar_pruebas.py
"""

import sys
from pathlib import Path

# Añadir directorio backend al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pruebas.ejecutar_pruebas import ejecutar_bateria_pruebas

if __name__ == "__main__":
    sys.exit(ejecutar_bateria_pruebas())
