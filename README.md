# platform-ops

This repository provides two types of content for enterprise infrastructure automation:

1. **AAP Automation Content** — Ansible playbooks and roles that execute automation tasks to configure systems and achieve desired end states
2. **Orchestrator Workflows** — Nexus workflow definitions that sequence and coordinate the automation content with control logic, approvals, and AI-assisted decisions

---

## Part 1: AAP Automation Content

Ansible automation for Red Hat Ansible Automation Platform (AAP). These playbooks and roles perform the actual work — checking certificates, deploying containers, remediating failures.

### Use Cases

| Domain | What It Does |
|--------|--------------|
| **Certificate Management** | Monitor SSL/TLS certificates across infrastructure. Auto-discover certificates, check expiry dates, generate alerts for expiring/expired certs, output structured reports. |
| **Blue-Green Deployments** | Zero-downtime deployments using container-based environments. Deploy new versions to inactive environment, verify health, switch traffic atomically. |
| **Website Remediation** | Analyze website failures, classify root causes, execute remediation actions (restart services, check DNS, validate SSL). |

### Quick Start

```bash
git clone https://github.com/ffirg/platform-ops.git
cd platform-ops
```

### Prerequisites

**AAP Credentials** — Configure via environment variables or macOS Keychain:

```bash
# Option 1: Environment variables
export CONTROLLER_HOST="your-aap-gateway.example.com"
export CONTROLLER_USERNAME="your-username"
export CONTROLLER_PASSWORD="your-password"
# Or use token auth:
export CONTROLLER_OAUTH_TOKEN="your-oauth-token"

# Option 2: macOS Keychain
security add-generic-password -s "aap-credentials" -a "aap-hostname" -w "<your-aap-host>"
security add-generic-password -s "aap-credentials" -a "aap-token" -w "<your-oauth-token>"
# Or basic auth:
security add-generic-password -s "aap-credentials" -a "aap-username" -w "<your-username>"
security add-generic-password -s "aap-credentials" -a "aap-password" -w "<your-password>"
```

**Target Host Requirements:**
```bash
dnf install python3-cryptography    # For certificate checking
dnf install podman                   # For blue-green deployments
```

### Seed AAP

```bash
# Create project, inventories, credentials, and job templates in AAP
ansible-playbook playbooks/seed-aap.yml
```

### Job Templates Created

| Job Template | Playbook | Purpose |
|--------------|----------|---------|
| `platform-ops \| Check Server Certificates` | `check-certs.yml` | Generic certificate checking with auto-discovery |
| `platform-ops \| Check AAP Certificates` | `check-aap-certs.yml` | AAP-specific certificate discovery |
| `platform-ops \| Blue-Green Demo` | `blue_green_demo.yml` | Multi-operation deployment (status/deploy/health/switch) |
| `platform-ops \| Website Remediation` | `website_remediation.yml` | Failure analysis and remediation |
| `platform-ops \| Setup Test Certs` | `setup-test-certs.yml` | Generate test certificates |
| `platform-ops \| Test Certificate Expiry` | `test-cert-expiry.yml` | Create certs with specific expiry scenarios |

---

### Certificate Management

Extensible certificate checking for any server, with specialized support for AAP infrastructure.

**Required AAP Credentials:**

| Credential | Type | Purpose |
|------------|------|---------|
| Platform Ops AAP | Red Hat Ansible Automation Platform | Gateway API access to discover AAP nodes |
| Platform Ops Machine | Machine | SSH access to check certificates on discovered nodes |

Create these in **AAP → Credentials** before running the certificate check job template.

**Features:**
- **Auto-discovery**: Finds certificates automatically if no explicit paths provided
- **AAP-specific support**: Automatic discovery of AAP components (containerized, OpenShift, Kubernetes)
- **Multiple output formats**: Console, Markdown, JSON (for API/portal integration)
- **Configurable thresholds**: Warning (30 days) and critical (14 days) alerts

**Usage:**
```bash
# Check all certificates on a server (auto-discovery)
ansible-playbook playbooks/check-certs.yml -i myserver.example.com,

# Check AAP certificates (auto-discovers nodes from Gateway API)
ansible-playbook playbooks/check-aap-certs.yml
```

**Output Structure (via set_stats):**
```yaml
cert_check:
  total_checked: 5
  expiring_soon: 1
  already_expired: 0
  certificates:
    - name: "Nginx SSL"
      status: "warning"
      days_remaining: 20
```

---

