# Hosting the Job Search Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the Streamlit web UI to a DigitalOcean $6/month Droplet so friends/colleagues can access it via browser, with all API keys hosted server-side.

**Architecture:** Docker Compose (already in repo) runs on a single Ubuntu 24.04 VM. A small code fix eliminates a concurrent-user output file conflict. nginx (optional) adds basic auth as a lightweight access gate.

**Tech Stack:** Docker Compose, DigitalOcean Droplet (Ubuntu 24.04), UFW firewall, nginx + htpasswd (optional)

---

## Context

The app already has a working Docker Compose stack (`db` + `app` + `web` services). The only blocker before deploying is a bug: `cli.py` writes results to a hardcoded `output/output.json`, so two simultaneous users overwrite each other. The fix takes ~30 minutes; the rest is infrastructure provisioning.

**Budget:** $6/month DigitalOcean Droplet (1 vCPU, 1 GB RAM). A free alternative — Oracle Cloud Always Free (4 OCPU, 24 GB RAM) — is noted at the end.

---

## Task 1: Write Failing Tests for Output File Fix

**Files:**
- Create: `tests/unit/test_output_file_arg.py`

- [ ] **Step 1: Create the test file**

```python
# tests/unit/test_output_file_arg.py
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cli import run_full


class TestOutputFileArg:

    def test_argparse_accepts_output_file(self, monkeypatch):
        monkeypatch.setattr(
            sys, "argv",
            ["cli.py", "full", "--cv", "/tmp/r.pdf", "--no-ui",
             "--output-file", "/tmp/custom.json"],
        )
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=None)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        with patch("cli.initialize", return_value=mock_ctx), \
             patch("cli.compose", return_value=MagicMock()), \
             patch("cli.asyncio.run"):
            from cli import main
            main()

    def test_run_full_uses_custom_output_path(self, tmp_path):
        custom_path = tmp_path / "session_xyz.json"
        mock_cfg = MagicMock()
        mock_cfg.database.host = "localhost"
        mock_cfg.database.port = "5432"
        mock_cfg.database.db = "job_search"
        mock_cfg.database.user = "user"
        mock_cfg.database.password = "pass"
        mock_cfg.anthropic_api_key = "key"
        mock_cfg.apify_api_token = "token"
        mock_cfg.vibe_api_key = "vibe"
        mock_cfg.vibe_api_base_url = "https://api.vibe.com"
        mock_cfg.scoring.max_contacts_per_category = 3
        mock_cfg.scoring.contact_score_threshold = 7.0
        mock_cfg.scoring.veteran_score_boost = 1.0
        mock_cfg.scoring.job_score_threshold = 7.0
        mock_cfg.scoring.top_n_jobs = 10
        mock_cfg.search.keywords = ["Python"]
        mock_cfg.search.location = "Denver, CO"
        mock_cfg.search.remote = True
        mock_cfg.search.onsite = False
        mock_cfg.search.job_type = "fulltime"
        mock_cfg.search.time_window_hours = 24
        mock_cfg.logging.level = "INFO"

        mock_ctx = MagicMock()
        mock_ctx.output = '{"job_table": {"rows": []}, "contact_table": {"rows": []}}'
        mock_ctx.errors = []
        mock_ctx.state = "complete"

        with patch("cli.create_pool", new_callable=AsyncMock) as mock_pool, \
             patch("cli.ensure_schema", new_callable=AsyncMock), \
             patch("cli.ClaudeClient"), \
             patch("cli.ApifyContactClient"), \
             patch("cli.VibeProspectingClient"), \
             patch("cli.ApifyClient"), \
             patch("cli.Orchestrator") as MockOrch, \
             patch("cli.configure_logging"):
            mock_pool.return_value.close = AsyncMock()
            mock_orch_instance = MagicMock()
            mock_orch_instance.run = AsyncMock(return_value=mock_ctx)
            MockOrch.return_value = mock_orch_instance

            import asyncio
            asyncio.run(
                run_full(mock_cfg, cv_path="/tmp/r.pdf", keywords=[],
                         output_file=str(custom_path))
            )

        assert custom_path.exists()
        data = json.loads(custom_path.read_text())
        assert "job_table" in data


class TestWebSessionIsolation:

    def test_run_pipeline_accepts_output_file_param(self):
        from web.app import _run_pipeline
        sig = inspect.signature(_run_pipeline)
        assert "output_file" in sig.parameters

    def test_run_pipeline_passes_output_file_to_subprocess(self, tmp_path):
        from web.app import _run_pipeline
        output_file = str(tmp_path / "output_abc123.json")
        with patch("web.app.subprocess.run") as mock_run, \
             patch("web.app.update_location"):
            mock_run.return_value = MagicMock(returncode=0)
            _run_pipeline(
                cv_path="/tmp/r.pdf",
                location="Denver, CO",
                keywords=[],
                output_file=output_file,
            )
        cmd = mock_run.call_args[0][0]
        assert "--output-file" in cmd
        assert output_file in cmd
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /home/smebellis/job_search_agent_take_2
python -m pytest tests/unit/test_output_file_arg.py -v
```

