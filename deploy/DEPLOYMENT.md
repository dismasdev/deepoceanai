# Brainstorm AI Deployment (DigitalOcean + Gradient)

This project deploys cleanly as three pieces:

1. Gradient Agent deployment (ADK entrypoint)
2. Backend API service (FastAPI)
3. Frontend web service (Next.js LiveKit starter)

## 1) Tokens You Need

### A) DigitalOcean API Token (for Gradient CLI)

Use this token to run `gradient agent configure/deploy`.

1. Open DigitalOcean Control Panel.
2. Go to API -> Tokens/Keys -> Generate New Token.
3. Give it GenAI/Agent Platform permissions (read + write) and project read access.
4. Export it locally:

```bash
export DIGITALOCEAN_API_TOKEN="YOUR_DO_API_TOKEN"
```

### Quick automation scripts

After setting `DIGITALOCEAN_API_TOKEN`, you can run:

```bash
./deploy/deploy-gradient-agent.sh
./deploy/deploy-all.sh
./deploy/invoke-gradient-agent.sh "hello"
```

The first deploys the ADK agent.
The second deploys backend and frontend App Platform services from spec files.
The third invokes the deployed Gradient endpoint using `DIGITALOCEAN_API_TOKEN` from `.env`.

### B) Gradient Model Access Key (optional)

Only needed if you enable real model calls from backend code (`ENABLE_GRADIENT_AGENT=true`).

1. In Gradient/GenAI console, create a Model Access Key.
2. Add it to backend env var `GRADIENT_MODEL_ACCESS_KEY`.

## 2) Deploy Gradient Agent (ADK)

Entrypoint already exists at `backend/adk_entrypoint.py`.

```bash
cd /home/dismasdev/hackathon/deepoceanai
uv sync
uv run gradient --version
uv run gradient agent configure
uv run gradient agent run --verbose
uv run gradient agent deploy
```

When prompted during `configure`, choose:
- Agent name: `brainstorm-ai`
- Deployment name: `production` (or `staging`)
- Entrypoint file: `backend/adk_entrypoint.py`

## 3) Deploy Backend API (App Platform)

Use spec file:
- `deploy/do-backend-app.yaml`

In the spec:
- Replace `YOUR_GITHUB_ORG/YOUR_REPO`
- Set secrets (`GRADIENT_MODEL_ACCESS_KEY` if needed)

Deploy from CLI:

```bash
doctl apps create --spec deploy/do-backend-app.yaml
```

After deploy, note backend URL, for example:
- `https://brainstorm-ai-backend-xxxxx.ondigitalocean.app`

## 4) Deploy Frontend (App Platform)

Use spec file:
- `deploy/do-frontend-app.yaml`

In the spec:
- Replace `YOUR_GITHUB_ORG/YOUR_REPO`
- Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- Replace `NEXT_PUBLIC_BACKEND_API_BASE` with your backend URL
- Replace `NEXT_PUBLIC_APP_CONFIG_ENDPOINT` with `<backend-url>/app-config`

Deploy:

```bash
doctl apps create --spec deploy/do-frontend-app.yaml
```

## 5) Runtime Checks

Backend checks:

```bash
curl https://YOUR_BACKEND_DOMAIN/health
curl -H "X-Sandbox-ID: opencolabo-ai-1ogbuq" https://YOUR_BACKEND_DOMAIN/app-config
```

Frontend checks:
- Open deployed frontend URL
- Start a call
- Speak (voice-only mode)
- Confirm transcript + backend response + backend audio playback

## Notes

- Frontend is pinned to sandbox ID `opencolabo-ai-1ogbuq` via env and token route validation.
- Rotate LiveKit API credentials if previously exposed.
