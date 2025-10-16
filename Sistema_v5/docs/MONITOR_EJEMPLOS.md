# Monitor PJN v5 - Ejemplos Practicos

Ejemplos de uso comunes del Monitor PJN v5.

## Tabla de Contenidos

- [Configuraciones Comunes](#configuraciones-comunes)
- [Casos de Uso](#casos-de-uso)
- [Scripts Personalizados](#scripts-personalizados)
- [Integraciones](#integraciones)

---

## Configuraciones Comunes

### 1. Monitor solo de entradas (recomendado)

Para usar el monitor solo para notificaciones/entradas:

**config/monitor.json:**
```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "intervalos_laboral_entradas": 10,
  "intervalos_no_laboral_entradas": 30,
  "fecha_desde_entradas": "15/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

**Uso:**
```bash
python scripts/monitor_cli.py --verificar-ahora
```

### 2. Monitor completo (entradas + expedientes)

Para monitorear tanto entradas como expedientes:

**config/monitor.json:**
```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true,
  "intervalos_laboral_entradas": 10,
  "intervalos_laboral_expedientes": 15,
  "fecha_desde_entradas": null,
  "fecha_hasta_entradas": null,
  "fecha_corte_expedientes": "2024-01-01"
}
```

### 3. Monitor de testing (verificacion rapida)

Para testing con intervalos cortos:

**config/monitor.json:**
```json
{
  "modo": "laboral",
  "headless": false,
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "intervalos_laboral_entradas": 5,
  "notificar_nuevas_entradas": true,
  "notificar_errores": true
}
```

**Uso:**
```bash
python scripts/monitor_cli.py --modo laboral --no-headless --verbose
```

### 4. Monitor de produccion (segundo plano)

Para ejecutar en servidor/segundo plano:

**config/monitor.json:**
```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": true,
  "intervalos_laboral_entradas": 15,
  "intervalos_laboral_expedientes": 30,
  "intervalos_no_laboral_entradas": 60,
  "intervalos_no_laboral_expedientes": 120,
  "notificar_errores": true
}
```

**Uso (modo continuo):**
```bash
# Linux/macOS con nohup
nohup python scripts/monitor_cli.py > monitor.log 2>&1 &

# Windows con pythonw (sin ventana de consola)
pythonw scripts/monitor_cli.py
```

---

## Casos de Uso

### Caso 1: Monitorear notificaciones de hoy

**Objetivo:** Solo verificar notificaciones del dia actual.

**Configuracion:**
```json
{
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "fecha_desde_entradas": "16/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

**Comando:**
```bash
python scripts/monitor_cli.py --verificar-ahora --verbose
```

### Caso 2: Verificar entradas de la semana

**Objetivo:** Revisar todas las entradas de la semana pasada.

**Configuracion:**
```json
{
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "fecha_desde_entradas": "09/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

### Caso 3: Monitor 24/7 con intervalos diferentes

**Objetivo:** Verificar mas frecuentemente en horario laboral.

**Configuracion:**
```json
{
  "modo": "automatico",
  "dias_laborales": ["lunes", "martes", "miercoles", "jueves", "viernes"],
  "hora_inicio": "08:00",
  "hora_fin": "18:00",
  "intervalos_laboral_entradas": 5,
  "intervalos_no_laboral_entradas": 60
}
```

**Comando (modo continuo):**
```bash
python scripts/monitor_cli.py
```

### Caso 4: Debugging de problemas

**Objetivo:** Ver que esta pasando cuando algo no funciona.

**Pasos:**

1. Habilitar logs detallados y ventana visible:
```bash
python scripts/monitor_cli.py --verificar-ahora --no-headless --verbose
```

2. Revisar cada paso del proceso:
   - Autenticacion
   - Navegacion
   - Extraccion de entradas
   - Deteccion de cambios

3. Si es necesario, eliminar datos guardados:
```bash
rm data/monitor/entradas_conocidas.json
rm data/monitor/estado.json
rm pjn/scraping/pjn_storage_state.json
```

4. Ejecutar nuevamente

### Caso 5: Integracion con cron (Linux)

**Objetivo:** Ejecutar verificacion cada hora mediante cron.

**Crontab:**
```bash
# Editar crontab
crontab -e

# Agregar linea (cada hora)
0 * * * * cd /ruta/al/proyecto && /ruta/al/.venv/bin/python scripts/monitor_cli.py --verificar-ahora >> /ruta/logs/monitor.log 2>&1

# O cada 15 minutos durante horario laboral (8am-6pm)
*/15 8-18 * * 1-5 cd /ruta/al/proyecto && /ruta/al/.venv/bin/python scripts/monitor_cli.py --verificar-ahora >> /ruta/logs/monitor.log 2>&1
```

### Caso 6: Integracion con Task Scheduler (Windows)

**Objetivo:** Ejecutar verificacion periodica en Windows.

**Pasos:**

1. Abrir Task Scheduler
2. Crear tarea basica
3. Trigger: Repetir cada X minutos
4. Action: Iniciar programa
   - Programa: `C:\ruta\al\.venv\Scripts\pythonw.exe`
   - Argumentos: `scripts\monitor_cli.py --verificar-ahora`
   - Directorio: `C:\ruta\al\proyecto`

---

## Scripts Personalizados

### Script 1: Verificar y enviar email

```python
#!/usr/bin/env python3
"""Monitor con notificacion por email."""

import asyncio
import smtplib
from email.mime.text import MIMEText
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

async def verificar_y_notificar_email():
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)

    # Verificar entradas
    nuevas = await monitor.verificar_entradas()

    if nuevas:
        # Preparar email
        asunto = f"PJN: {len(nuevas)} nuevas entradas"
        cuerpo = "Nuevas entradas detectadas:\n\n"
        for entrada in nuevas:
            cuerpo += f"- {entrada.numero}: {entrada.evento}\n"

        # Enviar email
        msg = MIMEText(cuerpo)
        msg["Subject"] = asunto
        msg["From"] = "monitor@example.com"
        msg["To"] = "destinatario@example.com"

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login("tu_email@gmail.com", "tu_password")
            server.send_message(msg)

        print(f"Email enviado: {len(nuevas)} nuevas entradas")
    else:
        print("Sin nuevas entradas")

if __name__ == "__main__":
    asyncio.run(verificar_y_notificar_email())
```

### Script 2: Exportar a Excel

```python
#!/usr/bin/env python3
"""Exportar entradas nuevas a Excel."""

import asyncio
import pandas as pd
from datetime import datetime
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

async def verificar_y_exportar():
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)

    # Verificar entradas
    nuevas = await monitor.verificar_entradas()

    if nuevas:
        # Convertir a DataFrame
        data = [entrada.to_dict() for entrada in nuevas]
        df = pd.DataFrame(data)

        # Exportar a Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"entradas_nuevas_{timestamp}.xlsx"
        df.to_excel(filename, index=False)

        print(f"Exportadas {len(nuevas)} entradas a {filename}")
    else:
        print("Sin nuevas entradas para exportar")

if __name__ == "__main__":
    asyncio.run(verificar_y_exportar())
```

### Script 3: Monitor con webhook

```python
#!/usr/bin/env python3
"""Monitor que envia notificaciones a webhook (Slack, Discord, etc)."""

import asyncio
import requests
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

async def verificar_y_webhook():
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)

    # Verificar entradas
    nuevas = await monitor.verificar_entradas()

    if nuevas:
        # Preparar payload para Slack
        mensaje = f"*PJN Monitor:* {len(nuevas)} nuevas entradas detectadas\n\n"
        for entrada in nuevas[:5]:  # Primeras 5
            mensaje += f"• {entrada.numero}: {entrada.evento}\n"

        if len(nuevas) > 5:
            mensaje += f"\n... y {len(nuevas) - 5} mas"

        payload = {
            "text": mensaje,
            "username": "PJN Monitor",
            "icon_emoji": ":bell:"
        }

        # Enviar a webhook
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        response = requests.post(webhook_url, json=payload)

        if response.status_code == 200:
            print(f"Webhook enviado: {len(nuevas)} nuevas entradas")
        else:
            print(f"Error al enviar webhook: {response.status_code}")
    else:
        print("Sin nuevas entradas")