Expected: `FAILED` on all 4 tests (functions don't exist yet).

---

## Task 2: Fix `cli.py` — Add `--output-file` Argument

**Files:**
- Modify: `cli.py:32` (signature), `cli.py:91-95` (write block), `cli.py:99-106` (argparse), `cli.py:113` (asyncio.run call)

- [ ] **Step 3: Update `run_full` signature**

Change line 32:
```python
# BEFORE
async def run_full(cfg, cv_path: str, keywords: list[str]):

# AFTER
async def run_full(cfg, cv_path: str, keywords: list[str], output_file: str | None = None):
```

- [ ] **Step 4: Update the file write block**

Replace lines 91–95:
```python
        if ctx.output:
            if output_file:
                out_path = Path(output_file)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(ctx.output)
            else:
                out_dir = (
                    Path("/app/output") if Path("/app/output").exists() else Path("output")
                )
                out_dir.mkdir(exist_ok=True)
                (out_dir / "output.json").write_text(ctx.output)
```

- [ ] **Step 5: Add `--output-file` to argparse** (after the `--no-ui` argument)

```python
    parser.add_argument(
        "--output-file",
        default=None,
        help="Path to write JSON output (default: output/output.json)",
    )
```

- [ ] **Step 6: Pass `output_file` to `asyncio.run`**

Change line 113:
```python
# BEFORE
            asyncio.run(run_full(cfg, cv_path=args.cv, keywords=args.keywords))

# AFTER
            asyncio.run(run_full(cfg, cv_path=args.cv, keywords=args.keywords,
                                 output_file=args.output_file))
```

---

## Task 3: Fix `web/app.py` — Session-Scoped Output Paths

**Files:**
- Modify: `web/app.py`

- [ ] **Step 7: Add `uuid` import** (after line 4)

```python
import uuid
```

- [ ] **Step 8: Update `_run_pipeline` signature and cmd**

```python
# BEFORE
def _run_pipeline(cv_path: str, location: str, keywords: list[str]) -> int:
    update_location(location)
    cmd = [sys.executable, "cli.py", "full", "--cv", cv_path, "--no-ui"]

# AFTER
def _run_pipeline(cv_path: str, location: str, keywords: list[str], output_file: str) -> int:
    update_location(location)
    cmd = [sys.executable, "cli.py", "full", "--cv", cv_path, "--no-ui",
           "--output-file", output_file]
```

- [ ] **Step 9: Replace the button-click handler in `main()`**

Replace lines 94–136 (from `has_resume = ...` to end of function) with:
```python
    has_resume = "resume_bytes" in st.session_state
    if st.button("Find My Jobs", disabled=not has_resume):
        if "resume_bytes" not in st.session_state:
            st.warning("Please upload your resume again.")
            st.stop()

        if "session_id" not in st.session_state:
            st.session_state["session_id"] = uuid.uuid4().hex

        session_id = st.session_state["session_id"]
        out_dir = Path("/app/output") if Path("/app/output").exists() else Path("output")
        out_dir.mkdir(exist_ok=True)
        session_output_path = out_dir / f"output_{session_id}.json"

        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(st.session_state["resume_bytes"])
            cv_path = tmp.name

        try:
            with st.spinner("Searching for jobs… this takes 2–3 minutes"):
                returncode = _run_pipeline(cv_path, location, keywords,
                                           output_file=str(session_output_path))
        finally:
            Path(cv_path).unlink(missing_ok=True)

        if returncode != 0:
            st.error("Something went wrong. Check that your API keys are valid and try again.")
            return

        if not session_output_path.exists():
            st.warning("No results found. Try different keywords or a broader location.")
            return

        try:
            data = json.loads(session_output_path.read_text())
        except (json.JSONDecodeError, OSError):
            st.warning("No results found. Try different keywords or a broader location.")
            return
        finally:
            session_output_path.unlink(missing_ok=True)

        jobs = parse_jobs(data)
        contacts = parse_contacts(data)
        message_count = sum(1 for c in contacts if c.get("message"))

        with st.expander(f"Top Jobs ({len(jobs)})", expanded=True):
            _render_jobs(jobs)

        with st.expander(f"Contacts ({len(contacts)})", expanded=True):
            _render_contacts(contacts)

        with st.expander(f"Outreach Messages ({message_count})", expanded=True):
            _render_messages(contacts)
```

- [ ] **Step 10: Run all tests — confirm green**

```bash
python -m pytest tests/unit/test_output_file_arg.py -v
python -m pytest tests/unit/ -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add cli.py web/app.py tests/unit/test_output_file_arg.py
git commit -m "fix: session-scoped output files prevent concurrent user conflicts"
```

---

## Task 4: Add `restart: unless-stopped` to Docker Compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 12: Add restart policy to all three services**

Add `restart: unless-stopped` under each service in `docker-compose.yml`:
```yaml
services:
  db:
    restart: unless-stopped
    ...
  app:
    restart: unless-stopped
    ...
  web:
    restart: unless-stopped
    ...
```

- [ ] **Step 13: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add restart policy so stack recovers after VM reboot"
```

---

## Task 5: Provision DigitalOcean Droplet

*(Run these commands on your local machine and then SSH into the new VM)*

- [ ] **Step 14: Create the Droplet**

1. Go to cloud.digitalocean.com → Create → Droplets
2. Region: pick closest to you
3. Image: Ubuntu 24.04 LTS (x64)
4. Size: Basic, Regular SSD, **$6/month** (1 vCPU, 1 GB RAM, 25 GB SSD)
5. Authentication: SSH Key — paste contents of `~/.ssh/id_ed25519.pub` (generate with `ssh-keygen -t ed25519` if needed)
6. Hostname: `job-search-agent`
7. Click Create Droplet — note the IP address (used as `<DROPLET_IP>` below)

- [ ] **Step 15: First login and system prep**

```bash
ssh root@<DROPLET_IP>
apt-get update && apt-get upgrade -y

# Add 1 GB swap (prevents OOM kill during pipeline LLM calls)
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
free -h   # verify swap shows 1.0G
```

- [ ] **Step 16: Install Docker Engine + Compose plugin**

```bash
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

docker --version
docker compose version
```

Expected: `Docker version 27.x.x` and `Docker Compose version v2.x.x`

- [ ] **Step 17: Configure firewall**

```bash
ufw allow OpenSSH
ufw allow 8501/tcp
ufw --force enable
ufw status
```

---

## Task 6: Deploy Application to VM

- [ ] **Step 18: Clone the repo**

```bash
cd /opt
# Public repo:
git clone https://github.com/YOUR_ORG/job_search_agent_take_2.git job-search-agent

# Private repo — use a token:
# git clone https://YOUR_TOKEN@github.com/YOUR_ORG/job_search_agent_take_2.git job-search-agent
```

- [ ] **Step 19: Create `.env` on the server**

```bash
cd /opt/job-search-agent
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-REPLACE_ME
APIFY_API_TOKEN=apify_api_REPLACE_ME
VIBE_API_KEY=REPLACE_ME
VIBE_API_BASE_URL=https://api.vibeprospecting.com

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=job_search
POSTGRES_USER=jobsearch
POSTGRES_PASSWORD=choose_a_strong_password

RESUME_DIR=/opt/job-search-agent/resumes
EOF

# Fill in real values
nano .env

mkdir -p resumes
```

> **Important:** `POSTGRES_HOST` must be `db` (the Docker service name), not `localhost`.

- [ ] **Step 20: Build and start the stack**

```bash
cd /opt/job-search-agent
docker compose up -d --build
```

This takes 3–5 minutes on first build. Watch progress:
```bash
docker compose logs -f
```

- [ ] **Step 21: Verify containers are running**

```bash
docker compose ps
```

Expected:
```
NAME                        SERVICE  STATUS   PORTS
job-search-agent-db-1       db       running  5432/tcp
job-search-agent-app-1      app      running
job-search-agent-web-1      web      running  0.0.0.0:8501->8501/tcp
```

---

## Task 7: Verify End-to-End

- [ ] **Step 22: Confirm web UI loads**

From your local machine:
```bash
curl -s -o /dev/null -w "%{http_code}" http://<DROPLET_IP>:8501/healthz
```
Expected: `200`

Or open `http://<DROPLET_IP>:8501` in a browser — you should see "Job Search Agent" with the resume upload form.

- [ ] **Step 23: Verify database connectivity**

```bash
docker compose exec web python -c "
import asyncio, os
import asyncpg
async def check():
    conn = await asyncpg.connect(
        host='db', port=5432,
        database=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
    )
    print('DB OK:', await conn.fetchval('SELECT version()'))
    await conn.close()
asyncio.run(check())
"
```

Expected: `DB OK: PostgreSQL 16.x ...`

- [ ] **Step 24: Share the URL**

Send friends: `http://<DROPLET_IP>:8501`

They upload their own resume, enter keywords, click "Find My Jobs." No accounts or API keys needed on their end.

---

## Task 8 (Optional): Add nginx + Basic Auth

Adds a username/password gate so the app isn't open to anyone who finds the IP.

- [ ] **Step 25: Install nginx and htpasswd**

```bash
apt-get install -y nginx apache2-utils
```

- [ ] **Step 26: Create password file**

```bash
# Replace "admin" and "yourpassword"
htpasswd -bc /etc/nginx/.htpasswd admin yourpassword
# Add more users:
# htpasswd -b /etc/nginx/.htpasswd alice alicespassword
```

- [ ] **Step 27: Create nginx site config**

```bash
cat > /etc/nginx/sites-available/job-search-agent << 'EOF'
server {
    listen 80;
    server_name _;

    auth_basic "Job Search Agent";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass         http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }
}
EOF

ln -s /etc/nginx/sites-available/job-search-agent /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
systemctl enable nginx
```

- [ ] **Step 28: Bind Streamlit to localhost only**

In `docker-compose.yml`, change the web service ports:
```yaml
  web:
    ports:
      - "127.0.0.1:8501:8501"   # only reachable from host, not internet
```

Then update UFW:
```bash
ufw allow 'Nginx HTTP'
ufw delete allow 8501/tcp
```

Restart the web container:
```bash
docker compose up -d web
```

- [ ] **Step 29: Test auth**

```bash
# Without credentials → 401
curl -s -o /dev/null -w "%{http_code}" http://<DROPLET_IP>/

# With credentials → 200
curl -s -o /dev/null -w "%{http_code}" -u admin:yourpassword http://<DROPLET_IP>/
```

Share: `http://<DROPLET_IP>/` + username + password.

---

## Day-Two Operations Reference

```bash
# View logs
docker compose logs -f web

# Restart after a code change
git pull && docker compose up -d --build

# Stop everything
docker compose down

# Check disk (25 GB SSD)
df -h /
docker system df
```

---

## Free Alternative: Oracle Cloud Always Free

Oracle Cloud's Always Free tier includes 4 OCPU ARM + 24 GB RAM + 200 GB storage at zero cost. The Dockerfile's `python:3.12-slim` base image has an ARM64 variant, so `docker compose up --build` works without changes. The provisioning steps are the same (Ubuntu 24.04, apt-get, docker install); the firewall is managed via Security Lists in the Oracle Cloud Console instead of UFW. Trade-off: Oracle's console is more complex than DigitalOcean's.

---

## Files Changed Summary

| File | Change |
|---|---|
| `cli.py` | Add `output_file` param to `run_full`; add `--output-file` argparse arg; use it in write block |
| `web/app.py` | Add `import uuid`; session-scoped output path; `_run_pipeline` gets `output_file` param |
| `tests/unit/test_output_file_arg.py` | New — TDD tests for the above |
| `docker-compose.yml` | Add `restart: unless-stopped`; optionally bind web to `127.0.0.1:8501` |
