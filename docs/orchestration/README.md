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

Workflow JSON definitions are included in this repository for direct import into Nexus:

```
platform-ops/
└── orchestrator/
    ├── README.md                      # Import instructions
    └── workflows/
        ├── aap-certificate-checks.json
        ├── blue-green-deployment.json
        └── eda-auto-remediation.json
```

**Import Instructions:** See [orchestrator/README.md](../../orchestrator/README.md) for configuration placeholders and step-by-step import guide.

## Quick Reference

### AAP Job Templates

| Template | Playbook | Created By |
|----------|----------|------------|
| `platform-ops \| Check Server Certificates` | `check-certs.yml` | `seed-aap.yml` |
| `platform-ops \| Check AAP Certificates` | `check-aap-certs.yml` | `seed-aap.yml` |
| `platform-ops \| Blue-Green Demo` | `blue_green_demo.yml` | `seed-aap.yml` |
| `platform-ops \| Website Remediation` | `website_remediation.yml` | `seed-aap.yml` |

**Note:** Job template IDs are environment-specific. Run `seed-aap.yml` to create templates, then get IDs from your AAP instance.

### Nexus Credentials Required

| Credential Type | Purpose | Workflow |
|-----------------|---------|----------|
| AAP Credential | Authenticate to AAP API | All workflows |
| OpenRouter/LLM Credential | AI decision-making | EDA Auto-Remediation only |

Create these in Nexus UI → Credentials before importing workflows.

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
