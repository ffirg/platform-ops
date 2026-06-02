# platform-ops

Automated operations for enterprise infrastructure, designed for Red Hat Ansible Automation Platform (AAP) and Nexus Orchestrator integration.

## Capabilities

| Domain | Description |
|--------|-------------|
| **Certificate Management** | SSL/TLS certificate monitoring with auto-discovery, expiry alerts, and structured output |
| **Blue-Green Deployments** | Zero-downtime deployments with traffic switching and approval gates |
| **Website Remediation** | AI-assisted incident analysis and auto-remediation for service failures |

## Quick Start

```bash
git clone https://github.com/ffirg/platform-ops.git
cd platform-ops
```

### AAP Bootstrap

```bash
# Configure credentials (see Prerequisites below)
ansible-playbook playbooks/seed-aap.yml
```

This creates the Platform Ops project, inventories, credentials, and job templates in AAP.

---

## Nexus Orchestrator Integration

This repository provides the Ansible automation that powers Nexus workflow use cases. Each workflow combines AAP job templates with orchestration logic (conditions, approvals, AI decisions).

### Workflow Use Cases

| Workflow | Description | Job Template |
|----------|-------------|--------------|
| **Certificate Expiration Check** | Check certs → conditional Jira ticket → notification | `platform-ops \| Certificate Check` |
| **Blue-Green Deployment** | Deploy → health check → approval → traffic switch | `platform-ops \| Blue-Green Demo` |
| **EDA Auto-Remediation** | Analyze failure → AI decision → auto-fix or escalate | `platform-ops \| Website Remediation` |

### AAP Job Templates

| ID | Job Template | Playbook | Description |
|----|--------------|----------|-------------|
| 26 | `platform-ops \| Certificate Check` | `check-certs.yml` | Check certificates with auto-discovery |
| 27 | `platform-ops \| Blue-Green Demo` | `blue_green_demo.yml` | Multi-operation deployment (status/deploy/health/switch/cleanup) |
| 28 | `platform-ops \| Website Remediation` | `website_remediation.yml` | Analyze and remediate website failures |

### Workflow JSON Files

Workflow definitions for import into Nexus are stored in the orchestrator repo:

```
aap-orchestrator/
├── imports/           # Workflow JSON for import
│   ├── certificate-check.json
│   ├── blue-green-demo.json
│   └── eda-auto-remediation.json
└── exports/           # Exported working workflows
```

---

## Certificate Management

Extensible certificate checking for any server, with specialized support for AAP.

### Features

- **Auto-discovery**: Finds certificates automatically if no explicit paths provided
- **AAP-specific support**: Automatic discovery of AAP components (containerized, OpenShift, Kubernetes)
- **Multiple output formats**: Console, Markdown, JSON (for API/portal integration)
- **Configurable thresholds**: Warning (30 days) and critical (14 days) alerts

### Playbooks

| Playbook | Description |
|----------|-------------|
| `check-certs.yml` | Generic certificate checking with auto-discovery |
| `check-aap-certs.yml` | AAP-specific certificate discovery and checking |
| `setup-test-certs.yml` | Generate test certificates on target hosts |
| `test-cert-expiry.yml` | Create certificates with specific expiry scenarios |

### Usage

```bash
# Check all certificates on a server (auto-discovery)
ansible-playbook playbooks/check-certs.yml -i myserver.example.com,

# Check AAP certificates (auto-discovers nodes from Gateway API)
ansible-playbook playbooks/check-aap-certs.yml
```

### Orchestrator Integration

The certificate check workflow uses `set_stats` to return structured data:

```yaml
# Output structure (under cert_check key)
cert_check:
  total_checked: 5
  expiring_soon: 1
  already_expired: 0
  certificates:
    - name: "Nginx SSL"
      status: "warning"
      days_remaining: 20
```

Nexus workflow conditions evaluate `${check_certs.result.cert_check.expiring_soon} > 0` to route to Jira ticket creation.

---

## Blue-Green Deployments

Zero-downtime deployment pattern using containerized environments with approval gates.

### Architecture

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

### Operations

The `blue_green_demo.yml` playbook supports multiple operations via `bg_operation`:

| Operation | Description |
|-----------|-------------|
| `status` | Check which environment is currently active |
| `deploy` | Deploy version to specified environment |
| `health_check` | Verify container is running and responding |
| `switch` | Update active symlink to new environment |
| `cleanup` | Remove all demo containers and files |

