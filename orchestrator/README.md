# Nexus Orchestrator Workflows

This directory contains workflow definitions for the Nexus Orchestrator that leverage platform-ops Ansible playbooks.

## Importing Workflows

These workflow JSON files can be imported directly into the Nexus Orchestrator UI:

1. Open **Nexus Orchestrator** → **Workflows**
2. Click **Import** (or **+ New Workflow** → **Import**)
3. Select the workflow JSON file from this directory
4. **Configure placeholders** (see below)
5. Save and publish the workflow

## Configuration Required

Before workflows will execute, you must replace placeholder values with your environment-specific IDs.

### Placeholder Values

| Placeholder | Description | How to Find |
|-------------|-------------|-------------|
| `__AAP_CREDENTIAL_ID__` | Nexus credential UUID for AAP authentication | Nexus UI → Credentials → copy ID |
| `__LLM_CREDENTIAL_ID__` | Nexus credential UUID for OpenRouter/LLM | Nexus UI → Credentials → copy ID |
| `__JOB_TEMPLATE_ID__` | AAP job template numeric ID | AAP UI → Templates → view ID in URL |
| `__TARGET_HOST__` | Target host for job execution | Your AAP inventory hostname |
| `__YOUR_AAP_HOSTNAME__` | AAP Gateway hostname (for cert checks) | Your AAP FQDN |

### Using Find & Replace

After importing, use your editor or the Nexus UI to find and replace:

```bash
# Example: Replace placeholders in imported workflow
sed -i 's/__AAP_CREDENTIAL_ID__/68904b3c-6319-470a-8be6-7a9d23ff019a/g' workflow.json
sed -i 's/__JOB_TEMPLATE_ID__/27/g' workflow.json
sed -i 's/__TARGET_HOST__/myserver.example.com/g' workflow.json
```

## Available Workflows

### blue-green-deployment.json

**Purpose:** Zero-downtime deployments with traffic switching and approval gates.

**Required AAP Job Template:** `platform-ops | Blue-Green Demo`

**Placeholders:**
- `__AAP_CREDENTIAL_ID__` — Nexus AAP credential
- `__JOB_TEMPLATE_ID__` — Job template ID (run `seed-aap.yml` first)
- `__TARGET_HOST__` — Host with podman for container deployments

**Flow:**
```
Trigger → Check Status → Calculate Target → Deploy → Health Check → Healthy?
                                                                      ├─ Yes → Approval → Switch → Success
                                                                      └─ No → Health Failed
```

---

### eda-auto-remediation.json

**Purpose:** AI-assisted incident remediation with automatic or escalated response.

**Required AAP Job Template:** `platform-ops | Website Remediation`

**Placeholders:**
- `__AAP_CREDENTIAL_ID__` — Nexus AAP credential
- `__LLM_CREDENTIAL_ID__` — OpenRouter/LLM credential for AI decisions
- `__JOB_TEMPLATE_ID__` — Job template ID

**Flow:**
```
Trigger → Analyze Alert → AI Decision → Auto-Remediate?
                                          ├─ Yes → Remediate → Success/Failed
                                          └─ No → Approval → Manual Remediate
```

---

### aap-certificate-checks.json

**Purpose:** Check AAP platform SSL certificates with per-certificate loop processing.

**Required AAP Job Template:** `platform-ops | Check AAP Certificates`

**Placeholders:**
- `__AAP_CREDENTIAL_ID__` — Nexus AAP credential
- `__JOB_TEMPLATE_ID__` — Job template ID
- `__YOUR_AAP_HOSTNAME__` — AAP Gateway hostname (in trigger defaults)

**Flow:**
```
Trigger → Discover Certs → Loop Each Cert → Actions → Consolidated Report
```

---

## Prerequisites

### 1. Seed AAP

Run the AAP seeding playbook to create required job templates:

```bash
ansible-playbook playbooks/seed-aap.yml
```

This creates:
- `platform-ops | Blue-Green Demo` (ID varies by environment)
- `platform-ops | Website Remediation` (ID varies by environment)
- `platform-ops | Check AAP Certificates` (ID varies by environment)

### 2. Create Nexus Credentials

In Nexus UI → **Credentials**, create:

1. **AAP Credential** — Type: AAP, with your AAP hostname and credentials
2. **LLM Credential** (for EDA workflow) — Type: OpenRouter, with API key

### 3. Get IDs

After creating resources, collect the IDs:

```bash
# Get AAP job template IDs
curl -sk -u admin:password https://your-aap/api/controller/v2/job_templates/ | jq '.results[] | {name, id}'

# Nexus credential IDs are shown in the Credentials list UI
```

## Security Notes

These workflow files are sanitized templates:
- No actual credentials or secrets
- No environment-specific hostnames
- No hardcoded IPs

The `_configuration_required` field in each JSON documents what needs to be configured.

## Updating Workflows

To export an updated workflow from Nexus:

1. Open the workflow in Nexus UI
2. Click **Export** (or use API: `GET /api/v1/workflows/{id}`)
3. Save to this directory
4. **Sanitize** before committing:
   - Replace credential UUIDs with `__AAP_CREDENTIAL_ID__` etc.
   - Replace hostnames with `__TARGET_HOST__` etc.
   - Remove any environment-specific data

## Related Documentation

- [Orchestration Use Cases](../docs/orchestration/) — Detailed workflow documentation
- [AAP Seeding](../playbooks/seed-aap.yml) — Creates required AAP resources
