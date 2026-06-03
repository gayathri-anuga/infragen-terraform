markdown# infragen-terraform

AI-powered agent that converts natural language to Terraform — generates, deploys, and self-heals GCP infrastructure automatically.

## What it does

Type plain English. Get real GCP infrastructure.
"Create a GCS bucket called my-bucket in us-central1"
↓
Terraform generated → init → plan → apply
↓
Real GCS bucket created in GCP

If Terraform fails, the agent automatically sends the error back to the LLM, fixes the code, and retries — no human intervention needed.

## Features

- Natural language to Terraform HCL generation
- Self-healing agent — auto-fixes errors and retries up to 3 times
- Supports GCS buckets, Cloud Run, VPC, Pub/Sub and more
- Conversational interface — asks for missing info before deploying
- Natural language destroy — delete resources by description
- FastAPI backend with Swagger UI for testing

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (Llama 3.3 70B) |
| Backend | FastAPI |
| IaC | Terraform + GCP Provider |
| Cloud | Google Cloud Platform |
| Language | Python 3.12 |

## Architecture
User Prompt
↓
FastAPI (/chat endpoint)
↓
Intent Detection (create or destroy?)
↓
Validation (all required info present?)
↓
Groq LLM generates Terraform HCL
↓
terraform init → plan → apply
↓
Success → GCP Resource Created
↓
Error → LLM fixes code → retry (max 3 attempts)

## Supported Resources

- Google Cloud Storage Buckets
- Cloud Run Services
- VPC Networks
- Pub/Sub Topics

## Prerequisites

- Python 3.12+
- Terraform
- GCP account with gcloud CLI authenticated
- Groq API key (free at console.groq.com)

## Setup

```bash
# Clone the repo
git clone https://github.com/gayathri-anuga/infragen-terraform.git
cd infragen-terraform

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GROQ_API_KEY="your-groq-api-key"

# Authenticate with GCP
gcloud auth application-default login

# Run the app
uvicorn main:app --reload
```

## Usage

Open `http://localhost:8000/docs`

**Create a resource:**
```json
{
  "message": "Create a GCS bucket called my-bucket in us-central1",
  "project_id": "your-gcp-project-id",
  "context": ""
}
```

**Delete a resource:**
```json
{
  "message": "delete my-bucket",
  "project_id": "your-gcp-project-id",
  "context": ""
}
```

## Project Structure
infragen-terraform/
├── main.py              # FastAPI backend and agent loop
├── generator.py         # Groq LLM integration
├── terraform_runner.py  # Terraform execution engine
├── requirements.txt     # Python dependencies
└── terraform/
└── main.tf          # Auto-generated Terraform code
