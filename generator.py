from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY"])

def generate_terraform(prompt: str, project_id: str) -> str:
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
    system_prompt = """
You are a Terraform expert for GCP.
Generate ONLY the resource block in valid Terraform HCL.
Do not include provider, terraform, or required_providers blocks.
Do not include any explanation, markdown backticks, or code fences.
Just the resource block only.
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


def extract_or_ask(prompt: str) -> dict:
    system_prompt = """
You are an AI assistant that helps users create GCP infrastructure.
Analyze the user's request and check if all required information is present.

For Cloud Run you need: service name, container image, region
For GCS Bucket you need: bucket name, region
For VPC you need: network name
For Pub/Sub you need: topic name

Respond ONLY in this JSON format, nothing else:
{
  "ready": true or false,
  "missing": ["list of missing fields"],
  "questions": "friendly message asking for missing info",
  "resource_type": "detected resource type"
}

If all required info is present set ready to true and missing to empty list.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    import json
    content = response.choices[0].message.content.strip()
    return json.loads(content)