### Blue-Green Deployments

Zero-downtime deployment pattern using containerized environments.

**Architecture:**
```
┌─────────────┐     ┌─────────────┐
│    Blue     │     │    Green    │
│  (9081)     │     │  (9082)     │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────┴──────┐
        │   Active    │
        │  Symlink    │
        └─────────────┘
```

**Operations (via `bg_operation` variable):**

| Operation | Description |
|-----------|-------------|
| `status` | Check which environment is currently active |
| `deploy` | Deploy version to specified environment |
| `health_check` | Verify container is running and responding |
| `switch` | Update active symlink to new environment |
| `cleanup` | Remove all demo containers and files |

**Usage:**
```bash
# Check current status
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=status"

# Deploy v2.0 to blue environment
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=deploy bg_environment=blue bg_version=v2.0"

# Switch traffic to blue
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=switch bg_environment=blue"
```

---

### Website Remediation

Failure analysis and remediation for website monitoring alerts.

**Operations:**

| Operation | Description |
|-----------|-------------|
| `analyze` | Classify failure type and recommend action |
| `remediate` | Execute remediation action |

**Failure Classifications:**

| Classification | Recommended Action | Auto-Remediate Safe |
|----------------|-------------------|---------------------|
| `connection_refused` | `restart_service` | ✅ Yes |
| `connection_timeout` | `restart_service` | ✅ Yes |
| `http_500` | `restart_service` | ✅ Yes |
| `dns_failure` | `check_dns` | ❌ No |
| `ssl_error` | `check_ssl` | ❌ No |
| `http_502` | `check_upstream` | ❌ No |
| `http_503` | `check_capacity` | ❌ No |

---

## Part 2: Orchestrator Workflows

Nexus Orchestrator workflow definitions that sequence the automation content above with control flow logic. Workflows add:

- **Conditional branching** — Route execution based on automation results
- **Approval gates** — Human review before critical actions
- **AI-assisted decisions** — LLM-powered analysis and risk assessment
- **Loops** — Process collections of items (e.g., certificates)
- **Notifications** — Structured output for downstream systems

### Workflow Files

```
platform-ops/
└── orchestrator/
    ├── README.md                      # Import instructions & configuration
    └── workflows/
        ├── aap-certificate-checks.json
        ├── blue-green-deployment.json
        └── eda-auto-remediation.json
```

### Available Workflows

| Workflow | Automation Used | Orchestration Logic |
|----------|-----------------|---------------------|
| **Certificate Checks** | `Check AAP Certificates` | Loop each cert → Actions per status → Consolidated report |
| **Blue-Green Deployment** | `Blue-Green Demo` | Status → Deploy → Health check → Approval gate → Switch |
| **EDA Auto-Remediation** | `Website Remediation` | Analyze → AI decision (auto-fix vs escalate) → Approval if needed |

### How Workflows Use Automation

Workflows reference AAP job templates **by name**, not ID:

```json
{
  "type": "aap_job_template",
  "config": {
    "job_template_name": "platform-ops | Blue-Green Demo",
    "organization_name": "Default",
    "extra_vars": {
      "bg_operation": "deploy",
      "bg_environment": "${calculate_target.target_env}"
    }
  }
}
```

The Nexus backend resolves names to IDs at runtime via AAP's API.

### Workflow Patterns

**Certificate Check Flow:**
```
Trigger → Discover Certs (AAP) → Loop Each Cert → Actions → Consolidated Report
```

**Blue-Green Deployment Flow:**
```
Trigger → Check Status (AAP) → Calculate Target → Deploy (AAP) → Health Check (AAP)
    → Healthy? ─┬─ Yes → Approval → Switch (AAP) → Notify Success
                └─ No  → Notify Health Failed
```

**EDA Auto-Remediation Flow:**
```
Trigger → Analyze Alert (AAP) → AI Decision → Auto-Remediate?
    ├─ Yes (low risk)  → Run Remediation (AAP) → Notify
    └─ No (high risk)  → Approval → Manual Remediation (AAP) → Notify
```

### Importing Workflows

1. Run `seed-aap.yml` to create required job templates in AAP
2. Create Nexus credentials (AAP credential, optionally LLM credential)
3. Import workflow JSON from `orchestrator/workflows/`
4. Replace placeholder values (`__AAP_CREDENTIAL_ID__`, etc.)

See [orchestrator/README.md](orchestrator/README.md) for detailed instructions.

---

## License

Apache 2.0