### Usage

```bash
# Check current status
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=status"

# Deploy v2.0 to blue environment
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=deploy bg_environment=blue bg_version=v2.0"

# Health check blue
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=health_check bg_environment=blue"

# Switch traffic to blue
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=switch bg_environment=blue"
```

### Orchestrator Integration

The Nexus workflow sequences these operations with an approval gate before switching:

```
Deploy → Health Check → Healthy?
                         ├─ Yes → Approval → Approved? → Switch → Notify
                         │                   └─ Rejected → Notify
                         └─ No → Notify Failed
```

---

## Website Remediation

AI-assisted incident analysis and auto-remediation for EDA-triggered alerts.

### Operations

| Operation | Description |
|-----------|-------------|
| `analyze` | Classify failure type and recommend action |
| `remediate` | Execute remediation action |

### Failure Classifications

| Classification | Recommended Action | Auto-Remediate |
|----------------|-------------------|----------------|
| `connection_refused` | `restart_service` | ✅ Yes |
| `connection_timeout` | `restart_service` | ✅ Yes |
| `http_500` | `restart_service` | ✅ Yes |
| `dns_failure` | `check_dns` | ❌ No |
| `ssl_error` | `check_ssl` | ❌ No |
| `http_502` | `check_upstream` | ❌ No |
| `http_503` | `check_capacity` | ❌ No |

### Orchestrator Integration

The EDA Auto-Remediation workflow uses an **agentic AI node** to decide whether to auto-remediate or escalate:

```
Analyze Alert → AI Decision → Auto-Remediate?
                               ├─ Yes (low risk) → Run Remediation → Notify
                               └─ No (high risk) → Approval → Manual Fix → Notify
```

The AI evaluates failure context and returns a structured decision with risk assessment.

---

## Roles

| Role | Description |
|------|-------------|
| `discover_aap_nodes` | Discovers AAP nodes from Gateway API via `add_host` |
| `check_server_certs` | Orchestrates certificate checking with auto-discovery |
| `check_aap_certs` | AAP-specific certificate discovery and checking |
| `check_cert_file` | Check a single certificate file |
| `cert_report` | Generate reports (console, markdown, JSON) |
| `cert_common` | Shared defaults and variables |
| `blue_green_demo` | Blue-green deployment operations |
| `website_remediation` | Website failure analysis and remediation |

---

## Prerequisites

### macOS Keychain Setup

Store AAP credentials securely:

```bash
# Hostname (required)
security add-generic-password -s "aap-credentials" -a "aap-hostname" -w "your-aap-host.example.com"

# Token auth (preferred)
security add-generic-password -s "aap-credentials" -a "aap-token" -w "your-oauth-token"

# Or basic auth
security add-generic-password -s "aap-credentials" -a "aap-username" -w "admin"
security add-generic-password -s "aap-credentials" -a "aap-password" -w "yourpassword"
```

### Target Host Requirements

For certificate checking:
```bash
dnf install python3-cryptography    # RHEL/CentOS/Fedora
```

For blue-green deployments:
```bash
dnf install podman                  # Container runtime
```

---

## Configuration

### Certificate Checking

| Variable | Default | Description |
|----------|---------|-------------|
| `cert_warning_days` | 30 | Days before expiry to trigger warning |
| `cert_critical_days` | 14 | Days before expiry to trigger critical |
| `cert_output_json` | true | Output JSON for API consumption |

### Blue-Green Demo

| Variable | Default | Description |
|----------|---------|-------------|
| `bg_operation` | `status` | Operation to perform |
| `bg_environment` | - | Target environment (blue/green) |
| `bg_version` | - | Version to deploy |
| `bg_port_blue` | 9081 | Blue environment port |
| `bg_port_green` | 9082 | Green environment port |

---

## Testing

- [Certificate Check Test Plan](docs/testing/certificate-check-test-plan.md)

---

## Related Documentation

- [Nexus Example Workflows](../aap-orchestrator/docs/nexus-example-workflows.md) — Full workflow documentation
- [Nexus Workflow Schemas](../aap-orchestrator/docs/nexus-workflow-schemas-verified.md) — JSON schema reference

---

## License

Apache 2.0
