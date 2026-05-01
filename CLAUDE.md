# Platform Ops

Ansible roles and playbooks for platform operations, including certificate checking.

## AAP Access

Use macOS keychain with `aap-credentials` service for AAP access:

```bash
AAP_HOST=$(security find-generic-password -s "aap-credentials" -a "aap-hostname" -w)
AAP_USER=$(security find-generic-password -s "aap-credentials" -a "aap-username" -w)
AAP_PASS=$(security find-generic-password -s "aap-credentials" -a "aap-password" -w)
curl -sk -u "${AAP_USER}:${AAP_PASS}" "https://${AAP_HOST}/api/controller/v2/..."
```

Always prefix AAP API commands with these credential lookups. Never hardcode hostnames or credentials.

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
