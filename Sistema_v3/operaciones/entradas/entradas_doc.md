# 📄 Documentación Mejorada: `entradas.py`

Este módulo maneja la **extracción y gestión de notificaciones electrónicas** (cédulas, DEO).

## Funciones

### `extraer_entradas(page, destino=None)`
- Recorre el panel de notificaciones y extrae nuevas entradas evitando duplicados.
- **Archivos generados:**
  - `historial_notificaciones.json`
  - `historial_notificaciones.csv`
- **Formato de notificación:**
```json
{
  "numero": "FRE 1234/2021",
  "caratula": "PEREZ, ANA c/ ESTADO",
  "fecha": "2025-05-21",
  "leida": false,
  "extraida_en": "2025-05-21 10:00:00"
}
```

### `notificaciones_proximas_a_vencer(destino=None, horas=48)`
- Filtra notificaciones cuya fecha cae dentro de las próximas `horas` horas.
- ⚠️ La fecha es la informada por el PJN, no un plazo procesal calculado.

