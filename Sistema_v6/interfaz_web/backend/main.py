from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from .db import obtener_expedientes
import json
import os
from datetime import datetime


app = FastAPI()
templates = Jinja2Templates(directory="backend/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    expedientes = obtener_expedientes()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "titulo": "Expedientes",
        "expedientes": expedientes
    })
# Ruta para el panel de administración
@app.get("/admin", response_class=HTMLResponse)
async def panel_admin(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "titulo": "Panel del Administrador"
    })


@app.get("/monitoreo", response_class=HTMLResponse)
async def vista_monitoreo(request: Request):
    ruta_json = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\Notificaciones\\expedientes.json"

    if not os.path.exists(ruta_json):
        return templates.TemplateResponse("monitoreo.html", {
            "request": request,
            "expedientes_por_fecha": {},
            "titulo": "Monitoreo"
        })

    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # Ordenar las fechas de más reciente a más antigua
    fechas_ordenadas = sorted(datos.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"), reverse=True)
    expedientes_por_fecha = {fecha: datos[fecha] for fecha in fechas_ordenadas}

    return templates.TemplateResponse("monitoreo.html", {
        "request": request,
        "expedientes_por_fecha": expedientes_por_fecha,
        "titulo": "Monitoreo"
    })

@app.post("/monitoreo/leido")
async def marcar_leido(fecha: str = Form(...), numero: str = Form(...)):
    ruta_json = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\Notificaciones\\expedientes.json"

    with open(ruta_json, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if fecha in datos:
        for expediente in datos[fecha]:
            if expediente["numero"] == numero:
                expediente["leido"] = True
                break

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

    return RedirectResponse(url="/monitoreo", status_code=303)