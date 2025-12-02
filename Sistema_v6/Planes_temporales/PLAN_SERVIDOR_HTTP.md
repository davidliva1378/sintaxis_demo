# Plan de Implementación: Servidor MCP HTTP

**Versión:** 1.0.0
**Fecha:** 2025-10-27
**Objetivo:** Convertir el servidor MCP de stdio a HTTP/SSE para acceso por red

---

## 📋 Resumen Ejecutivo

Transformar el servidor MCP actual (que usa stdio y solo funciona localmente) en un servidor HTTP que permita acceso desde múltiples computadoras en la red local, y eventualmente desde internet.

### Estado Actual
- ✅ Servidor MCP funcional con stdio
- ✅ 17 herramientas implementadas
- ✅ 4 tipos de recursos
- ✅ 6 templates de prompts
- ❌ Solo accesible localmente (misma PC)

### Estado Objetivo
- ✅ Servidor HTTP/SSE
- ✅ Accesible desde red local (LAN)
- ✅ Autenticación con tokens
- ✅ Múltiples clientes simultáneos
- ✅ Compatible con Claude y ChatGPT

---

## 🎯 Fases de Implementación

### Fase 1: Servidor HTTP Básico (Red Local)
**Objetivo:** Servidor funcionando en red local
**Tiempo estimado:** 4-6 horas

#### Tareas:
1. **Crear servidor HTTP con SSE**
   - Archivo: `mcp_server/http_server.py`
   - Framework: `aiohttp` o `fastapi`
   - Implementar protocolo MCP sobre HTTP

2. **Endpoints MCP estándar**
   ```
   POST /mcp/initialize
   GET  /mcp/list_tools
   POST /mcp/call_tool
   GET  /mcp/list_resources
   POST /mcp/read_resource
   GET  /mcp/list_prompts
   POST /mcp/get_prompt
   GET  /health (healthcheck)
   ```

3. **Autenticación básica**
   - Sistema de tokens Bearer
   - Archivo: `mcp_server/auth.py`
   - Generar tokens únicos por cliente

4. **Configuración**
   - Agregar a `MCPConfig`:
     - `server_host` (default: "0.0.0.0")
     - `server_port` (default: 8000)
     - `auth_tokens` (lista de tokens válidos)
     - `enable_http_server` (bool)

5. **Script de inicio**
   - Archivo: `bin/start_http_server.py`
   - Opciones: --host, --port, --generate-token

---

### Fase 2: Seguridad y Producción
**Objetivo:** Servidor seguro para uso real
**Tiempo estimado:** 3-4 horas

#### Tareas:
1. **HTTPS/SSL**
   - Soporte para certificados SSL
   - Let's Encrypt para certificados gratuitos
   - Redirección HTTP → HTTPS

2. **Autenticación robusta**
   - Expiración de tokens
   - Rate limiting (límite de peticiones)
   - Blacklist de IPs

3. **CORS**
   - Configurar CORS para acceso web
   - Whitelist de dominios permitidos

4. **Logging y monitoreo**
   - Logs de acceso
   - Logs de errores
   - Métricas de uso

---

### Fase 3: Configuración de Red
**Objetivo:** Hacer el servidor accesible desde otras PCs
**Tiempo estimado:** 1-2 horas

#### Tareas Red Local:
1. **Configurar servidor**
   - Obtener IP local del servidor: `ifconfig` (Mac/Linux) o `ipconfig` (Windows)
   - Ejemplo: `192.168.1.100`

2. **Firewall**
   - Mac: System Preferences → Security → Firewall → Allow port 8000
   - Windows: Firewall → Allow app
   - Linux: `ufw allow 8000`

3. **Probar conectividad**
   - Desde otra PC: `curl http://192.168.1.100:8000/health`

#### Tareas Acceso Internet (Opcional):
1. **Port Forwarding en router**
   - Acceder al router (ej: 192.168.1.1)
   - Redirigir puerto externo 8000 → IP servidor:8000

