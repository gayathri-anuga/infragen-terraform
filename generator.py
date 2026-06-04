from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY"])


import subprocess

def get_project_number(project_id: str) -> str:
    result = subprocess.run(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def generate_terraform(prompt: str, project_id: str) -> str:
    project_number = get_project_number(project_id)
    
    provider_block = f"""
terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  project = "{project_id}"
  region  = "us-central1"
}}
"""

    system_prompt = f"""
You are a Terraform expert for GCP.
Generate ONLY the resource block in valid Terraform HCL.
Do not include provider, terraform, or required_providers blocks.
Do not include any explanation, markdown backticks, or code fences.
Just the resource block only.

Important GCP project details:
- Project ID: {project_id}
- Project Number: {project_number}
- GCS service account: service-{project_number}@gs-project-accounts.iam.gserviceaccount.com
- Compute service account: {project_number}-compute@developer.gserviceaccount.com

When creating KMS resources always use the correct project number in service account references.
When creating KMS key rings always use location us-central1.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    resource_block = response.choices[0].message.content.strip()
    return provider_block + "\n" + resource_block

def fix_terraform(terraform_code: str, error: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are a Terraform expert for GCP.
Fix the Terraform code based on the error provided.
Return ONLY the fixed HCL code, no explanations, no markdown backticks."""},
            {"role": "user", "content": f"Terraform code:\n{terraform_code}\n\nError:\n{error}\n\nFix the code."}
        ]
    )
    return response.choices[0].message.content.strip()

def fix_security_issues(terraform_code: str, issues: list) -> str:
    issues_text = "\n".join([f"- {i['check_id']}: {i['check_name']} on {i['resource']}" for i in issues])
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are a Terraform security expert for GCP.
Fix the security issues in the Terraform code.
Return ONLY the fixed HCL code, no explanations, no markdown backticks.
For IAM bindings use correct GCP service account formats."""},
            {"role": "user", "content": f"Terraform code:\n{terraform_code}\n\nSecurity issues to fix:\n{issues_text}\n\nFix all security issues without adding unnecessary complexity."}
        ]
    )
    return response.choices[0].message.content.strip()
def extract_or_ask(prompt: str) -> dict:
    import json
    import re
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are an intelligent GCP infrastructure agent.
Analyze the user's request and extract what they want to create.

Required fields per resource type:
- GCS Bucket: name, region
- Cloud Run: service name, container image, region
- VPC Network: network name, region
- Pub/Sub Topic: topic name
- Cloud SQL: instance name, database version, region, tier

Rules:
- Understand natural language — user may say "make a bucket", "spin up cloud run", "need a vpc" etc.
- Extract any values the user already mentioned
- For any required field not mentioned by the user, ask for it
- Never assume or guess values — always ask if unsure
- Be conversational and friendly when asking

You MUST respond with valid JSON only. No extra text before or after.
Use double quotes for all strings. No trailing commas.

{
  "ready": true,
  "resource_type": "GCS Bucket",
  "extracted": {"name": "my-bucket", "region": "us-central1"},
  "missing": [],
  "questions": ""
}"""},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    
    # Remove markdown code fences if present
    content = re.sub(r'```json|```', '', content).strip()
    
    # Find the outermost JSON object
    try:
        # Try direct parse first
        return json.loads(content)
    except Exception:
        pass
    
    # Try extracting JSON with nested objects
    try:
        start = content.index('{')
        depth = 0
        for i, char in enumerate(content[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return json.loads(content[start:i+1])
    except Exception:
        pass
    
    # Safe fallback
    return {
        "ready": False,
        "missing": [],
        "questions": "Could you clarify what GCP resource you want to create and its name?",
        "resource_type": "unknown",
        "extracted": {}
    }
def detect_intent(message: str, state_list: str) -> dict:
    import json
    import re
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are an AI assistant for GCP infrastructure.
Detect if the user wants to CREATE or DESTROY a resource.
Currently managed resources in Terraform state:

""" + state_list + """

Respond ONLY in this JSON format, nothing else, no extra text:
{
  "intent": "create" or "destroy",
  "resource_name": "exact resource name from state list if destroying, empty string if creating"
}"""},
            {"role": "user", "content": message}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON even if LLM adds extra text
    json_match = re.search(r'\{.*?\}', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    
    # Default to create if parsing fails
    return {"intent": "create", "resource_name": ""}