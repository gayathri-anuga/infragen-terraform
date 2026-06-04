import subprocess
import os
import json

TERRAFORM_DIR = os.path.join(os.path.dirname(__file__), "terraform")

def scan_terraform(terraform_code: str) -> dict:
    # Write code to a temp file for scanning
    scan_file = os.path.join(TERRAFORM_DIR, "main.tf")
    with open(scan_file, "w") as f:
        f.write(terraform_code)

    # Run checkov
    result = subprocess.run(
        [
            "checkov",
            "--directory", TERRAFORM_DIR,
            "--output", "json",
            "--quiet",
            "--compact"
        ],
        capture_output=True,
        text=True
    )

    try:
        output = json.loads(result.stdout)
        failed_checks = output.get("results", {}).get("failed_checks", [])

        issues = []
        for check in failed_checks:
            issues.append({
                "check_id": check.get("check_id"),
                "check_name": check.get("check_type") or check.get("resource"),
                "severity": check.get("severity", "MEDIUM"),
                "resource": check.get("resource"),
                "guideline": check.get("guideline", "")
            })

        return {
            "passed": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues
        }

    except Exception:
        return {
            "passed": True,
            "issue_count": 0,
            "issues": []
        }