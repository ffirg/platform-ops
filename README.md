# platform-ops

Automated certificate lifecycle management for enterprise infrastructure. Monitors SSL/TLS certificates across servers, detects expiring or expired certificates, and provides structured JSON output for integration with monitoring dashboards and self-service portals.

Built for Red Hat Ansible Automation Platform (AAP) with support for containerized, OpenShift, and Kubernetes deployments.

## Getting Started

```bash
git clone https://github.com/ffirg/platform-ops.git
cd platform-ops
```

## Prerequisites

### macOS Keychain Setup (Recommended)

Store AAP credentials securely in macOS Keychain:

```bash
# Add credentials (one-time setup)
security add-generic-password -s "aap-credentials" -a "aap-hostname" -w "your-aap-host.example.com"
security add-generic-password -s "aap-credentials" -a "aap-username" -w "admin"
security add-generic-password -s "aap-credentials" -a "aap-password" -w "yourpassword"

# Verify
security find-generic-password -s "aap-credentials" -a "aap-username" -w
```

Playbooks automatically retrieve credentials from keychain, with environment variables as fallback.

### Target Host Requirements

For `community.crypto` modules, install on target hosts:

```bash
dnf install python3-cryptography    # RHEL/CentOS/Fedora
apt install python3-cryptography    # Debian/Ubuntu
```

## AAP Seeding

### Requirements

- `infra.aap_configuration` collection
- AAP credentials in keychain or environment variables

### Usage

Bootstrap AAP with the Platform Ops project and job templates:

```bash
# Using keychain credentials (recommended)
ansible-playbook playbooks/seed-aap.yml

# Or with environment variables
export AAP_HOST=your-aap-host.example.com
export AAP_USERNAME=admin
export AAP_PASSWORD=yourpassword
ansible-playbook playbooks/seed-aap.yml
```

This creates:
- **Project**: Platform Ops (linked to this GitHub repo)
- **Inventory**: Platform Ops (host: aap-mgd-node-1.lan)
- **Job Templates**:
  - `platform-ops | Check Server Certificates`
  - `platform-ops | Check AAP Certificates`
  - `platform-ops | Setup Test Certs`
  - `platform-ops | Test Certificate Expiry`

## Certificate Checking

Extensible certificate checking for any server, with specialized support for Red Hat Ansible Automation Platform (AAP).

### Quick Start

```bash
# Check certificates on a server (auto-discovery)
ansible-playbook playbooks/check-certs.yml -i myserver.example.com,

# Check certificates with explicit file paths
ansible-playbook playbooks/check-certs.yml -i myserver.example.com, \
  -e '{"cert_checks": [{"name": "Nginx", "type": "file", "path": "/etc/nginx/ssl/server.crt"}]}'

# Check AAP certificates (requires AAP host with podman/oc/kubectl)
ansible-playbook playbooks/check-aap-certs.yml -i aap.example.com,

# Generate test certificates (requires become/sudo)
ansible-playbook playbooks/setup-test-certs.yml -i testserver.example.com, -K

# Test certificate expiry scenarios: ok, warning, critical, expired (requires become/sudo)
ansible-playbook playbooks/test-cert-expiry.yml -i testserver.example.com, \
  -e "cert_scenario=warning" -K
```

### Features

- **Auto-discovery**: Finds certificates automatically if no explicit paths provided
- **File-based checking**: Check certificate files on hosts via SSH
- **Certificate chain tracking**: Full chain information including root CA and intermediates
- **Multiple output formats**: Console, Markdown, JSON (for API/portal integration)
- **AAP-specific support**: Automatic discovery of AAP components (containerized, OpenShift, Kubernetes)
- **Configurable thresholds**: Warning and critical day thresholds for expiry alerts

### Playbooks

| Playbook | Description |
|----------|-------------|
| `check-certs.yml` | Generic certificate checking with auto-discovery |
| `check-aap-certs.yml` | AAP-specific certificate discovery and checking |
| `setup-test-certs.yml` | Generate test certificates on target hosts |
| `test-cert-expiry.yml` | Create certificates with specific expiry scenarios |
| `seed-aap.yml` | Bootstrap AAP with project and job templates |

### Roles

| Role | Description |
|------|-------------|
| `check_server_certs` | Orchestrates certificate checking with auto-discovery |
| `check_aap_certs` | AAP-specific certificate discovery and checking |
| `check_cert_file` | Check a single certificate file |
| `cert_report` | Generate reports (console, markdown, JSON) |
| `cert_common` | Shared defaults and variables |

