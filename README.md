# platform-ops

Ansible roles for platform operations - certificate management, infrastructure checks, and operational automation.

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

## Certificate Checking

Extensible certificate checking for any server, with specialized support for Red Hat Ansible Automation Platform (AAP).

### Quick Start

```bash
# Clone the repo
git clone https://github.com/ffirg/platform-ops.git
cd platform-ops

# Check certificates on any server (auto-discovery)
ansible-playbook playbooks/check-certs.yml -i inventory/example.yml

# Check specific certificates
ansible-playbook playbooks/check-certs.yml -i localhost, \
  -e '{"cert_checks": [{"name": "GitHub", "type": "remote", "host": "github.com", "port": 443}]}'

# Check AAP certificates
ansible-playbook playbooks/check-aap-certs.yml -i aap-inventory.yml
```

### Features

- **Auto-discovery**: Finds certificates automatically if no explicit paths provided
- **File-based checking**: Check certificate files on hosts via SSH
- **Remote TLS checking**: Check remote endpoints via TLS handshake (no SSH needed)
- **Certificate chain tracking**: Full chain information including root CA and intermediates
- **Multiple output formats**: Console, Markdown, JSON (for API/portal integration)
- **AAP-specific support**: Automatic discovery of AAP components (containerized, OpenShift, Kubernetes)

### Roles

| Role | Description |
|------|-------------|
| `check_server_certs` | Generic certificate checking with auto-discovery |
| `check_aap_certs` | AAP-specific certificate discovery and checking |
| `check_cert_file` | Check a single certificate file |
| `check_cert_remote` | Check a certificate via TLS handshake |
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

#### Check remote TLS endpoints

```yaml
cert_checks:
  - name: "Production API"
    type: remote
    host: api.example.com
    port: 443
  - name: "Load Balancer"
    type: remote
    host: lb.example.com
    port: 8443
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

```json
{
  "host": "server1.example.com",
  "platform": "linux",
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
      "status": "ok",
      "days_remaining": 145,
      "chain": {
        "depth": 3,
        "root_ca": "ISRG Root X1",
        "is_self_signed": false
      }
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

## AAP Seeding

Bootstrap AAP with the Platform Ops project and job templates:

```bash
# Using keychain credentials (recommended)
ansible-playbook playbooks/seed-aap.yml

# Or with environment variables
export CONTROLLER_HOST=your-aap-host.example.com
export CONTROLLER_USERNAME=admin
export CONTROLLER_PASSWORD=yourpassword
ansible-playbook playbooks/seed-aap.yml
```

This creates:
- **Project**: Platform Ops (linked to this GitHub repo)
- **Inventory**: Platform Ops - Localhost
- **Job Templates**: Check Server Certificates, Check AAP Certificates

### Requirements

- `infra.aap_configuration` collection
- AAP credentials in keychain or environment variables

## Testing

See [docs/certificate-check-test-plan.md](docs/certificate-check-test-plan.md) for the certificate checking test plan and execution log.

## License

Apache 2.0
