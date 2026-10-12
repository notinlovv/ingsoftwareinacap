# Sistema de Registro de Progreso de Líneas de Fondeo

Sistema para registrar y monitorear en tiempo real el avance de las líneas de fondeo, reemplazando las planillas manuales por captura digital en terreno, base de datos centralizada y un dashboard de gestión.

> Proyecto académico — Ingeniería de Software, INACAP (Ingeniería Informática / Analista Programador).
> Equipo: Lucas Barrera, Cristian Marin, Leonardo Mora, Francisco Gatica.
> Profesor: Manuel Reveco Cabello.

**Estado de la base de datos:** SQLite en esta fase (piloto). La migración a PostgreSQL está planificada; ver [sección 15](#15-migración-futura-a-postgresql).

---

## Tabla de contenidos

1. [Problema](#1-problema)
2. [Objetivos](#2-objetivos)
3. [Alcance y limitaciones](#3-alcance-y-limitaciones)
4. [Arquitectura](#4-arquitectura)
5. [Stack tecnológico](#5-stack-tecnológico)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Requisitos previos (Debian)](#7-requisitos-previos-debian)
8. [Puesta en marcha](#8-puesta-en-marcha)
9. [Modelo de datos](#9-modelo-de-datos)
10. [API REST](#10-api-rest)
11. [Funcionamiento offline y sincronización](#11-funcionamiento-offline-y-sincronización)
12. [Dashboard y reportes](#12-dashboard-y-reportes)
13. [Seguridad y trazabilidad](#13-seguridad-y-trazabilidad)
14. [Contenedor Linux y despliegue](#14-contenedor-linux-y-despliegue)
15. [Migración futura a PostgreSQL](#15-migración-futura-a-postgresql)
16. [Pruebas](#16-pruebas)
17. [Metodología y flujo de trabajo](#17-metodología-y-flujo-de-trabajo)
18. [Hoja de ruta](#18-hoja-de-ruta)

---

## 1. Problema

El proceso actual es manual y lento:

1. **Captura:** el supervisor anota los metros avanzados en una libreta o planilla impresa.
2. **Transferencia:** al final del día entrega la planilla física en la oficina.
3. **Digitación:** un administrativo ingresa los datos a un Excel maestro (mayor fuente de errores).
4. **Consolidación:** semanalmente se genera un reporte manual para gerencia.
5. **Decisión:** la gerencia decide con datos de hasta una semana de antigüedad.

**Deficiencias:** latencia de datos, errores de transcripción y falta de trazabilidad (no hay historial de cambios auditable).

**Causa raíz:** no existe una herramienta digital integrada que capture el dato en origen y lo procese automáticamente.

## 2. Objetivos

**General:** desarrollar e implementar un sistema automatizado para el registro y monitoreo en tiempo real del progreso de las líneas de fondeo, eliminando la dependencia de planillas manuales.

**Específicos:**

1. App móvil (Android/iOS) para registrar el avance en terreno con validaciones de datos.
2. Base de datos centralizada en la nube que consolide la información sin transcripción manual.
3. Dashboard web para gerencia: porcentaje de avance, cuellos de botella y proyecciones de término.
4. Reducir en un 90 % el tiempo de generación de reportes y eliminar los errores de digitación.

## 3. Alcance y limitaciones

**Alcances**

- App móvil de registro de avance (metros lineales, fechas, ubicación y estado de cada línea).
- Servidor en la nube y base de datos centralizada.
- Dashboard web con reportes en tiempo real (descarga PDF/Excel y alertas por desviaciones).
- Capacitación al personal.

**Limitaciones**

- **Conectividad:** en zonas sin señal los datos se sincronizan al volver la cobertura.
- **Adopción:** el éxito depende de que el personal adopte la herramienta.
- **Alcance geográfico:** implementación inicial como piloto en **una sola línea de fondeo**.
- **Presupuesto:** sin integración con sistemas ERP en esta fase.
- **Base de datos:** SQLite en el piloto (un único proceso escritor); se migrará a PostgreSQL al escalar.

## 4. Arquitectura

```
┌────────────────────────┐        HTTPS / JSON        ┌───────────────────────────────┐
│  App móvil (terreno)   │ ─────────────────────────▶ │  Contenedor Linux (Docker)    │
│  React Native + Expo   │ ◀───────────────────────── │  ┌─────────────────────────┐  │
│  SQLite local + outbox │      sincronización        │  │ API REST (FastAPI)      │  │
└────────────────────────┘                            │  │ Auth JWT, reglas        │  │
                                                      │  └───────────┬─────────────┘  │
┌────────────────────────┐        HTTPS / JSON        │              │ SQLAlchemy     │
│  Dashboard web (oficina)│ ◀──────────────────────── │  ┌───────────▼─────────────┐  │
│  React + Vite + Recharts│                           │  │ SQLite (archivo .db)    │  │
└────────────────────────┘                            │  │ + carpeta de adjuntos   │  │
                                                      │  └─────────────────────────┘  │
                                                      └───────────────────────────────┘
                                                        Volumen persistente: ./data
```

Principios de diseño:

- **Offline-first:** la app lee y escribe siempre en su base local; la red solo sirve para sincronizar.
- **UUID generado en el dispositivo:** permite crear registros sin conexión y evita duplicados.
- **Operaciones idempotentes:** reenviar un registro no lo duplica.
- **Historial auditable:** cada cambio queda registrado con autor y fecha.
- **Base de datos intercambiable:** el acceso pasa por SQLAlchemy y la URL de conexión se define por variable de entorno, de modo que cambiar a PostgreSQL no requiere reescribir la lógica.

## 5. Stack tecnológico

| Capa | Tecnología | Uso |
|---|---|---|
| App móvil | React Native + Expo (TypeScript) | Interfaz Android/iOS |
| Navegación | Expo Router | Pantallas de la app |
| Formularios | React Hook Form + Zod | Captura y validación |
| Datos locales (móvil) | expo-sqlite | Base local y cola de sincronización (outbox) |
| Red | TanStack Query + NetInfo | Peticiones y detección de conexión |
| Ubicación | expo-location | Coordenadas GPS (funciona sin internet) |
| Sesión | expo-secure-store | Almacenamiento seguro de tokens |
| Backend | Python 3.11+ con FastAPI | API REST |
| Validación | Pydantic | Esquemas de entrada/salida |
| ORM / migraciones | SQLAlchemy + Alembic | Acceso a datos y versionado del esquema |
| Base de datos (servidor) | **SQLite** (fase actual) → PostgreSQL (futuro) | Almacenamiento centralizado |
| Autenticación | JWT (python-jose) + bcrypt (passlib) | Login y roles |
| Dashboard | React + Vite + Recharts | Tableros y gráficos |
| Reportes | openpyxl, reportlab | Exportación Excel y PDF |
| Pruebas | pytest, Jest | Calidad |
| Contenedor | Docker (imagen basada en Debian slim) | Empaquetado y despliegue del backend |
| Proxy / HTTPS | Caddy | Certificados automáticos |
| Compilación móvil | EAS Build (Expo) | Builds Android/iOS sin Mac |
| Control de versiones | Git + GitHub | Colaboración |
| Editor | Visual Studio Code | Desarrollo |

## 6. Estructura del repositorio

```
.
├── README.md
├── docker-compose.yml
├── Caddyfile
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py            # Instancia FastAPI
│   │   ├── config.py          # Variables de entorno
│   │   ├── database.py        # Conexión y sesión (SQLite hoy, PostgreSQL mañana)
│   │   ├── models.py          # Tablas SQLAlchemy
│   │   ├── schemas.py         # Modelos Pydantic
│   │   ├── auth.py            # Login, JWT, roles
│   │   ├── routers/
│   │   │   ├── registros.py   # Avance de líneas
│   │   │   ├── lineas.py      # Líneas de fondeo
│   │   │   ├── reportes.py    # PDF / Excel
│   │   │   └── dashboard.py   # Métricas agregadas
│   │   └── services/          # Cálculos (avance, proyección, alertas)
│   ├── alembic/               # Migraciones
│   ├── tests/
│   └── requirements.txt
├── mobile/
│   ├── app/                   # Pantallas (Expo Router)
│   ├── src/
│   │   ├── db/                # SQLite local y outbox
│   │   ├── sync/              # Lógica de sincronización
│   │   ├── schemas/           # Esquemas Zod
│   │   └── components/
│   ├── app.json
│   └── package.json
├── dashboard/
│   ├── src/
│   └── package.json
├── data/                      # (no versionado) fondeo.db, adjuntos, respaldos
└── docs/
    ├── requisitos.md
    ├── casos-de-uso.md
    ├── diagrama-er.md
    └── arquitectura.md
```

## 7. Requisitos previos (Debian)

> Desarrollo en Debian: **no se puede ejecutar el simulador de iOS en Linux**. En iOS se prueba con Expo Go en un iPhone físico y los builds se generan con EAS Build en la nube.

```bash
# Utilidades base
sudo apt update
sudo apt install -y git curl build-essential openjdk-17-jdk watchman \
  python3 python3-venv python3-pip sqlite3 qemu-kvm

# Node.js con nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install --lts
```

- **Docker:** instalar Docker Engine y el plugin Compose siguiendo la guía oficial para Debian, y agregar el usuario al grupo `docker` (`sudo adduser $USER docker`, luego reiniciar sesión).
- **Android Studio:** instalarlo para obtener el SDK y el emulador. Definir en `~/.bashrc`:
  ```bash
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools
  ```
- **KVM:** agregar el usuario al grupo `kvm` (`sudo adduser $USER kvm`) y reiniciar sesión.
- **VS Code, extensiones recomendadas:** ESLint, Prettier, Python, Pylance, Docker, Expo Tools, React Native Tools, SQLite Viewer.

## 8. Puesta en marcha

### 8.1 Variables de entorno

```bash
cp .env.example .env
```

Variables principales:

```
# Fase actual: SQLite (la ruta es la del contenedor; ./data se monta como volumen)
DATABASE_URL=sqlite:////app/data/fondeo.db

# Fase futura (PostgreSQL): solo se cambia esta línea
# DATABASE_URL=postgresql+psycopg://fondeo:clave@db:5432/fondeo

SECRET_KEY=generar-una-clave-larga-y-aleatoria
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=14
UPLOAD_DIR=/app/data/archivos
```

> Generar la clave con: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`

### 8.2 Backend con Docker (recomendado)

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head
```

Documentación interactiva de la API: <http://localhost:8000/docs>

### 8.3 Backend sin Docker (desarrollo rápido)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./data/fondeo.db
alembic upgrade head
uvicorn app.main:app --reload
```

### 8.4 App móvil

```bash
cd mobile
npm install
npx expo start
```

- Android: presionar `a` (emulador) o conectar el teléfono por USB con depuración activada.
- iOS: escanear el QR con la app **Expo Go** en un iPhone.
- Configurar la URL de la API en `mobile/.env` (`EXPO_PUBLIC_API_URL`). Usar la IP de la máquina en la red local, no `localhost`.

### 8.5 Dashboard web

```bash
cd dashboard
npm install
npm run dev
```

Disponible en <http://localhost:5173>.

## 9. Modelo de datos

| Tabla | Campos principales |
|---|---|
| `usuarios` | id, nombre, email, hash_password, rol (`supervisor`, `gerente`, `admin`), activo |
| `lineas_fondeo` | id, nombre, metros_totales, fecha_inicio, fecha_meta, estado |
| `registros_avance` | id (UUID del dispositivo), linea_id, usuario_id, metros_avanzados, fecha, latitud, longitud, estado, observacion, creado_en, sincronizado_en, version_esquema |
| `archivos` | id, registro_id, ruta, tipo, tamaño |
| `auditoria` | id, entidad, entidad_id, usuario_id, accion, valores_antes, valores_despues, fecha |

Validaciones de negocio:

- `metros_avanzados` ≥ 0 y la suma acumulada no puede superar `metros_totales`.
- La fecha del registro no puede ser futura.
- Los registros no pueden retroceder el avance acumulado sin quedar auditados.

Notas de compatibilidad SQLite ↔ PostgreSQL:

- Los UUID se guardan como texto (`String(36)`) para que funcionen igual en ambos motores.
- Los campos `valores_antes` / `valores_despues` usan el tipo `JSON` de SQLAlchemy (SQLite lo guarda como texto, PostgreSQL como JSON nativo).
- Las fechas se guardan en UTC.
- No usar funciones SQL específicas de un motor; las consultas se escriben con SQLAlchemy.

## 10. API REST

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/login` | Devuelve access y refresh token |
| POST | `/auth/refresh` | Renueva el access token |
| GET | `/lineas` | Lista de líneas de fondeo |
| PUT | `/registros/{uuid}` | Crea o actualiza un registro (idempotente) |
| GET | `/registros?desde=<timestamp>` | Registros modificados desde una fecha |
| POST | `/registros/{uuid}/archivos` | Sube un adjunto |
| GET | `/dashboard/resumen?linea_id=` | Avance, proyección y alertas |
| GET | `/reportes/avance.xlsx` | Reporte en Excel |
| GET | `/reportes/avance.pdf` | Reporte en PDF |

Códigos relevantes: `401` no autenticado, `403` sin permiso, `409` conflicto de versión (incluye la versión del servidor), `422` validación fallida.

## 11. Funcionamiento offline y sincronización

1. La app guarda cada registro en **SQLite local** con `estado_sync = pendiente`.
2. Cada operación se agrega a la tabla **`outbox`** (cola de envío).
3. Con **NetInfo** la app detecta cuándo hay conexión y procesa la cola en orden, con reintentos.
4. El servidor responde al `PUT /registros/{uuid}`; si se aplica, la app marca el registro como `sincronizado`.
5. Los adjuntos se suben después de que el registro ya existe en el servidor.
6. Si el servidor responde `409`, el registro pasa a `conflicto` y se muestra al usuario.
7. La app descarga los cambios del servidor con `GET /registros?desde=<último_sync>`.

La interfaz muestra un indicador por registro (pendiente / sincronizado / conflicto) y un banner de "sin conexión".

## 12. Dashboard y reportes

Indicadores:

- **% de avance** = metros acumulados / metros totales.
- **Proyección de término** = metros restantes / promedio diario de avance de los últimos 7 días.
- **Cuellos de botella:** días o tramos con avance por debajo del promedio.
- **Alertas por desviación:** una tarea periódica compara el avance real con el plan y marca las líneas atrasadas.

Reportes descargables en **PDF** y **Excel**, generados desde el servidor.

## 13. Seguridad y trazabilidad

- HTTPS obligatorio en producción (Caddy + Let's Encrypt).
- Contraseñas con bcrypt; tokens de vida corta y refresh token.
- Tokens en el dispositivo guardados con `expo-secure-store`.
- Control de acceso por rol (supervisor registra; gerente consulta; admin gestiona).
- Tabla `auditoria` con autor, fecha y valores antes/después de cada cambio.
- Validación y límite de tamaño/tipo en archivos adjuntos.
- Secretos solo en `.env`; el archivo **no se versiona** (incluirlo en `.gitignore`, junto con `data/`).
- **Respaldos:** copiar `data/fondeo.db` de forma segura (ver 14.4).

## 14. Contenedor Linux y despliegue

El backend se empaqueta en un contenedor Linux (imagen Debian slim). SQLite vive en un volumen (`./data`) para que los datos sobrevivan a reinicios y actualizaciones de la imagen.

### 14.1 `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# IMPORTANTE: un solo worker mientras se use SQLite (un único escritor)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### 14.2 `docker-compose.yml`

```yaml
services:
  api:
    build: ./backend
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"

  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./dashboard/dist:/srv
      - caddy_data:/data
    depends_on:
      - api
    restart: unless-stopped

volumes:
  caddy_data:
```

### 14.3 `Caddyfile`

```
fondeo.tudominio.cl {
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy api:8000
    }
    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
```

> Para pruebas locales, reemplazar el dominio por `:80`.

### 14.4 Operación del día a día

```bash
# Actualizar a una nueva versión
git pull
docker compose up --build -d
docker compose exec api alembic upgrade head

# Ver logs
docker compose logs -f api

# Respaldo consistente de SQLite (con el contenedor en marcha)
docker compose exec api python -c "import sqlite3; \
src=sqlite3.connect('/app/data/fondeo.db'); \
dst=sqlite3.connect('/app/data/respaldo.db'); src.backup(dst)"
```

Programar el respaldo diario con `cron` en el servidor y copiar `data/` fuera de la máquina.

### 14.5 Ajustes recomendados para SQLite

- Activar el modo **WAL** y las claves foráneas al abrir la conexión (en `database.py`): `PRAGMA journal_mode=WAL;` y `PRAGMA foreign_keys=ON;`.
- Mantener **un solo worker** de Uvicorn.
- En Alembic, usar `render_as_batch=True` para que las migraciones que alteran tablas funcionen en SQLite.

### 14.6 Distribución de la app móvil

- **Builds:** `eas build --platform android` / `--platform ios`.
- **Pruebas internas:** Google Play Internal Testing y TestFlight.
- Para uso solo interno, evaluar distribución privada en lugar de la tienda pública.

## 15. Migración futura a PostgreSQL

SQLite es suficiente para el piloto (una línea, pocos usuarios). Conviene migrar cuando ocurra alguno de estos casos:

- Varios supervisores sincronizando al mismo tiempo de forma frecuente.
- Necesidad de más de un worker/instancia de la API.
- Escalado a toda la operación.
- Requisitos de alta disponibilidad o respaldos continuos.

**Pasos de migración**

1. Agregar el servicio de base de datos al `docker-compose.yml`:
   ```yaml
   db:
     image: postgres:16
     environment:
       POSTGRES_USER: fondeo
       POSTGRES_PASSWORD: ${DB_PASSWORD}
       POSTGRES_DB: fondeo
     volumes:
       - pgdata:/var/lib/postgresql/data
     restart: unless-stopped
   ```
   y agregar `pgdata:` a `volumes`.
2. Agregar `psycopg[binary]` a `requirements.txt`.
3. Cambiar `DATABASE_URL` en `.env` a `postgresql+psycopg://fondeo:<clave>@db:5432/fondeo`.
4. Crear el esquema: `docker compose exec api alembic upgrade head`.
5. Copiar los datos existentes desde `fondeo.db` (script de migración con SQLAlchemy o `pgloader`) y validar conteos de filas por tabla.
6. Subir los workers de Uvicorn y quitar la restricción de un solo escritor.
7. Quitar los `PRAGMA` de SQLite y `render_as_batch` si ya no se usa SQLite.

Como el acceso a datos pasa por SQLAlchemy, la lógica de negocio y los endpoints no cambian.

## 16. Pruebas

```bash
# Backend
cd backend && pytest

# App móvil
cd mobile && npm test

# Dashboard
cd dashboard && npm test
```

Pruebas clave a documentar:

- Validaciones de metros y fechas.
- Idempotencia del `PUT /registros/{uuid}`.
- **Prueba en modo avión:** registrar avances sin red, reconectar y verificar que se sincronizan sin duplicados.
- Permisos por rol.
- Persistencia: reiniciar el contenedor y comprobar que los datos siguen en `data/fondeo.db`.

## 17. Metodología y flujo de trabajo

- **Scrum** con sprints cortos (1–2 semanas) y tablero de tareas.
- **Ramas:** `main` (estable), `develop` (integración) y `feature/<nombre>`.
- **Commits:** mensajes claros en formato convencional (`feat:`, `fix:`, `docs:`).
- **Pull requests** con al menos una revisión de otro integrante.
- Linters y formateo: ESLint + Prettier (JS/TS), Ruff + Black (Python).

## 18. Hoja de ruta

- [ ] Documentación: requisitos, casos de uso, diagrama ER y de arquitectura.
- [ ] Backend en contenedor: autenticación, líneas y registros (`PUT`/`GET`) sobre SQLite.
- [ ] App: formulario con validaciones y guardado local.
- [ ] App: outbox y sincronización.
- [ ] App: GPS y adjuntos.
- [ ] Dashboard: avance, proyección y gráficos.
- [ ] Reportes PDF/Excel y alertas.
- [ ] Pruebas en terreno con el piloto (una línea de fondeo).
- [ ] Capacitación y entrega.
- [ ] Migración a PostgreSQL.
- [ ] Fase futura: integración con ERP y escalado a toda la operación.

---

## Licencia

Proyecto académico. Definir la licencia antes de publicar el repositorio.
