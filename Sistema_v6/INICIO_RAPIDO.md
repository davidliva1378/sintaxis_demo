# Guía de Inicio Rápido - Sistema PJN v6

**5 minutos para empezar a usar el sistema**

---

## 🚀 Instalación Rápida con Docker

### Requisitos
- Docker y Docker Compose instalados
- 5 GB de espacio libre

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/sistema-pjn-v6.git
cd sistema-pjn-v6/Sistema_v6

# 2. Configurar variables de entorno
cat > .env << 'EOF'
JWT_SECRET_KEY=tu-clave-secreta-jwt-cambiar-en-produccion
ENCRYPTION_FERNET_KEY=gZxdkgEN2wyl4L3A77Xkrwjzk_uRq6Orz8txZmbdXG4=
EOF

# 3. Iniciar sistema
docker-compose up -d --build

# 4. Esperar ~2 minutos y verificar
docker-compose ps
```

### Acceder

- **Frontend**: http://localhost
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

---

## 👤 Primera Configuración

### 1. Crear Cuenta

1. Abre http://localhost
2. Haz clic en **"Crear cuenta"**
3. Completa:
   ```
   Nombre:     Tu Nombre
   Email:      tu@email.com
   Contraseña: MiPassword123
   ```
4. Haz clic en **"Registrarse"**

### 2. Configurar Credenciales del PJN

1. Ve a **Configuración** (⚙️) → **Credenciales PJN**
2. Ingresa tus credenciales de scw.pjn.gov.ar:
   ```
   Usuario PJN:    tu_usuario_pjn
   Contraseña PJN: tu_password_pjn
   ```
3. Haz clic en **"Guardar Credenciales"**
4. Prueba la conexión: **"Probar Conexión"**

---

## 📋 Primera Extracción

### Extraer Expedientes

1. Ve a **Expedientes** en el menú lateral
2. Haz clic en **"Extraer Expedientes"**
3. Espera 1-5 minutos (depende de cantidad)
4. ¡Listo! Verás tu lista de expedientes

### Ver Detalles

1. Haz clic en **"Ver Detalles"** de cualquier expediente
2. Revisa información completa
3. Haz clic en **"Extraer Actuaciones"** para obtener todas las actuaciones

---

## 📁 Organizar con Workspaces

### Crear un Workspace

1. Ve a **Workspaces**
2. Haz clic en **"+ Nuevo Workspace"**
3. Completa:
   ```
   Nombre:      Casos Urgentes
   Descripción: Expedientes prioritarios
   Color:       Rojo
   Icono:       📂
   ```
4. Haz clic en **"Crear Workspace"**

### Agregar Expedientes

1. En lista de expedientes, menú (⋮) → **"Agregar a Workspace"**
2. Selecciona "Casos Urgentes"
3. Haz clic en **"Agregar"**

---

## 🔔 Configurar Monitoreo

### Crear Monitor

1. Ve a **Monitoreo**
2. Haz clic en **"+ Nuevo Monitor"**
3. Configura:
   ```
   Expediente:  CNM 1234/2024
   Frecuencia:  Cada 1 hora
   Horario:     08:00 - 20:00
   Días:        Lunes a Viernes
   ```
4. Marca opciones de notificación:
   ```
   [x] Notificar nueva actuación
   [x] Notificar cambio de situación
   ```
5. Haz clic en **"Crear Monitor"**

### Ver Cambios

1. Ve a **Monitoreo** → **Historial**
2. Revisa todos los cambios detectados
3. Haz clic en **"Ver detalles"** para más información

---

## ⚙️ Personalizar

### Cambiar Tema

1. Ve a **Configuración** → **Preferencias**
2. En "Tema", selecciona:
   - **Claro**: Fondo blanco
   - **Oscuro**: Fondo negro (recomendado para uso nocturno)
   - **Sistema**: Sigue configuración del SO

### Configurar Notificaciones

1. En **Preferencias**:
   ```
   [x] Notificaciones de escritorio
   [ ] Sonido en notificaciones
   ```

---

## 📖 Comandos CLI Útiles

### Ver Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs solo del backend
docker-compose logs -f backend

# Ver logs solo del frontend
docker-compose logs -f frontend
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo backend
docker-compose restart backend

# Reiniciar solo frontend
docker-compose restart frontend
```

