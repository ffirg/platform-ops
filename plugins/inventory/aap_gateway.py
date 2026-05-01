#!/usr/bin/env python3
"""
Dynamic inventory for AAP infrastructure via Gateway API.

Discovers all AAP service nodes and groups them by service type:
  - aap_gateway: Gateway nodes
  - aap_controller: Controller nodes
  - aap_hub: Automation Hub nodes
  - aap_eda: Event-Driven Ansible nodes
  - aap_all: All unique AAP hosts

Credentials are retrieved from macOS Keychain (service: aap-credentials).
Use EITHER token OR username/password authentication.

Usage:
  ansible-playbook -i inventory/aap_gateway.py playbooks/check-aap-certs.yml

Requirements:
  - macOS with keychain credentials configured
  - AAP Gateway API access
"""

import json
import subprocess
import sys
import urllib.request
import ssl
from collections import defaultdict


def get_keychain_value(account: str) -> str:
    """Retrieve value from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "aap-credentials", "-a", account, "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_aap_credentials() -> tuple[str, str, str, str]:
    """Get AAP credentials from keychain. Returns (host, token, user, password)."""
    host = get_keychain_value("aap-hostname")
    token = get_keychain_value("aap-token")
    user = get_keychain_value("aap-username")
    password = get_keychain_value("aap-password")

    if not host:
        sys.stderr.write("Error: AAP hostname not found in keychain.\n")
        sys.stderr.write("Configure with:\n")
        sys.stderr.write('  security add-generic-password -s "aap-credentials" -a "aap-hostname" -w "your-host"\n')
        sys.exit(1)

    if not token and not (user and password):
        sys.stderr.write("Error: AAP credentials not found in keychain.\n")
        sys.stderr.write("Configure with EITHER token OR username/password:\n")
        sys.stderr.write('  # Token auth (preferred)\n')
        sys.stderr.write('  security add-generic-password -s "aap-credentials" -a "aap-token" -w "your-token"\n')
        sys.stderr.write('  # OR basic auth\n')
        sys.stderr.write('  security add-generic-password -s "aap-credentials" -a "aap-username" -w "admin"\n')
        sys.stderr.write('  security add-generic-password -s "aap-credentials" -a "aap-password" -w "password"\n')
        sys.exit(1)

    return host, token, user, password


def api_request(host: str, token: str, user: str, password: str, endpoint: str) -> dict:
    """Make authenticated request to AAP Gateway API."""
    import base64

    url = f"https://{host}/api/gateway/v1/{endpoint}"

    # Use token auth if available, otherwise basic auth
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    else:
        credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }

    # Disable SSL verification (for self-signed certs)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, context=ssl_context) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        sys.stderr.write(f"Error querying {url}: {e}\n")
        return {"results": []}


def build_inventory() -> dict:
    """Build Ansible inventory from AAP Gateway API."""
    host, token, user, password = get_aap_credentials()

    # Get service types for name mapping
    service_types_data = api_request(host, token, user, password, "service_types/")
    type_map = {st["id"]: st["name"] for st in service_types_data.get("results", [])}

    # Get all service nodes
    service_nodes = api_request(host, token, user, password, "service_nodes/")

    # Build groups by service type
    groups = defaultdict(lambda: {"hosts": []})
    all_hosts = set()
    hostvars = {}

    for node in service_nodes.get("results", []):
        address = node.get("address", "")
        if not address:
            continue

        # Get service type from cluster
        cluster_id = node.get("service_cluster")
        service_type_id = node.get("summary_fields", {}).get("service_cluster", {}).get("service_type")
        service_type = type_map.get(service_type_id, "unknown")

        # Add to service-specific group
        group_name = f"aap_{service_type}"
        if address not in groups[group_name]["hosts"]:
            groups[group_name]["hosts"].append(address)

        all_hosts.add(address)

        # Set host variables
        if address not in hostvars:
            hostvars[address] = {
                "aap_services": [],
                "aap_platform": "containerized"  # Default, could be detected
            }
        hostvars[address]["aap_services"].append(service_type)

    # Build final inventory structure
    inventory = {
        "_meta": {
            "hostvars": hostvars
        },
        "all": {
            "children": ["aap_all"]
        },
        "aap_all": {
            "hosts": list(all_hosts),
            "vars": {
                "cert_warning_days": 30,
                "cert_critical_days": 14
            }
        }
    }

    # Add service-specific groups
    for group_name, group_data in groups.items():
        inventory[group_name] = group_data
        if "children" not in inventory["aap_all"]:
            inventory["aap_all"]["children"] = []
        inventory["aap_all"]["children"].append(group_name)

    return inventory


def main():
    """Main entry point."""
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        inventory = build_inventory()
        print(json.dumps(inventory, indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == "--host":
        # Return empty dict for host-specific vars (we use _meta)
        print(json.dumps({}))
    else:
        sys.stderr.write("Usage: aap_gateway.py --list | --host <hostname>\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
