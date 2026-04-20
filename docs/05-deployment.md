# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- 3GPP spec ZIP files

### Setup

```bash
git clone https://github.com/sohelimi/3gppspec.git
cd 3gppspec
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

### Run Ingestion (one-time)

```bash
python scripts/ingest.py --releases Rel-18 --series 38_series,23_series,33_series
```

### Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### Start Frontend

```bash
cd frontend && npm install && npm run dev
# UI: http://localhost:3000
```

---

## Docker

```bash
cp .env.example .env  # add GROQ_API_KEY
docker-compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

---

## GCP Cloud Run

### Step 1 — Create Project & Enable APIs

```bash
gcloud projects create YOUR_PROJECT_ID --name="3gppSpec"
gcloud config set project YOUR_PROJECT_ID
gcloud billing projects link YOUR_PROJECT_ID --billing-account=YOUR_BILLING_ID

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

### Step 2 — Store API Key in Secret Manager

```bash
echo -n "YOUR_GROQ_API_KEY" | gcloud secrets create groq-api-key --data-file=-
```

### Step 3 — Run Ingestion Locally

```bash
python scripts/ingest.py
# This builds ./data/chromadb/ which gets bundled into the Docker image
```

### Step 4 — Build & Push Docker Image

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev

docker build \
  -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/3gppspec/3gppspec:latest \
  .

docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/3gppspec/3gppspec:latest
```

### Step 5 — Deploy with Terraform

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit: set project_id = "YOUR_PROJECT_ID"
terraform init
terraform apply
```

### Step 6 — Map Custom Domain

After `terraform apply` outputs the Cloud Run URL, add a DNS record:

```
Type:  CNAME
Name:  3gpp
Value: ghs.googlehosted.com
```

SSL certificate provisions automatically within ~15 minutes.

**Live at: https://3gpp.deltatechus.com**

---

## CI/CD (GitHub Actions)

Every push to `main` triggers an automatic build and deploy.

### Required GitHub Secrets

| Secret | How to get it |
|---|---|
| `GCP_PROJECT_ID` | Your GCP project ID string |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | From GCP IAM → Workload Identity |
| `GCP_SERVICE_ACCOUNT` | `github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com` |

### Setup Workload Identity (keyless auth)

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Create Workload Identity Pool
gcloud iam workload-identity-pools create github \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key (free at console.groq.com) |
| `SPECS_DIR` | Ingestion only | Path to 3GPP spec ZIP files |
| `CHROMA_DB_PATH` | Yes | Path to ChromaDB folder (default: `./data/chromadb`) |
| `INGEST_RELEASES` | Ingestion only | Comma-separated releases (default: `Rel-17,Rel-18,Rel-19`) |
| `INGEST_SERIES` | Ingestion only | Comma-separated series (default: `23_series,24_series,33_series,38_series`) |
| `APP_ENV` | No | `development` or `production` |
| `ALLOWED_ORIGINS` | Yes | CORS origins (comma-separated) |
