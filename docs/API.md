# Vocentra AI - API Specification Reference

All API requests return a standard JSON envelope structure:

```json
{
  "success": true,
  "message": "Response description message",
  "data": {}
}
```

---

## 1. Authentication Router (`/api/v1/auth`)

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/signup` | `POST` | Public | Registers a new user account and provisions a sandbox Organization |
| `/login` | `POST` | Public | Validates user password and returns a JWT bearer token |

---

## 2. Dashboard Analytics & Monitoring (`/api/v1/dashboard`)

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Authenticated | Fetches analytics summaries (total calls, pipeline value, bookings) |
| `/active-calls` | `GET` | Authenticated | Retrieves ongoing call states, latency metrics, and confidence |

---

## 3. n8n Workflows Configuration (`/api/v1/dashboard/workflows`)

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Authenticated | Lists all registered webhook integrations mapped to n8n pipelines |
| `/{id}/toggle` | `PUT` | Authenticated | Toggles active/inactive execution triggers for the workflow |

---

## 4. Developer API Key Manager (`/api/v1/dashboard/keys`)

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Authenticated | Lists active API Key prefixes and metadata |
| `/` | `POST` | Authenticated | Generates a new API Key, hashing it using SHA-256 for secure storage |
| `/{id}` | `DELETE` | Authenticated | Revokes/deactivates the API Key |

---

## 5. Team Members & Audit Trail (`/api/v1/dashboard/team`)

| Endpoint | Method | Security | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | Authenticated | Lists colleagues and active RBAC roles within the Organization |
| `/invite` | `POST` | Admin/Manager | Invites a new team member and queues an invitation token |
| `/audit-logs` | `GET` | Authenticated | Pulls system audit entries (action, details, timestamp, IP) |
