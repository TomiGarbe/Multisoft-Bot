# Multisoft Bot

Plataforma empresarial de bots conversacionales multiempresa desarrollada para Multisoft.

El objetivo del proyecto es ofrecer una base sólida, escalable y mantenible para automatizar conversaciones por distintos canales (WhatsApp, WebChat y futuros canales), integrando IA y futuros módulos conectados al ERP mediante API.

---

# Características principales

- Multiempresa / multi-tenant
- Panel administrativo web
- Bots configurables por negocio
- Configuración global + configuración por canal
- Roles y permisos personalizados
- Conversaciones e historial de mensajes
- Adjuntos almacenados en PostgreSQL
- Arquitectura desacoplada por providers
- Integración futura con ERP vía API
- Preparado para escalar nuevos canales

---

# Stack tecnológico

## Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL

## Frontend

- React
- Next.js
- TypeScript
- TailwindCSS

## Infraestructura

- Docker
- Docker Compose

---

# Estructura del proyecto

```text
multisoft-bot/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── interfaces/
│   │   ├── modules/
│   │   ├── providers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   └── Dockerfile
│
├── docs/
├── docker/
├── .env.example          # Plantilla de variables para docker-compose
└── docker-compose.yml
```

---

# Variables de entorno

La configuración está centralizada en **un único archivo por contexto**:

| Archivo                | Cuándo se usa                                        | Versionado |
|------------------------|------------------------------------------------------|------------|
| `.env` (raíz)          | `docker compose up` — fuente de verdad para todos los containers | No (gitignored) |
| `.env.example` (raíz)  | Plantilla del `.env` raíz                            | Sí         |
| `backend/.env`         | Backend corriendo **fuera** de Docker (`uvicorn` local) | No        |
| `backend/.env.example` | Plantilla del `backend/.env`                         | Sí         |
| `frontend/.env`        | Frontend corriendo **fuera** de Docker (`npm run dev` local) | No   |

## Reglas

- **Docker Compose**: `docker-compose.yml` resuelve `${VAR}` desde el `.env` de la raíz y las pasa al backend vía `environment:`. No hay `env_file` ni `.env.docker`.
- **Hostname de la base**: dentro de la red de Docker, el host es el nombre del servicio (`postgres`). Nunca usar `localhost` ni `127.0.0.1` desde un container.
- **`NEXT_PUBLIC_API_URL`**: estas variables se hornean en el bundle del navegador. Como el navegador corre en el host, debe apuntar al puerto publicado (`http://localhost:8000/api/v1`), no al nombre del servicio.

## Setup rápido (Docker)

```bash
cp .env.example .env       # editar valores (DB_PASSWORD, SECRET_KEY, etc.)
docker compose up --build
```

> ⚠️ Si ya tenías un volumen `postgres_data` con credenciales previas, debés
> recrearlo para que tome las nuevas: `docker compose down -v` (esto **borra**
> los datos de la base local).

## Setup rápido (desarrollo local sin Docker)

```bash
# Backend
cp backend/.env.example backend/.env   # editar (DB_HOST=localhost)
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && cp .env.local.example .env && npm run dev
```