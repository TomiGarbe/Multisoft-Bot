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
└── docker-compose.yml