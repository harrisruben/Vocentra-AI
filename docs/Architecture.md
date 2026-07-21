# Vocentra AI - System Architecture

This document describes the high-level system layout, sequence diagrams, and database Entity Relationship Diagram (ERD) mapping.

---

## 1. Sequence Diagram: Inbound Voice Flow

This sequence diagrams details the step-by-step transaction flow from a customer phone call to dynamic tool routing, n8n workflow integrations, and live dashboard telemetry reporting:

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Twilio as Twilio Gateway
    participant Vapi as Vapi Orchestrator
    participant Router as Vocentra Router
    participant DB as SQLite / PostgreSQL
    participant n8n as n8n Workflow Engine
    participant Dash as Next.js Dashboard

    Customer->>Twilio: Call Vocentra Phone Number
    Twilio->>Vapi: Redirect SIP stream to Assistant Webhook
    Vapi->>Router: Forward Caller speech intent (POST /api/webhooks/vapi)
    
    activate Router
    Router->>Router: Rewrites query & queries pgvector chunks (RAG)
    Router->>DB: Check Calendar / CRM parameters
    Router->>Vapi: Return text dialogue & action instructions
    deactivate Router
    
    Vapi->>Customer: Speak reply to caller
    
    Note over Customer, Vapi: Conversation finishes
    
    Vapi->>Router: Report Call logs & Transcript summary (POST /api/webhooks/vapi)
    Router->>DB: Log Call, Messages & Lead Scores
    Router->>n8n: Dispatch Workflow Trigger Webhook
    n8n->>n8n: Syncs HubSpot Lead, Sends Resend Email
    n8n-->>Router: Update workflow execution status
    Router->>Dash: Broadcast telemetry (via polling/Active Calls)
```

---

## 2. Database ERD Mapping

Vocentra AI uses a strict multi-tenant schema model partitioned by `organization_id`. The entity relationship details are mapped below:

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : "has team"
    ORGANIZATION ||--o{ CUSTOMER : "manages"
    ORGANIZATION ||--o{ CALL : "records"
    ORGANIZATION ||--o{ LEAD : "tracks"
    ORGANIZATION ||--o{ APPOINTMENT : "schedules"
    ORGANIZATION ||--o{ KNOWLEDGE : "stores context"
    ORGANIZATION ||--o{ WORKFLOW_CONFIG : "registers webhooks"
    ORGANIZATION ||--o{ API_KEY : "issues secrets"
    ORGANIZATION ||--o{ AUDIT_LOG : "records safety"

    ORGANIZATION {
        int id PK
        string name
        string billing_tier "free | growth | enterprise"
        int usage_limit
        int usage_count
        string twilio_sid
        string twilio_token
        string vapi_assistant_id
        string n8n_webhook_url
        json working_hours
        datetime created_at
    }

    USER {
        int id PK
        string email UK
        string name
        string hashed_password
        string role "admin | manager | member"
        int organization_id FK
        string invite_token
        datetime invite_expires
        boolean is_active
        datetime created_at
    }

    CUSTOMER {
        int id PK
        string name
        string phone
        string email
        int organization_id FK
        datetime created_at
    }

    CALL {
        int id PK
        string vapi_call_id UK
        string twilio_call_id
        int organization_id FK
        int customer_id FK
        string status "ongoing | completed | failed"
        int duration
        text summary
        string sentiment "positive | neutral | negative"
        int lead_score
        string recording_url
        float cost
        datetime created_at
    }

    WORKFLOW_CONFIG {
        int id PK
        int organization_id FK
        string name
        string webhook_url
        boolean enabled
        int retries
        datetime last_executed_at
        string last_status "success | failed"
        datetime created_at
    }

    API_KEY {
        int id PK
        int organization_id FK
        string name
        string key_prefix
        string hashed_key UK
        datetime created_at
        datetime expires_at
        boolean is_active
    }
```
