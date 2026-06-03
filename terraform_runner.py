import subprocess
import os

TERRAFORM_DIR = os.path.join(os.path.dirname(__file__), "terraform")

def run_terraform(terraform_code: str) -> dict:
    main_tf_path = os.path.join(TERRAFORM_DIR, "main.tf")
    with open(main_tf_path, "w") as f:
        f.write(terraform_code)

    init = subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
    if init.returncode != 0:
        return {
            "init": init.stdout + init.stderr,
            "plan": "", "apply": "",
            "error": init.stdout + init.stderr,
            "success": False
        }

    plan = subprocess.run(["terraform", "plan"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
    if plan.returncode != 0:
        return {
            "init": init.stdout + init.stderr,
            "plan": plan.stdout + plan.stderr,
            "apply": "", 
            "error": plan.stdout + plan.stderr,
            "success": False
        }

    apply = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=TERRAFORM_DIR, capture_output=True, text=True)
    if apply.returncode != 0:
        return {
            "init": init.stdout + init.stderr,
            "plan": plan.stdout + plan.stderr,
            "apply": apply.stdout + apply.stderr,
            "error": apply.stdout + apply.stderr,
            "success": False
        }

    return {
        "init": init.stdout + init.stderr,
        "plan": plan.stdout + plan.stderr,
        "apply": apply.stdout + apply.stderr,
        "error": None,
        "success": True
    }