2. **DNS Dinámico**
   - Registrar en servicio (No-IP, DuckDNS)
   - Obtener dominio: `mi-servidor.ddns.net`

3. **Alternativa: Cloudflare Tunnel**
   - Instalar `cloudflared`
   - Crear túnel: `cloudflared tunnel create sintaxis-mcp`
   - Obtener URL: `https://sintaxis-mcp.trycloudflare.com`

---

### Fase 4: Configuración de Clientes
**Objetivo:** Documentar cómo conectarse desde diferentes IAs
**Tiempo estimado:** 1 hora

#### Claude Code/Desktop:
```json
{
  "mcpServers": {
    "sintaxis-actuaciones": {
      "url": "http://192.168.1.100:8000",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer TOKEN_GENERADO"
      }
    }
  }
}
```

#### ChatGPT (GPT Actions):
```yaml
openapi: 3.0.0
info:
  title: SintaXis MCP Server
  version: 1.0.0
servers:
  - url: http://192.168.1.100:8000
paths:
  /mcp/list_tools:
    get:
      summary: List available tools
      security:
        - bearerAuth: []
  /mcp/call_tool:
    post:
      summary: Execute a tool
      security:
        - bearerAuth: []
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
```

---

## 🏗️ Arquitectura Técnica

### Componentes Nuevos

```
mcp_server/
├── server.py              # Servidor MCP original (stdio)
├── http_server.py         # 🆕 Servidor HTTP/SSE
├── auth.py                # 🆕 Sistema de autenticación
├── middleware.py          # 🆕 Middleware (CORS, logging)
├── config.py              # Actualizado con config HTTP
└── ...
```

### Flujo de Petición HTTP

```
Cliente (Claude/ChatGPT)
    ↓ HTTP POST /mcp/call_tool
Middleware de autenticación
    ↓ Verifica token
HTTP Server (FastAPI/aiohttp)
    ↓ Parse request
ActuacionesMCPServer
    ↓ call_tool()
DataLoader → workspace/
    ↓ Procesa datos
← Respuesta JSON
```

---

## 📦 Dependencias Nuevas

Agregar a `requirements.txt`:

```txt
# Servidor HTTP
fastapi==0.104.1           # Framework web moderno
uvicorn[standard]==0.24.0  # Servidor ASGI
python-multipart==0.0.6    # Para form data

# O alternativa con aiohttp
aiohttp==3.9.1             # Servidor HTTP async
aiohttp-sse==2.2.0         # Server-Sent Events

# Autenticación
pyjwt==2.8.0               # Para tokens JWT
python-jose==3.3.0         # Alternativa JWT
bcrypt==4.1.1              # Hashing de passwords

# HTTPS (opcional)
certbot==2.7.4             # Let's Encrypt
cryptography==41.0.7       # Certificados SSL
```

---

## 🔒 Consideraciones de Seguridad

### Nivel 1 - Red Local (Mínimo)
- ✅ Autenticación con token
- ✅ Firewall configurado
- ✅ Solo acceso desde red local

### Nivel 2 - Internet (Recomendado)
- ✅ Todo lo anterior
- ✅ HTTPS obligatorio
- ✅ Rate limiting
- ✅ Logs de acceso
- ✅ Tokens con expiración

### Nivel 3 - Producción (Ideal)
- ✅ Todo lo anterior
- ✅ Autenticación OAuth2
- ✅ IP Whitelist
- ✅ WAF (Web Application Firewall)
- ✅ Monitoreo 24/7
- ✅ Backups automáticos

---

## 🧪 Plan de Testing

### Tests Unitarios
```python
# tests/test_http_server.py
- test_health_endpoint()
- test_authentication()
- test_list_tools_endpoint()
- test_call_tool_endpoint()
- test_unauthorized_access()
```

### Tests de Integración
```python
# tests/test_integration_http.py
- test_full_workflow_http()
- test_multiple_clients()
- test_concurrent_requests()
```

### Tests de Red
```bash
# Desde otra PC en la red
curl -H "Authorization: Bearer TOKEN" \
     http://192.168.1.100:8000/mcp/list_tools

# Test de carga
ab -n 1000 -c 10 http://192.168.1.100:8000/health
```

