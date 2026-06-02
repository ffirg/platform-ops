# EDA Auto-Remediation Workflow

AI-assisted incident remediation triggered by Event-Driven Ansible, with automatic or escalated response based on risk assessment.

## Overview

| Attribute | Value |
|-----------|-------|
| **Trigger** | Manual (designed for EDA webhook) |
| **AAP Job Template** | `platform-ops \| Website Remediation` (ID: 28) |
| **Playbook** | `playbooks/website_remediation.yml` |
| **Role** | `roles/website_remediation/` |
| **AI Provider** | OpenRouter (Claude) |

## Workflow Flow

```
Trigger → Analyze Alert (AAP) → AI Decision → Parse Decision → Auto-Remediate?
                                                                  ├─ Yes → Run Remediation → Success?
                                                                  │                            ├─ Yes → Notify: Success
                                                                  │                            └─ No  → Notify: Failed
                                                                  └─ No  → Escalation Review (Approval)
                                                                                    ├─ Approved → Manual Remediation → Notify
                                                                                    └─ Rejected → Notify: Rejected
```

## Key Components

### Agentic AI Node

The workflow uses Nexus's **agentic node** to make remediation decisions. The AI evaluates the failure context and returns a structured decision.

**Configuration:**
```json
{
  "type": "agentic",
  "config": {
    "credential_id": "f2b8dfe2-b0c9-4564-87e5-e8ff71086c66",
    "prompt": "Analyze this website failure and decide whether to auto-remediate or escalate...",
    "response_schema": {
      "type": "object",
      "properties": {
        "decision": {"enum": ["AUTO_REMEDIATE", "ESCALATE"]},
        "reason": {"type": "string"},
        "risk_level": {"enum": ["low", "medium", "high"]}
      }
    }
  }
}
```

**Output Path:**
```
${ai_decision.result.result.content.decision}
```

Note: Agentic nodes have nested `result.result.content` structure for structured output.

### Failure Classifications

The playbook's `analyze` operation classifies failures and recommends actions:

| Classification | Recommended Action | Auto-Remediate |
|----------------|-------------------|----------------|
| `connection_refused` | `restart_service` | ✅ Yes |
| `connection_timeout` | `restart_service` | ✅ Yes |
| `http_500` | `restart_service` | ✅ Yes |
| `dns_failure` | `check_dns` | ❌ No |
| `ssl_error` | `check_ssl` | ❌ No |
| `http_502` | `check_upstream` | ❌ No |
| `http_503` | `check_capacity` | ❌ No |
| `unknown` | `escalate` | ❌ No |

## Nodes

### 1. Analyze Alert (AAP Job)

Analyzes the failure and classifies it.

**Extra Vars:**
```json
{
  "remediation_operation": "analyze",
  "alert_url": "${trigger.input.url}",
  "alert_error": "${trigger.input.error}"
}
```

**Output:**
```yaml
remediation:
  classification: "connection_refused"
  recommended_action: "restart_service"
  confidence: 0.95
  details: "Connection refused on port 9081"
```

### 2. AI Decision (Agentic Node)

AI evaluates the failure context and decides on response strategy.

**Prompt Template:**
```
You are an SRE assistant. Analyze this website failure:

URL: ${analyze_alert.result.remediation.alert_url}
Error: ${analyze_alert.result.remediation.classification}
Recommended Action: ${analyze_alert.result.remediation.recommended_action}

Decide whether to AUTO_REMEDIATE (low risk, well-understood failure) 
or ESCALATE (needs human review).
```

**Response Schema:**
```json
{
  "decision": "AUTO_REMEDIATE",
  "reason": "Connection refused is a common transient failure, restart is safe",
  "risk_level": "low"
}
```

### 3. Parse Decision (Script Node)

Extracts the decision for the condition node.

