# Certificate Check Test Plan

Test plan for validating the certificate checking playbooks across all expiry scenarios.

## Prerequisites

- AAP instance with Platform Ops project synced
- Managed node with nginx installed (`aap-mgd-node-1.lan`)
- Job templates configured:
  - **Test Certificate Expiry** (id: 17) - generates test certificates
  - **Check Server Certificates** (id: 14) - runs certificate checks

## Test Scenarios

Run each scenario by launching the Test Certificate Expiry job template with the appropriate `cert_scenario` extra var, then run Check Server Certificates to verify detection.

### 1. OK Scenario (90 days to expiry)

**Generate cert:**
```yaml
extra_vars:
  cert_scenario: ok
```

**Expected result:**
- Status: `[OK] OK`
- Days remaining: 90
- No alerts displayed
- Summary shows `ok: 1`

### 2. WARNING Scenario (20 days to expiry)

**Generate cert:**
```yaml
extra_vars:
  cert_scenario: warning
```

**Expected result:**
- Status: `[WARN] WARNING`
- Days remaining: 20
- Alert: "1 certificate(s) expire within 30 days"
- Summary shows `warning: 1`

### 3. CRITICAL Scenario (10 days to expiry)

**Generate cert:**
```yaml
extra_vars:
  cert_scenario: critical
```

**Expected result:**
- Status: `[FAILED] CRITICAL`
- Days remaining: 10
- Alert: "1 certificate(s) expire within 14 days"
- Summary shows `critical: 1`

### 4. EXPIRED Scenario (5 days past expiry)

**Generate cert:**
```yaml
extra_vars:
  cert_scenario: expired
```

**Expected result:**
- Status: `[FAILED] EXPIRED`
- Days remaining: -5
- Alert: "1 certificate(s) have EXPIRED!"
- Summary shows `expired: 1`

## Validation Checklist

For each scenario, verify:

- [ ] Correct status classification in report output
- [ ] Accurate days remaining calculation
- [ ] Appropriate alert message displayed
- [ ] JSON report contains correct `status` and `days_remaining` values
- [ ] Summary counts match expected values

## Thresholds

Default thresholds (configurable via `cert_warning_days` and `cert_critical_days`):

| Status | Condition |
|--------|-----------|
| OK | > 30 days remaining |
| WARNING | 15-30 days remaining |
| CRITICAL | 1-14 days remaining |
| EXPIRED | <= 0 days remaining |

## API Commands

Launch test cert generation:
```bash
curl -sk -u "${AAP_USER}:${AAP_PASS}" -X POST \
  "https://carmaap1.lan/api/controller/v2/job_templates/17/launch/" \
  -H "Content-Type: application/json" \
  -d '{"extra_vars": {"cert_scenario": "warning"}}'
```

Launch certificate check:
```bash
curl -sk -u "${AAP_USER}:${AAP_PASS}" -X POST \
  "https://carmaap1.lan/api/controller/v2/job_templates/14/launch/" \
  -H "Content-Type: application/json" -d '{}'
```

Get job output:
```bash
curl -sk -u "${AAP_USER}:${AAP_PASS}" \
  "https://carmaap1.lan/api/controller/v2/jobs/{job_id}/stdout/?format=txt"
```

## Test Execution Log

| Date | Scenario | Result | Job IDs |
|------|----------|--------|---------|
| 2026-05-01 | OK | PASS | 405, 407 |
| 2026-05-01 | WARNING | PASS | 409, 411 |
| 2026-05-01 | CRITICAL | PASS | 413, 415 |
| 2026-05-01 | EXPIRED | PASS | 417, 419 |
