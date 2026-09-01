"""
Módulo de Test Doubles y Fakes para la Suite de Pruebas.
"""

from pruebas.fakes.fakes_repositorios import (
    RepositorioTriajeEnMemoria,
    RepositorioPacientesEnMemoria,
    RepositorioMedicosEnMemoria,
    RepositorioAuditoriaEnMemoria
)

__all__ = [
    "RepositorioTriajeEnMemoria",
    "RepositorioPacientesEnMemoria",
    "RepositorioMedicosEnMemoria",
    "RepositorioAuditoriaEnMemoria"
]
