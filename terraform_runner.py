import subprocess
import os
import re

TERRAFORM_BASE_DIR = os.path.join(os.path.dirname(__file__), "terraform_workspaces")

def get_workspace_for_resource(resource_name: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resource_name)
    workspace_dir = os.path.join(TERRAFORM_BASE_DIR, safe_name)
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir

def extract_resource_name(terraform_code: str) -> str:
    match = re.search(r'resource\s+"[^"]+"\s+"([^"]+)"', terraform_code)
    return match.group(1) if match else "default"

def run_terraform(terraform_code: str) -> dict:
    resource_name = extract_resource_name(terraform_code)
    workspace = get_workspace_for_resource(resource_name)
    
    with open(os.path.join(workspace, "main.tf"), "w") as f:
        f.write(terraform_code)

    init = subprocess.run(["terraform", "init"], cwd=workspace, capture_output=True, text=True)
    if init.returncode != 0:
        return {"init": init.stdout + init.stderr, "plan": "", "apply": "", "error": init.stdout + init.stderr, "success": False}

    plan = subprocess.run(["terraform", "plan"], cwd=workspace, capture_output=True, text=True)
    if plan.returncode != 0:
        return {"init": init.stdout + init.stderr, "plan": plan.stdout + plan.stderr, "apply": "", "error": plan.stdout + plan.stderr, "success": False}

    apply = subprocess.run(["terraform", "apply", "-auto-approve"], cwd=workspace, capture_output=True, text=True)
    if apply.returncode != 0:
        return {"init": init.stdout + init.stderr, "plan": plan.stdout + plan.stderr, "apply": apply.stdout + apply.stderr, "error": apply.stdout + apply.stderr, "success": False}

    return {"init": init.stdout + init.stderr, "plan": plan.stdout + plan.stderr, "apply": apply.stdout + apply.stderr, "error": None, "success": True}

def list_resources() -> str:
    if not os.path.exists(TERRAFORM_BASE_DIR):
        return ""
    
    all_resources = []
    for workspace in os.listdir(TERRAFORM_BASE_DIR):
        workspace_dir = os.path.join(TERRAFORM_BASE_DIR, workspace)
        if os.path.isdir(workspace_dir):
            result = subprocess.run(
                ["terraform", "state", "list"],
                cwd=workspace_dir,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                all_resources.extend(result.stdout.strip().split("\n"))
    
    return "\n".join(all_resources)

def destroy_resource(resource_name: str) -> dict:
    if not os.path.exists(TERRAFORM_BASE_DIR):
        return {"output": "No workspaces found", "success": False}
    
    for workspace in os.listdir(TERRAFORM_BASE_DIR):
        workspace_dir = os.path.join(TERRAFORM_BASE_DIR, workspace)
        if os.path.isdir(workspace_dir):
            result = subprocess.run(
                ["terraform", "state", "list"],
                cwd=workspace_dir,
                capture_output=True,
                text=True
            )
            if resource_name in result.stdout:
                destroy = subprocess.run(
                    ["terraform", "destroy", "-auto-approve", f"-target={resource_name}"],
                    cwd=workspace_dir,
                    capture_output=True,
                    text=True
                )
                return {
                    "output": destroy.stdout + destroy.stderr,
                    "success": destroy.returncode == 0
                }
    
    return {"output": f"Resource {resource_name} not found", "success": False}