if __name__ == "__main__":
    asyncio.run(verificar_y_webhook())
```

### Script 4: Monitor con logging a base de datos

```python
#!/usr/bin/env python3
"""Monitor que guarda entradas en SQLite."""

import asyncio
import sqlite3
from datetime import datetime
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

def crear_tabla():
    """Crea tabla si no existe."""
    conn = sqlite3.connect("monitor.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entradas_nuevas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            caratula TEXT,
            fecha TEXT,
            evento TEXT,
            tipo_evento TEXT,
            detectada_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

async def verificar_y_guardar_db():
    crear_tabla()

    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)

    # Verificar entradas
    nuevas = await monitor.verificar_entradas()

    if nuevas:
        conn = sqlite3.connect("monitor.db")
        cursor = conn.cursor()

        for entrada in nuevas:
            cursor.execute("""
                INSERT INTO entradas_nuevas
                (numero, caratula, fecha, evento, tipo_evento)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entrada.numero,
                entrada.caratula,
                entrada.fecha,
                entrada.evento,
                entrada.tipo_evento
            ))

        conn.commit()
        conn.close()

        print(f"Guardadas {len(nuevas)} entradas en base de datos")
    else:
        print("Sin nuevas entradas")

if __name__ == "__main__":
    asyncio.run(verificar_y_guardar_db())
```

---

## Integraciones

### Telegram Bot

```python
#!/usr/bin/env python3
"""Monitor con notificaciones via Telegram."""

import asyncio
import telegram
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

async def verificar_y_telegram():
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)

    # Configurar bot de Telegram
    bot_token = "TU_BOT_TOKEN"
    chat_id = "TU_CHAT_ID"
    bot = telegram.Bot(token=bot_token)

    # Verificar entradas
    nuevas = await monitor.verificar_entradas()

    if nuevas:
        mensaje = f"📨 *PJN Monitor*\n\n{len(nuevas)} nuevas entradas:\n\n"
        for entrada in nuevas[:10]:
            mensaje += f"• `{entrada.numero}`\n  {entrada.evento}\n\n"

        if len(nuevas) > 10:
            mensaje += f"... y {len(nuevas) - 10} mas"

        await bot.send_message(
            chat_id=chat_id,
            text=mensaje,
            parse_mode="Markdown"
        )

        print(f"Telegram enviado: {len(nuevas)} nuevas entradas")
    else:
        print("Sin nuevas entradas")

if __name__ == "__main__":
    asyncio.run(verificar_y_telegram())
```

### API REST (FastAPI)

```python
#!/usr/bin/env python3
"""API REST para el monitor."""

from fastapi import FastAPI, BackgroundTasks
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN

app = FastAPI(title="PJN Monitor API")

@app.get("/")
async def root():
    return {"status": "ok", "service": "PJN Monitor"}

@app.post("/verificar/entradas")
async def verificar_entradas(background_tasks: BackgroundTasks):
    """Inicia verificacion de entradas en background."""
    background_tasks.add_task(ejecutar_verificacion_entradas)
    return {"status": "iniciado", "message": "Verificacion en progreso"}

@app.get("/estado")
async def obtener_estado():
    """Obtiene estado actual del monitor."""
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)
    return {
        "estado": monitor.estado.to_dict(),
        "config": config.to_dict()
    }

async def ejecutar_verificacion_entradas():
    """Ejecuta verificacion de entradas."""
    config = MonitorConfig.from_file("config/monitor.json")
    monitor = MonitorPJN(config)
    nuevas = await monitor.verificar_entradas()
    print(f"Verificacion completada: {len(nuevas)} nuevas entradas")

# Ejecutar con:
# uvicorn script_nombre:app --host 0.0.0.0 --port 8000
```

---

## Tips y Mejores Practicas

### 1. Manejo de errores

Siempre configurar reintentos y notificaciones de error:

```json
{
  "max_reintentos_entradas": 3,
  "espera_reintentos_entradas": 30,
  "notificar_errores": true
}
```

### 2. Logs rotativos

Para evitar que los logs crezcan indefinidamente:

```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "monitor.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### 3. Monitoreo de salud

Crear script que verifique si el monitor esta corriendo:

```bash
#!/bin/bash
# check_monitor.sh

if pgrep -f "monitor_cli.py" > /dev/null; then
    echo "Monitor OK"
else
    echo "Monitor DOWN - reiniciando..."
    cd /ruta/al/proyecto
    python scripts/monitor_cli.py &
fi
```

Agregarlo a cron para ejecutar cada 5 minutos:
```
*/5 * * * * /ruta/al/check_monitor.sh
```

### 4. Respaldo periodico

Hacer respaldo del historial:

```bash
#!/bin/bash
# backup_monitor.sh

fecha=$(date +%Y%m%d)
mkdir -p backups
cp -r data/monitor backups/monitor_$fecha
echo "Respaldo creado: backups/monitor_$fecha"
```

---

## FAQ

**P: Como cambio el rango de fechas sin editar el JSON?**

R: Por ahora debes editar el JSON. En futuras versiones habra parametros CLI para esto.

**P: Puedo ejecutar multiples monitores simultaneamente?**

R: Si, pero debes usar directorios de datos diferentes:

```json
{
  "directorio_datos": "data/monitor_cuenta1"
}
```

**P: Como desactivo las notificaciones desktop?**

R: Configura en false:

```json
{
  "notificar_nuevas_entradas": false,
  "notificar_cambios_expedientes": false
}
```

**P: El monitor consume muchos recursos?**

R: En modo headless el consumo es minimo. Para reducir aun mas, aumenta los intervalos:

```json
{
  "intervalos_laboral_entradas": 30,
  "intervalos_no_laboral_entradas": 120
}
```