### Detener Sistema

```bash
# Detener servicios
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener y eliminar todo (incluyendo volúmenes)
docker-compose down -v
```

---

## 🆘 Problemas Comunes

### Puerto 80 ocupado

```bash
# Cambiar puerto en docker-compose.yml:
ports:
  - "8080:80"  # Usar puerto 8080

# Acceder en: http://localhost:8080
```

### No puedo iniciar sesión

1. Verifica email y contraseña (case-sensitive)
2. Si olvidaste contraseña, registra nuevo usuario
3. O resetea base de datos:
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   ```

### Error al conectar con PJN

1. Verifica credenciales en Configuración → Credenciales PJN
2. Haz clic en **"Probar Conexión"**
3. Verifica conexión a internet: `ping scw.pjn.gov.ar`
4. Verifica que el PJN esté disponible en tu navegador

### Extracción muy lenta

- Usa "max_paginas" en CLI para extracciones parciales
- Verifica recursos del sistema: `docker stats`
- Reinicia el backend: `docker-compose restart backend`

---

## 📚 Documentación Completa

- **Manual de Usuario Completo**: [MANUAL_USUARIO.md](MANUAL_USUARIO.md)
- **Guía de Docker**: [DOCKER.md](DOCKER.md)
- **README General**: [README.md](README.md)
- **API Docs**: http://localhost:8000/docs

---

## 🔗 Enlaces Útiles

- **Portal Judicial Nacional**: https://scw.pjn.gov.ar/
- **GitHub**: https://github.com/tu-usuario/sistema-pjn-v6
- **Issues**: https://github.com/tu-usuario/sistema-pjn-v6/issues

---

## 💡 Tips Rápidos

### ✅ Mejores Prácticas

1. **Cambia las claves** del `.env` en producción
2. **Usa HTTPS** en servidores públicos
3. **Haz backups** de `data/sistema.db` regularmente
4. **Monitorea con frecuencia razonable** (no cada 5 min)
5. **Organiza con workspaces** desde el principio

### 🚀 Flujo de Trabajo Diario

```
1. Abrir aplicación
2. Revisar notificaciones en Dashboard
3. Ir a Monitoreo → Historial
4. Ver cambios de las últimas 24h
5. Extraer actuaciones de expedientes con cambios
6. Trabajar en workspaces organizados
```

### ⚡ Atajos

- **CLI**: Usa comandos para automatización
- **API**: Integra con tus sistemas
- **Workspaces**: Organiza por cliente/tipo
- **Monitores**: Configura y olvídate

---

## 🎯 Próximos Pasos

Ahora que tienes el sistema funcionando:

1. ✅ **Extrae todos tus expedientes**
2. ✅ **Crea workspaces para organizarlos**
3. ✅ **Configura monitores para los importantes**
4. ✅ **Personaliza preferencias**
5. ✅ **Integra con tu workflow diario**

---

## 🆘 Necesitas Ayuda?

- Lee el [**Manual Completo**](MANUAL_USUARIO.md) (93 páginas con TODO)
- Revisa [**Troubleshooting**](MANUAL_USUARIO.md#resolución-de-problemas)
- Consulta [**FAQ**](MANUAL_USUARIO.md#preguntas-frecuentes-faq)
- Abre un [**Issue en GitHub**](https://github.com/tu-usuario/sistema-pjn-v6/issues)

---

**¡Listo para usar Sistema PJN v6!** 🎉

**Versión**: 6.0.0
**Última actualización**: 2025-11-05
