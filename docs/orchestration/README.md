# Nexus Orchestrator Use Cases

This directory documents the Nexus workflow use cases that leverage platform-ops playbooks.

## Overview

Platform-ops provides the Ansible automation (playbooks + roles) that execute within Nexus orchestrated workflows. Each workflow combines multiple AAP job invocations with orchestration logic.

## Use Cases

| Use Case | Document | Status |
|----------|----------|--------|
| Certificate Expiration Check | [certificate-check.md](certificate-check.md) | ✅ Tested |
| Blue-Green Deployment | [blue-green-deployment.md](blue-green-deployment.md) | ✅ Tested |
| EDA Auto-Remediation | [eda-auto-remediation.md](eda-auto-remediation.md) | ✅ Tested |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Nexus Orchestrator                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Triggers   │  │   Control   │  │  Executors  │         │
│  │  - Manual   │  │  - Condition│  │  - AAP Job  │         │
│  │  - Webhook  │  │  - Approval │  │  - Script   │         │
│  │  - Schedule │  │  - Loop     │  │  - Agentic  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Ansible Automation Platform                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Job Templates                     │   │
│  │  - platform-ops | Certificate Check                 │   │
│  │  - platform-ops | Blue-Green Demo                   │   │
│  │  - platform-ops | Website Remediation               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     platform-ops Repo                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Playbooks  │  │    Roles    │  │ Inventories │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Playbook → Workflow

Playbooks communicate results back to Nexus using Ansible's `set_stats` module:

```yaml
# In playbook
- name: Return results to orchestrator
  ansible.builtin.set_stats:
    data:
      cert_check:
        expiring_soon: 2
        certificates: [...]
```

Nexus workflow nodes reference this data:
```
${check_certs.result.cert_check.expiring_soon} > 0
```

## Workflow Files

Workflow JSON definitions are maintained in the orchestrator repo:

| Location | Purpose |
|----------|---------|
| `aap-orchestrator/imports/` | Source workflow definitions for import |
| `aap-orchestrator/exports/` | Exported working workflows (backup/reference) |

## Quick Reference

### AAP Job Template IDs

| ID | Template | Playbook |
|----|----------|----------|
| 26 | `platform-ops \| Certificate Check` | `check-certs.yml` |
| 27 | `platform-ops \| Blue-Green Demo` | `blue_green_demo.yml` |
| 28 | `platform-ops \| Website Remediation` | `website_remediation.yml` |

### AAP Credential IDs

| ID | Credential | Purpose |
|----|------------|---------|
| `68904b3c-...` | AAP Credential | Workflow → AAP authentication |
| `f2b8dfe2-...` | OpenRouter LLM | Agentic AI node (auto-remediation) |

### Nexus API

```bash
# Trigger workflow via webhook
curl -X POST http://localhost:8000/api/v1/webhooks/{path} \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Check execution status
curl http://localhost:8000/api/v1/executions/{execution_id}

# Approve/reject pending approval
curl -X PATCH http://localhost:8000/api/v1/approvals/{approval_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "notes": "..."}'
```
