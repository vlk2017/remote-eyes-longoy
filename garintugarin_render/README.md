# Garintugarin — Render Telegram bridge

Isolated deployment branch. Source and secrets are separate.

Render service (Python, Frankfurt, free): 
- Build: `pip install -r garintugarin_render/requirements.txt`
- Start: `cd garintugarin_render && gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app:application`
- Health: `/health`

Required secret: `TELEGRAM_BOT_TOKEN`. Optional: `TELEGRAM_OWNER_ID` (until configured, only /whoami works). `RENDER_EXTERNAL_URL` is provided by Render.

At process startup, the webhook is registered with Telegram. No Android runtime exists on this server; scans intentionally cannot run, and no messaging to prospects is enabled.
