from fastapi import FastAPI
from pydantic import BaseModel
from generator import generate_terraform, fix_terraform, extract_or_ask, detect_intent
from terraform_runner import run_terraform, destroy_resource, list_resources
from logger import log_action, get_history
from security_scanner import scan_terraform
from generator import generate_terraform, fix_terraform, extract_or_ask, detect_intent, fix_security_issues
app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    project_id: str

class ChatRequest(BaseModel):
    message: str
    project_id: str
    context: str = ""

@app.post("/chat")
def chat(request: ChatRequest):
    state = list_resources()
    intent = detect_intent(request.message, state)

    if intent["intent"] == "destroy":
        if not intent["resource_name"]:
            return {
                "status": "needs_info",
                "message": "Which resource do you want to delete? Current resources:\n" + state
            }
        result = destroy_resource(intent["resource_name"])
        
        log_action(
            action="destroy",
            resource_type=intent["resource_name"].split(".")[0],
            resource_name=intent["resource_name"].split(".")[1] if "." in intent["resource_name"] else intent["resource_name"],
            status="success" if result["success"] else "failed",
            error="" if result["success"] else result["output"]
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "message": f"Resource {intent['resource_name']} deleted successfully!" if result["success"] else "Failed to delete resource",
            "output": result["output"]
        }

    full_prompt = f"{request.context}\nUser: {request.message}".strip()
    validation = extract_or_ask(full_prompt)

    if not validation["ready"]:
        return {
            "status": "needs_info",
            "message": validation["questions"],
            "missing": validation["missing"],
            "context": full_prompt
        }

    terraform_code = generate_terraform(full_prompt, request.project_id)

     # Security scan before applying
    scan_result = scan_terraform(terraform_code)
    if not scan_result["passed"]:
        # Auto-fix security issues
        terraform_code = fix_security_issues(terraform_code, scan_result["issues"])


    max_retries = 5
    for attempt in range(max_retries):
        results = run_terraform(terraform_code)

        if results["success"]:
            log_action(
                action="create",
                resource_type=validation.get("resource_type", "unknown"),
                resource_name=request.message,
                status="success",
                attempts=attempt + 1,
                terraform_code=terraform_code
            )
            return {
                "status": "success",
                "attempts": attempt + 1,
                "message": "Resource created successfully!",
                "terraform_code": terraform_code,
                "output": results["apply"]
            }

        error = results["error"]
        terraform_code = fix_terraform(terraform_code, error)

    log_action(
        action="create",
        resource_type=validation.get("resource_type", "unknown"),
        resource_name=request.message,
        status="failed",
        attempts=max_retries,
        error=results["error"]
    )

    return {
        "status": "failed",
        "attempts": max_retries,
        "message": "Failed to create resource after 3 attempts",
        "output": results["error"]
    }

@app.get("/resources")
def resources():
    state = list_resources()
    if not state:
        return {"resources": [], "message": "No resources currently managed"}
    return {
        "resources": state.split("\n"),
        "count": len(state.split("\n"))
    }

@app.get("/history")
def history():
    logs = get_history()
    return {
        "total": len(logs),
        "history": logs
    }

@app.get("/")
def root():
    return {"message": "Infragen API is running"}