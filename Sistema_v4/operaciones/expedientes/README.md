# Migración de expedientes a Sistema_v4

Este directorio concentra la migración progresiva de los módulos de expedientes hacia la nueva arquitectura `Sistema_v4`.

## Objetivos de la migración
- Adaptar los procesos de extracción y gestión de expedientes a los nuevos requisitos técnicos.
- Mejorar la organización modular para facilitar el mantenimiento y las pruebas automatizadas.
- Documentar cada componente modernizado para acelerar la incorporación de nuevos equipos.

## Diferencias clave respecto de `Sistema_v3`
- Uso de rutas de importación basadas en `Sistema_v4`, manteniendo compatibilidad temporal con `Sistema_v3` durante la transición.
- Separación explícita de auxiliares y pruebas dentro de `operaciones/expedientes` para clarificar el alcance de cada módulo.
- Posibilidad de coexistencia entre versiones, permitiendo alternar rápidamente entre implementaciones según el estado de la migración.

A medida que se incorporen nuevos módulos (`expedientes_v4.py`, auxiliares, pruebas), deberán ubicarse aquí y actualizar esta documentación con sus detalles específicos.
