# Guía de Acceso Remoto - Servidor MCP

Esta guía explica cómo configurar acceso remoto al servidor MCP de Sintaxis
para usar desde Claude Desktop, Claude Code u otros clientes MCP.

## Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de ngrok](#instalación-de-ngrok)
3. [Generar Token de Acceso](#generar-token-de-acceso)
4. [Iniciar Servidor con ngrok](#iniciar-servidor-con-ngrok)
5. [Configurar Claude Desktop](#configurar-claude-desktop)
6. [Configurar Claude Code CLI](#configurar-claude-code-cli)
7. [Alternativa: Cloudflare Tunnel](#alternativa-cloudflare-tunnel)
8. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

- Python 3.10+
- Dependencias MCP instaladas (`pip install mcp`)
- Cuenta ngrok (gratuita): https://ngrok.com
- MySQL corriendo con base de datos sintaxis

---

## Instalación de ngrok

### macOS (Homebrew)

```bash
brew install ngrok
```

### macOS/Linux (Manual)

```bash
# Descargar desde https://ngrok.com/download
unzip ngrok-v3-stable-darwin-amd64.zip
mv ngrok /usr/local/bin/
```

### Configurar Token

1. Crear cuenta en https://dashboard.ngrok.com
2. Copiar tu authtoken desde el dashboard
3. Configurar:

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

---

## Generar Token de Acceso

Antes de exponer el servidor, genera un token Bearer para autenticación:

### Opción 1: Desde el servidor SSE

```bash
cd /path/to/sintaXis/Sistema_v6

PYTHONPATH=$(pwd):$(dirname $(pwd)):$PYTHONPATH \
python -m sintaxis_mcp.sintaxis_mcp_server_sse --generate-token "claude-desktop"
```

Salida:
```
============================================================
✅ TOKEN GENERADO
============================================================
Nombre: claude-desktop
Token ID: a1b2c3d4

🔑 TOKEN: mcp_abcdefghijklmnop...

⚠️  Guarda este token de forma segura.
   No podrás verlo de nuevo.
============================================================
```

### Opción 2: Usando el CLI

```bash
cd /path/to/sintaXis/Sistema_v6

PYTHONPATH=$(pwd):$(dirname $(pwd)):$PYTHONPATH \
python sintaxis_mcp/bin/mcp_token_cli.py generate --name "claude-desktop"
```

### Listar tokens existentes

```bash
python sintaxis_mcp/bin/mcp_token_cli.py list
```

---

## Iniciar Servidor con ngrok

### Método 1: Script automático (Recomendado)

```bash
cd /path/to/sintaXis/Sistema_v6

# Sin autenticación (solo desarrollo local)
./scripts/start_mcp_with_ngrok.sh

# Con autenticación (recomendado)
./scripts/start_mcp_with_ngrok.sh --auth

# Con autenticación + rate limiting + HTTPS
./scripts/start_mcp_with_ngrok.sh --auth --rate-limit --ssl
```

El script mostrará:
- URL local: `http://localhost:8765/sse`
- URL pública: `https://abc123.ngrok-free.app/sse`
- Configuración para Claude Desktop

### Método 2: Manual

```bash
# Terminal 1: Servidor MCP
cd /path/to/sintaXis/Sistema_v6
PYTHONPATH=$(pwd):$(dirname $(pwd)):$PYTHONPATH \
MYSQL_PASSWORD=tu_password \
python -m sintaxis_mcp.sintaxis_mcp_server_sse --auth --rate-limit

# Terminal 2: ngrok
ngrok http 8765
```

---

## Configurar Claude Desktop

### Ubicación del archivo de configuración

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuración con autenticación (Recomendado)

```json
{
  "mcpServers": {
    "sintaxis-remoto": {
      "url": "https://abc123.ngrok-free.app/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer mcp_tu_token_aqui..."
      }
    }
  }
}
```

### Configuración sin autenticación (Solo desarrollo)

```json
{
  "mcpServers": {
    "sintaxis-remoto": {
      "url": "https://abc123.ngrok-free.app/sse",
      "transport": "sse"
    }
  }
}
```

### Configuración local (STDIO)

Para uso local sin red, usar STDIO:

```json
{
  "mcpServers": {
    "sintaxis-local": {
      "command": "python",
      "args": ["-m", "sintaxis_mcp.sintaxis_mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/sintaXis:/path/to/sintaXis/Sistema_v6",
        "MYSQL_PASSWORD": "tu_password"
      }
    }
  }
}
```

---

## Configurar Claude Code CLI

```bash
# Agregar servidor remoto
claude mcp add sintaxis-remoto \
  --transport sse \
  --url "https://abc123.ngrok-free.app/sse" \
  --header "Authorization: Bearer mcp_tu_token_aqui..."

# Verificar
claude mcp list

# Probar conexión
claude mcp test sintaxis-remoto
```

---

## Alternativa: Cloudflare Tunnel

Para URLs estables sin costo adicional:

### Instalación

```bash
brew install cloudflared
```

### Crear túnel

```bash
# Login
cloudflared tunnel login

# Crear túnel
cloudflared tunnel create sintaxis-mcp

# Configurar DNS (requiere dominio en Cloudflare)
cloudflared tunnel route dns sintaxis-mcp mcp.tu-dominio.com

# Iniciar
cloudflared tunnel run sintaxis-mcp
```

### Ventajas sobre ngrok

| Característica | ngrok Free | ngrok Pro | Cloudflare |
|----------------|------------|-----------|------------|
| URL estable | ❌ | ✅ | ✅ |
| HTTPS gratis | ✅ | ✅ | ✅ |
| Dominio propio | ❌ | ✅ | ✅ |
| Costo | Gratis | $8/mes | Gratis |

---

## Troubleshooting

### Error: "ngrok no está instalado"

```bash
brew install ngrok
ngrok config add-authtoken YOUR_TOKEN
```

### Error: "Authorization header required"

El servidor tiene autenticación habilitada. Asegúrate de incluir el header:

```json
"headers": {
  "Authorization": "Bearer mcp_tu_token..."
}
```

### Error: "Invalid or expired token"

1. Verifica que el token esté correcto (sin espacios extra)
2. Lista tokens activos: `python bin/mcp_token_cli.py list`
3. Genera uno nuevo si expiró

### Error: "Rate limit exceeded"

Espera 60 segundos o usa un token autenticado (tiene límite más alto).

### La URL de ngrok cambió

ngrok Free genera URLs nuevas en cada reinicio. Opciones:
1. Actualizar `claude_desktop_config.json` con la nueva URL
2. Usar ngrok Pro para URLs estables
3. Usar Cloudflare Tunnel

### Claude Desktop no conecta

1. Verificar que el servidor esté corriendo: `curl https://URL/health`
2. Verificar config JSON válido (sin comas trailing)
3. Reiniciar Claude Desktop después de cambiar config

### Ver logs del servidor

```bash
# Durante ejecución, logs van a stdout
# Para más detalle:
python -m sintaxis_mcp.sintaxis_mcp_server_sse --auth 2>&1 | tee mcp.log
```

---

## Seguridad

### Recomendaciones

1. **Siempre usar autenticación** (`--auth`) para acceso remoto
2. **Usar HTTPS** (`--ssl`) o ngrok (provee HTTPS automático)
3. **Habilitar rate limiting** (`--rate-limit`) para prevenir abuso
4. **Rotar tokens** periódicamente
5. **No compartir tokens** - cada cliente debe tener el suyo

### Niveles de seguridad

| Escenario | Flags recomendados |
|-----------|-------------------|
| Desarrollo local | Ninguno |
| Red local | `--auth` |
| Internet (demo) | `--auth --rate-limit` |
| Producción | `--auth --rate-limit --ssl` + Cloudflare |

---

## Comandos rápidos

```bash
# Generar token
python sintaxis_mcp_server_sse.py --generate-token "nombre"

# Iniciar con seguridad completa
./scripts/start_mcp_with_ngrok.sh --auth --rate-limit

# Ver tokens
python bin/mcp_token_cli.py list

# Estadísticas
python bin/mcp_token_cli.py stats

# Revocar token
python bin/mcp_token_cli.py revoke TOKEN_ID

# Health check
curl https://TU_URL_NGROK/health
```

---

**Última actualización:** 2024-12-01
