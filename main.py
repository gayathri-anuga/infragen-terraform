from fastapi import FastAPI
from pydantic import BaseModel
from generator import generate_terraform, fix_terraform, extract_or_ask
from terraform_runner import run_terraform

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str
    project_id: str

class ChatRequest(BaseModel):
    message: str
    project_id: str
    context: str = ""  # stores previous conversation

@app.post("/chat")
def chat(request: ChatRequest):
    # Combine context + new message
    full_prompt = f"{request.context}\nUser: {request.message}".strip()
    
    # Check if we have enough info
    validation = extract_or_ask(full_prompt)
    
    if not validation["ready"]:
        # Not enough info - ask for missing fields
        return {
            "status": "needs_info",
            "message": validation["questions"],
            "missing": validation["missing"],
            "context": full_prompt
        }
    
    # Have all info - generate and deploy
    terraform_code = generate_terraform(full_prompt, request.project_id)
    
    max_retries = 3
    for attempt in range(max_retries):
        results = run_terraform(terraform_code)
        
        if results["success"]:
            return {
                "status": "success",
                "attempts": attempt + 1,
                "message": "Resource created successfully!",
                "terraform_code": terraform_code,
                "output": results["apply"]
            }
        
        error = results["error"]
        terraform_code = fix_terraform(terraform_code, error)
    
    return {
        "status": "failed",
        "attempts": max_retries,
        "message": "Failed to create resource after 3 attempts",
        "output": results["error"]
    }

@app.post("/generate")
def generate(request: PromptRequest):
    terraform_code = generate_terraform(request.prompt, request.project_id)
    
    max_retries = 3
    for attempt in range(max_retries):
        results = run_terraform(terraform_code)
        
        if results["success"]:
            return {
                "status": "success",
                "attempts": attempt + 1,
                "terraform_code": terraform_code,
                "output": results["apply"]
            }
        
        error = results["error"]
        terraform_code = fix_terraform(terraform_code, error)
    
    return {
        "status": "failed",
        "attempts": max_retries,
        "terraform_code": terraform_code,
        "output": results["error"]
    }

@app.get("/")
def root():
    return {"message": "Infragen API is running"}