### Usage Examples

#### Check all certificates on a server (auto-discovery)

```bash
ansible-playbook playbooks/check-certs.yml -i myserver.example.com,
```

#### Check specific certificate files

```yaml
# In your playbook or via -e
cert_checks:
  - name: "Nginx SSL"
    type: file
    path: /etc/nginx/ssl/server.crt
  - name: "PostgreSQL TLS"
    type: file
    path: /var/lib/pgsql/data/server.crt
```

#### Check AAP certificates

```bash
# Auto-detect platform
ansible-playbook playbooks/check-aap-certs.yml -i aap.example.com,

# Specify platform
ansible-playbook playbooks/check-aap-certs.yml -i aap.example.com, \
  -e "aap_platform=containerized"
```

### Output Formats

#### Console Output

```
═══════════════════════════════════════════════════════════════════════════════════════
                           CERTIFICATE EXPIRY REPORT
═══════════════════════════════════════════════════════════════════════════════════════
Host: server1.example.com
Platform: linux
Check Date: 2026-04-30T10:00:00Z
Thresholds: Warning=30 days, Critical=14 days
───────────────────────────────────────────────────────────────────────────────────────
CERTIFICATE               STATUS     SOURCE       DAYS   KEY             ISSUER
Nginx SSL                 [OK]       Let's Encrypt  145  rsaEncryption   R3
PostgreSQL TLS            [WARNING]  Self-Signed     12  rsaEncryption   localhost
───────────────────────────────────────────────────────────────────────────────────────
SUMMARY: Total=2 | OK=1 | Warning=1 | Critical=0 | Expired=0 | Missing=0
```

#### JSON Output (for API/Portal Integration)

The playbook outputs structured JSON that can be consumed by external services such as:

- **Self-Service Portals**: Display certificate status in user dashboards
- **Monitoring Systems**: Feed certificate data into Prometheus, Grafana, or Splunk
- **CMDB Integration**: Update configuration management databases with certificate inventory
- **Alerting Pipelines**: Trigger notifications via webhooks or message queues
- **Compliance Reporting**: Generate audit-ready certificate inventory reports

The JSON is output as a single line prefixed with `CERT_REPORT_JSON=` for easy parsing:

```json
{
  "host": "server1.example.com",
  "platform": "Linux",
  "checkDate": "2026-04-30T10:00:00Z",
  "thresholds": {
    "warningDays": 30,
    "criticalDays": 14
  },
  "summary": {
    "total": 2,
    "ok": 1,
    "warning": 1,
    "critical": 0,
    "expired": 0,
    "missing": 0
  },
  "certificates": [
    {
      "name": "Nginx SSL",
      "path": "/etc/nginx/ssl/server.crt",
      "type": "file",
      "status": "ok",
      "days_remaining": 145,
      "expiry_date": "20260922100000Z",
      "subject": "server1.example.com",
      "issuer": "R3",
      "serial": "123456789",
      "key_algorithm": "RSA",
      "key_size": 2048,
      "sig_algorithm": "sha256WithRSAEncryption",
      "chain": {
        "depth": 3,
        "root_ca": "ISRG Root X1",
        "is_self_signed": false,
        "chain_valid": true
      },
      "service": "nginx",
      "source": "Let's Encrypt"
    }
  ]
}
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `cert_warning_days` | 30 | Days before expiry to trigger warning |
| `cert_critical_days` | 14 | Days before expiry to trigger critical |
| `cert_show_paths` | false | Show file paths in output |
| `cert_show_chain` | true | Show certificate chain info |
| `cert_output_json` | true | Output JSON for API consumption |
| `cert_report_file` | "" | Path to save markdown report |
| `cert_fail_on_expired` | true | Fail playbook if expired certs found |
| `cert_fail_on_critical` | false | Fail playbook if critical certs found |
| `cert_fail_on_warning` | false | Fail playbook if warning certs found |

### Requirements

- Ansible 2.9+
- `community.crypto` collection
- `python3-cryptography` on target hosts
- For AAP: podman (containerized), oc (OpenShift), or kubectl (Kubernetes)

## Testing

See [docs/certificate-check-test-plan.md](docs/certificate-check-test-plan.md) for the certificate checking test plan and execution log.

## License

Apache 2.0
