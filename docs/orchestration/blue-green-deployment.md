# Blue-Green Deployment Workflow

Zero-downtime deployments with traffic switching and human approval gates.

## Overview

| Attribute | Value |
|-----------|-------|
| **Trigger** | Manual (with version input) |
| **AAP Job Template** | `platform-ops \| Blue-Green Demo` (ID: 27) |
| **Playbook** | `playbooks/blue_green_demo.yml` |
| **Role** | `roles/blue_green_demo/` |

## Workflow Flow

```
Trigger → Check Active → Calculate Target → Deploy → Health Check → Healthy?
                                                                      ├─ Yes → Approval → Approved?
                                                                      │                    ├─ Yes → Switch Traffic → Notify: Success
                                                                      │                    └─ No  → Notify: Rejected
                                                                      └─ No  → Notify: Health Failed
```

## Architecture

### Environments

| Environment | Port | Container |
|-------------|------|-----------|
| Blue | 9081 | `blue-green-blue` |
| Green | 9082 | `blue-green-green` |
| Staging | 9083 | (reserved) |

### Traffic Routing

Traffic is directed via a symlink that points to the active environment:

```
/tmp/blue-green-demo/active -> blue  (or green)
```

The playbook's `switch` operation updates this symlink atomically.

## Nodes

### 1. Check Active Environment (AAP Job)

Determines which environment is currently receiving traffic.

**Extra Vars:**
```json
{
  "bg_operation": "status"
}
```

**Output:**
```yaml
blue_green:
  active_environment: "blue"
  blue_status: "running"
  green_status: "stopped"
```

### 2. Calculate Target (Script Node)

Determines which environment to deploy to (opposite of active).

```python
import json
import os

active = os.environ.get('active_environment', 'blue')
target = 'green' if active == 'blue' else 'blue'

print(json.dumps({
    'target_environment': target,
    'active_environment': active
}))
```

### 3. Deploy to Target (AAP Job)

Deploys the new version to the inactive environment.

**Extra Vars:**
```json
{
  "bg_operation": "deploy",
  "bg_environment": "${calculate_target.result.target_environment}",
  "bg_version": "${trigger.input.version}"
}
```

### 4. Health Check (AAP Job)

Verifies the newly deployed container is healthy.

**Extra Vars:**
```json
{
  "bg_operation": "health_check",
  "bg_environment": "${calculate_target.result.target_environment}"
}
```

**Output:**
```yaml
blue_green:
  health_status: "healthy"
  response_code: 200
  response_time_ms: 45
```

### 5. Condition: Healthy?

```
${health_check.result.blue_green.health_status} == "healthy"
```

### 6. Approval: Service Switch

Human approval gate before switching production traffic.

**Configuration:**
```json
{
  "name": "Service Switch",
  "timeout": 3600,
  "on_timeout": "reject"
}
```

### 7. Switch Traffic (AAP Job)

Updates the active symlink to point to the new environment.

**Extra Vars:**
```json
{
  "bg_operation": "switch",
  "bg_environment": "${calculate_target.result.target_environment}"
}
```

## Playbook Operations

### status

Check which environment is currently active.

```bash
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=status"
```

### deploy

Deploy a version to a specific environment.

```bash
ansible-playbook playbooks/blue_green_demo.yml \
  -e "bg_operation=deploy" \
  -e "bg_environment=blue" \
  -e "bg_version=v2.0"
```

### health_check

Verify a container is running and responding.

```bash
ansible-playbook playbooks/blue_green_demo.yml \
  -e "bg_operation=health_check" \
  -e "bg_environment=blue"
```

### switch

Update the active symlink.

```bash
ansible-playbook playbooks/blue_green_demo.yml \
  -e "bg_operation=switch" \
  -e "bg_environment=blue"
```

### cleanup

Remove all demo containers and files.

```bash
ansible-playbook playbooks/blue_green_demo.yml -e "bg_operation=cleanup"
```

## Testing

### End-to-End Test

1. **Initial State**: Run `status` to see current active environment
2. **Run Workflow**: Trigger with `{"version": "v2.0"}`
3. **Monitor**: Watch execution in Nexus visualizer
4. **Approve**: When approval node activates, approve via UI or API
5. **Verify**: Check containers and active symlink

### Manual Verification

```bash
# Check running containers
podman ps --filter "name=blue-green"

# Check active environment
cat /tmp/blue-green-demo/active

# Test endpoints
curl http://localhost:9081  # Blue
curl http://localhost:9082  # Green
```

### Approval via API

```bash
# List pending approvals
curl http://localhost:8000/api/v1/approvals?status=pending

# Approve
curl -X PATCH http://localhost:8000/api/v1/approvals/{approval_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "notes": "Deployment verified"}'
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `bg_operation` | `status` | Operation to perform |
| `bg_environment` | - | Target environment (blue/green) |
| `bg_version` | - | Version string to deploy |
| `bg_port_blue` | 9081 | Blue environment port |
| `bg_port_green` | 9082 | Green environment port |
| `bg_base_dir` | `/tmp/blue-green-demo` | Demo working directory |

## Workflow JSON

Location: `orchestrator/workflows/blue-green-deployment.json`

See [orchestrator/README.md](../../orchestrator/README.md) for import instructions.
