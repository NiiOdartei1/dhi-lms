Render deployment notes
=======================

1) Prepare repo

- Ensure `requirements.txt`, `Procfile`, and `runtime.txt` exist (they do).
- `app.py` exposes the Flask `app` object and now honors `Config` / `DATABASE_URL`.

2) Required environment variables (set these in Render dashboard or `render.yaml`):

- `SECRET_KEY` (strong random string)
- `DATABASE_URL` (Postgres URL; Render provides managed DB or use external)
- `MAIL_USERNAME`, `MAIL_PASSWORD` (for Flask-Mailman / Gmail)
- `FLASK_ENV` = `production`

3) Start command

- The `Procfile` uses: `web: gunicorn --worker-class eventlet -w 1 app:app`

4) Quick local test (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_ENV="development"
set "PORT=5000"
python app.py
```

5) Deploy

- Push to your Git repo and connect the repository in Render.
- Configure environment variables in the Render service settings.
- Trigger a deploy; watch the build logs for dependency installation and the start step.

6) Notes

- If using Render Postgres, use the provided `DATABASE_URL` and keep the `postgres://` → `postgresql://` replacement in `config.py`.
- Keep `eventlet` and `gunicorn` in `requirements.txt` (already present).
