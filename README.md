<div align="center">

# 🚀 Vocentra AI
### Enterprise AI Voice Calling Platform for Intelligent Outbound Campaigns

<p align="center">
  <b>Automate intelligent outbound voice campaigns using AI Agents powered by Vapi, Twilio, FastAPI, Next.js, and PostgreSQL.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-blueviolet?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi"/>
  <img src="https://img.shields.io/badge/Next.js-Frontend-black?style=for-the-badge&logo=nextdotjs"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql"/>
  <img src="https://img.shields.io/badge/Twilio-Voice-red?style=for-the-badge&logo=twilio"/>
  <img src="https://img.shields.io/badge/Vapi-AI%20Voice-orange?style=for-the-badge"/>
</p>

</div>

---

# 📌 Overview

Vocentra AI is an enterprise-grade AI Voice Calling Platform that enables organizations to automate outbound calling campaigns using AI-powered voice assistants.

The platform allows businesses to upload thousands of customer contacts, launch intelligent AI-driven voice campaigns, monitor calls in real time, analyze conversations, and manage campaigns through a modern SaaS dashboard.

Designed with scalability, security, and multi-tenancy in mind, Vocentra AI demonstrates modern full-stack engineering practices and production-ready architecture.

---

# ✨ Key Features

## 🤖 AI Voice Agents

- AI-powered outbound calling
- Human-like conversations
- Dynamic call flows
- Multi-assistant support
- Voice Agent orchestration using Vapi

---

## 📞 Bulk Calling Campaigns

- CSV / Excel Upload
- Automatic Lead Import
- Sequential AI Calling
- Campaign Scheduling
- Live Campaign Monitoring
- Retry Failed Calls

---

## 📊 Real-Time Dashboard

- Live Campaign Status
- Active Calls
- Campaign Analytics
- Voice Logs
- Performance Metrics
- Cost Tracking
- Call Duration Monitoring

---

## 🧠 AI Conversation Intelligence

- Call Transcript
- AI Summary
- Recording Playback
- Sentiment Analysis Ready
- Conversation Analytics

---

## 🔍 Lead Management

- Customer Database
- Campaign Leads
- Search & Filter
- Contact History
- Lead Status Tracking

---

## 🏢 Multi-Tenant SaaS

- Organization Isolation
- Role-Based Access Control (RBAC)
- Workspace Settings
- API Key Management
- Billing Ready Architecture

---

## ⚡ Enterprise Features

- Authentication & Authorization
- Async Processing
- Background Workers
- WebSockets
- Real-Time Updates
- Scalable Database Design

---

# 🏗️ System Architecture

```text
                    ┌────────────────────┐
                    │     Next.js UI     │
                    └─────────┬──────────┘
                              │
                     REST API / WebSockets
                              │
                    ┌─────────▼──────────┐
                    │      FastAPI       │
                    │   Business Logic   │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      PostgreSQL         Redis Queue       Background Workers
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                    Vapi AI Voice Platform
                            │
                            ▼
                      Twilio Telephony
                            │
                            ▼
                        Customer Calls
```

---

# 🛠️ Tech Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- ShadCN UI
- WebSockets

---

## Backend

- FastAPI
- Python
- SQLAlchemy Async
- Alembic
- ARQ Workers
- Redis

---

## Database

- PostgreSQL
- pgvector

---

## AI & Voice

- Vapi AI
- Twilio
- OpenAI Embeddings
- Retrieval-Augmented Generation (RAG)

---

## Authentication

- JWT Authentication
- Role-Based Access Control

---

## DevOps

- Docker
- Docker Compose
- Git
- GitHub

---

# 📂 Project Structure

```text
Vocentra-AI
│
├── backend/
├── frontend/
├── docs/
├── docker/
├── scripts/
├── migrations/
├── README.md
└── docker-compose.yml
```

---

# 🚀 Core Modules

- Authentication
- Organization Management
- Campaign Management
- Bulk Calling Engine
- AI Voice Agent Integration
- Live Dashboard
- Voice Logs
- Analytics
- Knowledge Base
- API Keys
- Billing
- User Management

---

# 📈 Platform Workflow

```text
Upload Contacts

↓

Create Campaign

↓

Queue Leads

↓

AI Voice Calls

↓

Conversation Analysis

↓

Call Logs

↓

Analytics Dashboard

↓

Campaign Insights
```

---

# 📸 Screenshots

> Screenshots and demo GIFs will be added soon.

---

# 🔮 Future Enhancements

- CRM Integrations
- WhatsApp Automation
- SMS Campaigns
- Predictive Dialing
- AI Voice Cloning
- Multi-Language Voice Agents
- Advanced Analytics
- Calendar Scheduling
- Workflow Automation
- Mobile Application

---

# 💼 Why This Project?

Vocentra AI was built to demonstrate production-grade software engineering practices by combining Artificial Intelligence, Voice Automation, Cloud Architecture, and Full Stack Development into a scalable enterprise SaaS platform.

This project showcases skills in:

- Backend Engineering
- AI Integration
- Distributed Systems
- Database Design
- Authentication
- API Development
- Real-Time Applications
- Cloud-Ready Architecture
- Modern Frontend Development

---

# 👨‍💻 About the Developer

**Harris Ruben**

AI Engineer | Machine Learning Engineer | Full Stack Developer

🎓 B.Tech Artificial Intelligence & Data Science

Passionate about building scalable AI products, intelligent automation platforms, and enterprise-grade software solutions.

---

# ⭐ Support

If you found this project interesting, consider giving it a ⭐ on GitHub.

It motivates further development and helps others discover the project.

---

<div align="center">

### ⭐ Thanks for visiting Vocentra AI ⭐

Building the future of AI-powered voice automation.

</div>
