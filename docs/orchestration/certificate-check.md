# Certificate Expiration Check Workflow

Automated certificate monitoring with conditional Jira ticket creation.

## Overview

| Attribute | Value |
|-----------|-------|
| **Trigger** | Manual |
| **AAP Job Template** | `platform-ops \| Certificate Check` (ID: 26) |
| **Playbook** | `playbooks/check-certs.yml` |
| **Role** | `roles/check_server_certs/` |

## Workflow Flow

```
Trigger → Check Certificates → Any Expiring? 
                                 ├─ Yes → Create Jira Ticket → Notify: Expiring
                                 └─ No  → Notify: All Valid
```

## Nodes

### 1. Check Certificates (AAP Job Template)

Runs the certificate check playbook against target hosts.

**Configuration:**
```json
{
  "job_template_id": 26,
  "extra_vars": {}
}
```

**Output (via set_stats):**
```yaml
cert_check:
  total_checked: 5
  expiring_soon: 1
  already_expired: 0
  certificates:
    - name: "Nginx SSL"
      status: "warning"
      days_remaining: 20
      path: "/etc/nginx/ssl/server.crt"
```

### 2. Condition: Any Expiring?

Evaluates whether any certificates need attention.

**Condition:**
```
${check_certs.result.cert_check.expiring_soon} > 0 or ${check_certs.result.cert_check.already_expired} > 0
```

### 3. Create Jira Ticket (Script Node)

Creates a Jira ticket with certificate details.

**Script (Python):**
```python
import json
import os

# Access playbook output via environment
cert_data = json.loads(os.environ.get('cert_check', '{}'))
expiring = cert_data.get('expiring_soon', 0)
expired = cert_data.get('already_expired', 0)

# Build ticket description
certs = cert_data.get('certificates', [])
details = '\n'.join([
    f"- {c['name']}: {c['status']} ({c['days_remaining']} days)"
    for c in certs if c['status'] in ('warning', 'critical', 'expired')
])

result = {
    "summary": f"Certificate Alert: {expiring} expiring, {expired} expired",
    "description": f"Certificates requiring attention:\n{details}",
    "priority": "High" if expired > 0 else "Medium"
}
print(json.dumps(result))
```

### 4. Notify Nodes (Script)

Simple notification scripts for success/alert paths.

## Testing

### Generate Test Certificates

```bash
# OK scenario (90 days)
ansible-playbook playbooks/test-cert-expiry.yml -e "cert_scenario=ok"

# Warning scenario (20 days)
ansible-playbook playbooks/test-cert-expiry.yml -e "cert_scenario=warning"

# Critical scenario (10 days)
ansible-playbook playbooks/test-cert-expiry.yml -e "cert_scenario=critical"

# Expired scenario
ansible-playbook playbooks/test-cert-expiry.yml -e "cert_scenario=expired"
```

### Run Workflow

1. Open Nexus UI → Workflows → Certificate Expiration Check
2. Click Run
3. Monitor execution in the visualizer
4. Verify correct path taken based on certificate state

## Playbook Details

### Input Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cert_warning_days` | 30 | Days threshold for warning |
| `cert_critical_days` | 14 | Days threshold for critical |
| `cert_checks` | auto | Specific certs to check (optional) |

### Output Structure

The playbook uses `set_stats` to return data under the `cert_check` key:

```yaml
- name: Return results to orchestrator
  ansible.builtin.set_stats:
    data:
      cert_check:
        total_checked: "{{ cert_results | length }}"
        expiring_soon: "{{ cert_results | selectattr('status', 'in', ['warning', 'critical']) | list | length }}"
        already_expired: "{{ cert_results | selectattr('status', 'equalto', 'expired') | list | length }}"
        certificates: "{{ cert_results }}"
```

## Workflow JSON

Location: `aap-orchestrator/imports/certificate-check.json`

See [nexus-example-workflows.md](../../../aap-orchestrator/docs/nexus-example-workflows.md) for the full workflow definition.