---

## 📊 Métricas de Éxito

### Funcionales
- [ ] Servidor HTTP arranca sin errores
- [ ] Responde a peticiones desde red local
- [ ] Autenticación funciona correctamente
- [ ] Claude puede conectarse y usar tools
- [ ] ChatGPT puede conectarse y usar tools
- [ ] Múltiples clientes simultáneos (al menos 5)

### Performance
- [ ] Latencia < 100ms para peticiones simples
- [ ] Latencia < 2s para extracción de PDFs
- [ ] Soporta 10+ peticiones concurrentes
- [ ] Uso de memoria < 500MB con 10 clientes

### Seguridad
- [ ] No hay acceso sin token válido
- [ ] HTTPS funciona correctamente
- [ ] Logs registran todos los accesos
- [ ] Rate limiting previene abusos

---

## 📝 Documentación a Crear/Actualizar

1. **MCP_SERVIDOR.md** (actualizar)
   - Agregar sección de servidor HTTP
   - Instrucciones de configuración
   - Troubleshooting

2. **CONFIGURACION_RED.md** (nuevo)
   - Configuración de red local
   - Port forwarding
   - Firewall por OS
   - DNS dinámico

3. **CONFIGURACION_CLIENTES.md** (nuevo)
   - Claude Code/Desktop
   - ChatGPT
   - Otros clientes MCP

4. **SEGURIDAD.md** (nuevo)
   - Mejores prácticas
   - Generación de tokens
   - Renovación de tokens
   - Auditoría de accesos

---

## 🚀 Comandos Rápidos

### Iniciar servidor (desarrollo)
```bash
python bin/start_http_server.py --host 0.0.0.0 --port 8000
```

### Iniciar servidor (producción)
```bash
python bin/start_http_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --ssl-cert /path/to/cert.pem \
  --ssl-key /path/to/key.pem
```

### Generar token
```bash
python bin/start_http_server.py --generate-token
# Output: TOKEN_abc123xyz...
```

### Test rápido
```bash
# Health check
curl http://localhost:8000/health

# List tools
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/mcp/list_tools
```

---

## ❓ Decisiones Pendientes

### Framework Web
- [ ] **FastAPI** (más moderno, documentación automática)
- [ ] **aiohttp** (más ligero, control fino)

**Recomendación:** FastAPI (mejor DX, OpenAPI automático para ChatGPT)

### Protocolo MCP Transport
- [ ] **SSE (Server-Sent Events)** - Unidireccional, más simple
- [ ] **WebSocket** - Bidireccional, más complejo

**Recomendación:** SSE para empezar, WebSocket después si se necesita

### Almacenamiento de Tokens
- [ ] **Archivo JSON** - Simple, para desarrollo
- [ ] **Base de datos** - Mejor para producción
- [ ] **Variables de entorno** - Muy simple, menos flexible

**Recomendación:** Archivo JSON encriptado para empezar

---

## 🔄 Roadmap de Versiones

### v1.0.0 - Servidor HTTP Básico
- Servidor HTTP funcionando
- Autenticación con tokens
- Acceso desde red local

### v1.1.0 - Seguridad Mejorada
- HTTPS
- Rate limiting
- Logs completos

### v1.2.0 - Multi-tenant
- Múltiples workspaces
- Permisos por usuario
- Aislamiento de datos

### v2.0.0 - Producción
- Dashboard web de administración
- Métricas en tiempo real
- Backups automáticos
- Monitoreo y alertas

---

## 📞 Contacto y Soporte

**Dudas durante implementación:**
- Revisar este documento
- Consultar `docs/MCP_SERVIDOR.md`
- Revisar issues en GitHub

**Testing:**
- Siempre testear en red local primero
- Nunca exponer a internet sin HTTPS
- Hacer backup antes de cambios mayores

---

**Última actualización:** 2025-10-27
**Próxima revisión:** Después de completar Fase 1