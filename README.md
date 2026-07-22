# 💼 AI LinkedIn Profile Builder

Generate a professional, recruiter-ready LinkedIn profile from your real college
information using AI. Built with **Python + Streamlit + OpenAI**, containerized
with **Docker**, and deployed to **Google Cloud Run** via **GitHub Actions**.

> 🛡️ **Honesty guarantee:** the AI only rewrites and polishes what *you* enter.
> It never invents fake companies, internships, certifications or achievements.

---

## 📌 Project Overview

Students often struggle to translate their coursework, projects and skills into a
polished LinkedIn presence. This app takes structured inputs (skills, projects,
internships, etc.) and generates ten professional sections:

- Professional Headline
- About Section
- Skills
- Professional Project Descriptions
- Internship Description
- Certifications
- Career Objective
- Resume Bullet Points
- Career Recommendations
- LinkedIn Banner Tagline

It is intentionally simple to read and modify — ideal for learning modern AI +
cloud deployment practices.

---

## 🏗️ Architecture

```
          User
            |
            v
   GitHub Repository
            |
            v
     GitHub Actions
            |
            v
      Docker Build
            |
            v
   Artifact Registry
            |
            v
      Cloud Run  <---- OPENAI_API_KEY (secret)
            |
            v
      OpenAI API
            |
            v
        Browser
```

At runtime the Streamlit app (on Cloud Run) collects inputs, calls the OpenAI
API, parses the Markdown response into sections, and renders them in the browser.

---

## ✨ Features

- Modern Streamlit UI with a hero banner, sidebar, cards and footer.
- Responsive two-column form layout.
- Loading spinner + progress indicator during generation.
- Expandable containers with copy-ready code blocks per section.
- Input validation (name, career goal and skills are required).
- Graceful OpenAI error handling with friendly messages.
- Model selector (`gpt-4o-mini` / `gpt-4o`).
- Production-ready Dockerfile (non-root user, port 8080).
- Automated CI/CD to Cloud Run with Workload Identity Federation.

---

## 🧰 Tech Stack

Python 3.11 · Streamlit · OpenAI Python SDK · python-dotenv · Docker ·
GitHub · GitHub Actions · Google Cloud (Artifact Registry, Cloud Run).

---

## 📥 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/linkedin-profile-builder.git
cd linkedin-profile-builder

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env      # then edit .env and add your OPENAI_API_KEY
```

---

## ▶️ Running Locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

---

## 🐳 Docker Build

```bash
# Build the image
docker build -t linkedin-profile-builder .

# Run the container (maps host 8080 -> container 8080)
docker run -p 8080:8080 -e OPENAI_API_KEY=sk-your-key linkedin-profile-builder
```

Then open http://localhost:8080.

---

## ⚙️ GitHub Actions Pipeline

The workflow at `.github/workflows/deploy.yml` runs on every push to `main` and:

1. Checks out the repository.
2. Sets up Python 3.11 and compiles the sources as a sanity check.
3. Authenticates to Google Cloud (Workload Identity Federation).
4. Configures Docker for Artifact Registry.
5. Builds the Docker image.
6. Pushes the image to Artifact Registry.
7. Deploys to Cloud Run.
8. Prints the public deployment URL in the job summary.

---

## 🔐 GitHub Secrets

Add these under **Settings → Secrets and variables → Actions**:

| Secret | Description | Example |
| --- | --- | --- |
| `GCP_PROJECT_ID` | Your Google Cloud project id | `my-gcp-project` |
| `GCP_REGION` | Deployment region | `us-central1` |
| `ARTIFACT_REGISTRY` | Artifact Registry repo name | `linkedin-builder` |
| `CLOUD_RUN_SERVICE` | Cloud Run service name | `linkedin-profile-builder` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `WORKLOAD_IDENTITY_PROVIDER` | WIF provider resource name | `projects/123.../providers/github` |
| `SERVICE_ACCOUNT_EMAIL` | Deploy service account email | `deployer@my-gcp-project.iam.gserviceaccount.com` |

**Alternative (Service Account Key JSON):** if you cannot use Workload Identity
Federation, create a service account key and store the entire JSON in a secret
named `GCP_SA_KEY`. Then in `deploy.yml`, comment out the
`workload_identity_provider` / `service_account` lines and uncomment the
`credentials_json: ${{ secrets.GCP_SA_KEY }}` line. WIF is preferred because it
avoids long-lived keys.

---

## ☁️ Cloud Run Deployment (one-time GCP setup)

```bash
# Variables
export PROJECT_ID=my-gcp-project
export REGION=us-central1
export REPO=linkedin-builder
export SERVICE=linkedin-profile-builder

# 1. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  --project "$PROJECT_ID"

# 2. Create an Artifact Registry Docker repository
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker \
  --location="$REGION" \
  --project "$PROJECT_ID"

# 3. Create a deploy service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer" --project "$PROJECT_ID"

export SA_EMAIL="github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# 4. Grant the roles needed to push images and deploy
for ROLE in roles/run.admin roles/artifactregistry.writer roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$ROLE"
done
```

### Workload Identity Federation (keyless auth)

```bash
# 1. Create a workload identity pool
gcloud iam workload-identity-pools create github-pool \
  --location=global --display-name="GitHub Pool" --project "$PROJECT_ID"

# 2. Create an OIDC provider for GitHub
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --project "$PROJECT_ID"

# 3. Allow your repo to impersonate the service account
export POOL_ID=$(gcloud iam workload-identity-pools describe github-pool \
  --location=global --project "$PROJECT_ID" --format='value(name)')

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/<your-username>/linkedin-profile-builder" \
  --project "$PROJECT_ID"

# 4. The WORKLOAD_IDENTITY_PROVIDER secret value:
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global --workload-identity-pool=github-pool \
  --project "$PROJECT_ID" --format='value(name)'
```

Put the resource name printed in step 4 into the `WORKLOAD_IDENTITY_PROVIDER`
secret, and `$SA_EMAIL` into `SERVICE_ACCOUNT_EMAIL`.

Once the secrets are set, **push to `main`** and GitHub Actions will build and
deploy automatically.

---

## 📁 Folder Structure

```
linkedin-profile-builder/
├── app.py                     # Streamlit UI
├── prompts.py                 # OpenAI prompt templates
├── utils.py                   # OpenAI client + response parsing
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Production container image
├── .dockerignore              # Files excluded from the image
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── assets/                    # Screenshots / images
└── .github/
    └── workflows/
        └── deploy.yml         # CI/CD pipeline
```

---

## 🖼️ Screenshots

_Add screenshots to `assets/` and reference them here:_

| Input form | Generated profile |
| --- | --- |
| ![Home](assets/screenshot-home.png) | ![Result](assets/screenshot-result.png) |

---

## 🚀 Future Enhancements

- PDF / DOCX export of the generated profile.
- One-click "copy all" and shareable links.
- Multi-language profile generation.
- Optional profile photo and banner image generation.
- Rate limiting and per-user usage analytics.
- Unit tests + linting in CI (pytest, ruff, mypy).

---

## 📝 License

Released for educational use. Add a `LICENSE` file (e.g. MIT) if you plan to
distribute it.

---

Made with ❤️ using Python, Streamlit and Google Cloud.