```python
import json
import os

decision_raw = os.environ.get('ai_decision', '{}')
decision_data = json.loads(decision_raw)

result = {
    'should_auto_remediate': decision_data.get('decision') == 'AUTO_REMEDIATE',
    'risk_level': decision_data.get('risk_level', 'unknown'),
    'reason': decision_data.get('reason', '')
}
print(json.dumps(result))
```

### 4. Condition: Auto-Remediate?

```
${parse_decision.result.should_auto_remediate} == true
```

### 5. Run Remediation (AAP Job)

Executes the recommended remediation action.

**Extra Vars:**
```json
{
  "remediation_operation": "remediate",
  "remediation_action": "${analyze_alert.result.remediation.recommended_action}",
  "target_url": "${trigger.input.url}"
}
```

### 6. Escalation Review (Approval)

Human approval gate for high-risk remediations.

**Configuration:**
```json
{
  "name": "Escalation Review",
  "description": "AI flagged this for human review: ${parse_decision.result.reason}",
  "timeout": 1800,
  "on_timeout": "reject"
}
```

## Playbook Operations

### analyze

Classify the failure and recommend action.

```bash
ansible-playbook playbooks/website_remediation.yml \
  -e "remediation_operation=analyze" \
  -e "alert_url=http://192.168.138.212:9081" \
  -e "alert_error=connection_refused"
```

### remediate

Execute a remediation action.

```bash
ansible-playbook playbooks/website_remediation.yml \
  -e "remediation_operation=remediate" \
  -e "remediation_action=restart_service" \
  -e "target_url=http://192.168.138.212:9081"
```

## EDA Integration

The workflow is designed to be triggered by Event-Driven Ansible monitoring. Example rulebook:

```yaml
# extensions/eda/rulebooks/website_monitor.yml
---
- name: Website Monitoring
  hosts: all
  sources:
    - ansible.eda.url_check:
        urls:
          - http://192.168.138.212:9081  # Blue
          - http://192.168.138.212:9082  # Green
        delay: 30

  rules:
    - name: Website down - trigger remediation
      condition: event.url_check.status == "down"
      throttle:
        once_within: 5 minutes
        group_by_attributes:
          - event.url_check.url
      action:
        run_job_template:
          name: "platform-ops | Website Remediation"
          extra_vars:
            alert_url: "{{ event.url_check.url }}"
            alert_error: "{{ event.url_check.error | default('unknown') }}"
            remediation_operation: "analyze"
```

## Testing

### Simulate Failure

```bash
# Stop a blue-green container to trigger connection_refused
podman stop blue-green-blue

# Run the workflow manually with failure context
# In Nexus UI, trigger with:
{
  "url": "http://192.168.138.212:9081",
  "error": "connection_refused"
}
```

### Expected Outcomes

| Failure Type | AI Decision | Path |
|--------------|-------------|------|
| `connection_refused` | AUTO_REMEDIATE (low risk) | Auto-fix → Success |
| `ssl_error` | ESCALATE (high risk) | Approval → Manual |
| `dns_failure` | ESCALATE (infrastructure) | Approval → Manual |

### Verify Remediation

```bash
# Check container was restarted
podman ps --filter "name=blue-green-blue"

# Check endpoint recovered
curl http://192.168.138.212:9081
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `remediation_operation` | - | Operation: `analyze` or `remediate` |
| `alert_url` | - | URL that triggered the alert |
| `alert_error` | - | Error type from monitoring |
| `remediation_action` | - | Action to execute (for remediate) |

## Credentials

| Credential | ID | Purpose |
|------------|-----|---------|
| OpenRouter LLM | `f2b8dfe2-b0c9-4564-87e5-e8ff71086c66` | AI decision node |
| AAP Credential | `68904b3c-6319-470a-8be6-7a9d23ff019a` | Workflow → AAP auth |

## Workflow JSON

Location: `aap-orchestrator/imports/eda-auto-remediation.json`

See [nexus-example-workflows.md](../../../aap-orchestrator/docs/nexus-example-workflows.md) for the full workflow definition.
