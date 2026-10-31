import ipaddress
import re


def check_rules(show_output):

    findings = []
    output = show_output.lower()

    # ============================================================
    # 1. INTERFACE DOWN
    # ============================================================

    if "administratively down" in output:
        findings.append(
            "❌ Interface is administratively down (shutdown)."
        )
    elif re.search(r"\bdown\s+down\b", output):
        findings.append(
            "❌ Interface and line protocol are down."
        )
    elif re.search(r"\bup\s+down\b", output):
        findings.append(
            "⚠️ Interface is up but line protocol is down."
        )

    # ============================================================
    # 2. MISSING ROUTE / DEFAULT ROUTE
    # ============================================================

    if "gateway of last resort is not set" in output:
        findings.append(
            "❌ Default route is not configured (missing default gateway)."
        )
    elif "no default route" in output:
        findings.append(
            "❌ No default route detected."
        )
    elif (
        "network unreachable" in output
        or "route not found" in output
    ):
        findings.append(
            "❌ Required route to destination network is missing."
        )

    # ============================================================
    # 3. MISSING VLAN
    # ============================================================

    if (
        re.search(r"vlan\s*\d*\s*(?:not found|does not exist|missing|unassigned)", output)
        or ("vlan" in output and ("not found" in output or "does not exist" in output))
    ):
        findings.append(
            "❌ VLAN is missing or not configured on switch."
        )

    # ============================================================
    # 4. DUPLICATE IP
    # ============================================================

    if (
        "duplicate ip" in output
        or "duplicate address" in output
        or "ip conflict" in output
    ):
        findings.append(
            "❌ Duplicate IP address conflict detected."
        )

    # ============================================================
    # 5. WRONG SUBNET MASK
    # ============================================================

    if (
        "wrong subnet mask" in output
        or "incorrect mask" in output
        or "mask mismatch" in output
        or "incorrect subnet" in output
    ):
        findings.append(
            "❌ Incorrect subnet mask detected."
        )

    # ============================================================
    # 6. GATEWAY MISMATCH
    # ============================================================

    if (
        "gateway mismatch" in output
        or "wrong gateway" in output
    ):
        findings.append(
            "❌ Gateway mismatch: Default gateway is incorrect."
        )

    # ============================================================
    # 7. PARSED IP / SUBNET MASK / GATEWAY CONSISTENCY CHECK
    # ============================================================

    ip_match = re.search(
        r"(?:ip address|ip-address|ip):\s*(\d+\.\d+\.\d+\.\d+)",
        output
    )

    mask_match = re.search(
        r"(?:subnet mask|subnet-mask|mask):\s*(\d+\.\d+\.\d+\.\d+)",
        output
    )

    gateway_match = re.search(
        r"(?:gateway|default gateway|default-gateway):\s*(\d+\.\d+\.\d+\.\d+)",
        output
    )

    if ip_match and mask_match and gateway_match:

        ip_address = ip_match.group(1)
        subnet_mask = mask_match.group(1)
        gateway = gateway_match.group(1)

        try:
            network = ipaddress.IPv4Network(
                f"{ip_address}/{subnet_mask}",
                strict=False
            )
            gateway_ip = ipaddress.IPv4Address(gateway)

            if gateway_ip not in network:
                findings.append(
                    f"❌ Gateway mismatch: Gateway {gateway} is outside the host's subnet {network}."
                )

        except ValueError:
            findings.append(
                "❌ Invalid IP address or subnet mask format detected."
            )

    # ============================================================
    # DEDUPLICATE FINDINGS
    # ============================================================

    unique_findings = []
    for finding in findings:
        if finding not in unique_findings:
            unique_findings.append(finding)

    # ============================================================
    # DEFAULT IF NO ISSUES FOUND
    # ============================================================

    if not unique_findings:
        unique_findings.append(
            "✅ No configuration errors detected by Python rules."
        )

    return unique_findings


if __name__ == "__main__":
    import os
    import sys
    import csv

    # Ensure UTF-8 output on Windows consoles
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("=" * 65)
    print("NetSage Static Rule Checker - Self-Test Suite")
    print("=" * 65)

    cases_file = os.path.join(os.path.dirname(__file__), "cases.csv")
    if os.path.exists(cases_file):
        with open(cases_file, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"Loaded {len(reader)} incident cases from cases.csv:\n")
            for row in reader:
                cid = row.get("case_id", "N/A")
                sym = row.get("symptom", "N/A")
                show_out = row.get("show_output", "")
                results = check_rules(show_out)
                print(f"[{cid}] {sym}")
                for res in results:
                    print(f"   {res}")
                print()
    else:
        sample = "GigabitEthernet0/0/0 192.168.1.1 YES manual administratively down down"
        print("Sample test:")
        for res in check_rules(sample):
            print(f"   {res}")


if __name__ == "__main__":
    import os
    import sys
    import csv

    # Ensure UTF-8 output on Windows consoles
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("=" * 65)
    print("NetSage Static Rule Checker - Self-Test Suite")
    print("=" * 65)

    cases_file = os.path.join(os.path.dirname(__file__), "cases.csv")
    if os.path.exists(cases_file):
        with open(cases_file, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            print(f"Loaded {len(reader)} incident cases from cases.csv:\n")
            for row in reader:
                cid = row.get("case_id", "N/A")
                sym = row.get("symptom", "N/A")
                show_out = row.get("show_output", "")
                results = check_rules(show_out)
                print(f"[{cid}] {sym}")
                for res in results:
                    print(f"   {res}")
                print()
    else:
        sample = "GigabitEthernet0/0/0 192.168.1.1 YES manual administratively down down"
        print("Sample test:")
        for res in check_rules(sample):
            print(f"   {res}")
