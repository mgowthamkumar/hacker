Deploying FastAPI `backendreal.py` to Vercel as `autohire`

1) Pre-reqs
- Install Vercel CLI: `npm i -g vercel`
- Have a Vercel account and be logged in: `vercel login`

2) What I added
- `Dockerfile` - builds a container with the FastAPI app and runs `uvicorn backendreal:app`.
- `vercel.json` - instructs Vercel to build the project using the Dockerfile (keeps existing rewrites).

3) Deploy steps
Run in the project root:

```bash
# Login to Vercel if needed
vercel login

# Create/deploy as a new project named autohire (production)
vercel --prod --name autohire
```

If you already have a Vercel project and just want to update its name, use the Vercel dashboard or the CLI when linking:

```bash
vercel link --name autohire
vercel --prod
```

4) Environment variables
- The container listens on port `5501`. The Dockerfile exposes `5501`.
- By default the containerized app binds to `127.0.0.1` (localhost) to match local development environments. This avoids exposing the server unintentionally when running locally.
- To allow external access from the container (required for many cloud/container platforms), set `HOST=0.0.0.0` in your deployment environment.
- To override port, set `PORT` (default `5501`).

5) Notes
- This uses a container (Docker) build which may consume build minutes on Vercel depending on your plan.
- After deploy, your app will be available at `https://<your-project>.vercel.app` (or the custom domain you choose).

6) Automated deploy via GitHub Actions (no manual CLI needed)

- I added a GitHub Actions workflow at `.github/workflows/deploy-autohire.yml` that runs on push to `main`/`master` and calls Vercel to deploy the project as `autohire`.
- Required repository secrets (set these in GitHub > Settings > Secrets):
	- `VERCEL_TOKEN` — a Personal Token from Vercel (Account Settings -> Tokens).
	- `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` — available from your Vercel project settings (or via the Vercel dashboard API).

Once those secrets are set, push to `main` and GitHub Actions will deploy automatically.
