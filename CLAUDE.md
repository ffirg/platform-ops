# Platform Ops

Ansible roles and playbooks for platform operations, including certificate checking.

## AAP Access

Use macOS keychain with `aap-credentials` service for AAP access. Use EITHER token OR username/password, not both.

```bash
# Hostname (always required)
AAP_HOST=$(security find-generic-password -s "aap-credentials" -a "aap-hostname" -w)

# Option 1: Token auth (preferred)
AAP_TOKEN=$(security find-generic-password -s "aap-credentials" -a "aap-token" -w)
curl -sk -H "Authorization: Bearer ${AAP_TOKEN}" "https://${AAP_HOST}/api/controller/v2/..."

# Option 2: Basic auth
AAP_USER=$(security find-generic-password -s "aap-credentials" -a "aap-username" -w)
AAP_PASS=$(security find-generic-password -s "aap-credentials" -a "aap-password" -w)
curl -sk -u "${AAP_USER}:${AAP_PASS}" "https://${AAP_HOST}/api/controller/v2/..."
```

Always prefix AAP API commands with these credential lookups. Never hardcode hostnames or credentials.

## Testing

Always follow `docs/testing/certificate-check-test-plan.md` when running certificate tests unless told otherwise.

## AAP Asset Management Rules

1. **Credentials from keychain**: Always obtain AAP credentials from macOS keychain unless explicitly told otherwise.

2. **Naming convention**: Prefix job templates with the GitHub repo name using pipe separator:
   - Format: `<repo-name> | <descriptive name>`
   - Example: `platform-ops | Check Server Certificates`

3. **Keep seed playbook in sync**: When creating, updating, or removing AAP assets (projects, credentials, inventories, hosts, job templates, etc.) via Ansible collections or API calls, always reflect those changes in `playbooks/seed-aap.yml`.

4. **Asset types to track in seed playbook**:
   - Organizations
   - Projects
   - Inventories and hosts
   - Credentials
   - Job templates
   - Workflow templates
   - Schedules

## API Paths

- Controller API: `/api/controller/v2/`
- Gateway API: `/api/gateway/v1/`

## Common Operations

- Sync project: `POST /api/controller/v2/projects/{id}/update/`
- Launch job: `POST /api/controller/v2/job_templates/{id}/launch/`
- Get job status: `GET /api/controller/v2/jobs/{id}/`
- Get job output: `GET /api/controller/v2/jobs/{id}/stdout/?format=txt`
- Ad-hoc command: `POST /api/controller/v2/ad_hoc_commands/`

## Target Host Requirements

For `community.crypto` modules, install on target hosts:
```bash
dnf install python3-cryptography
```
