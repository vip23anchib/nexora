# Nexora — Production Deployment Handbook

> **Step-by-step guides for deploying Nexora to production using Docker Compose, Cloud VPS, Managed PaaS (Render / Railway), or Traditional Linux VMs.**

---

## Deployment Architecture Overview

Nexora is composed of 5 services:
1. **Frontend:** React 18 + Vite SPA built into static assets and served by **Nginx Alpine** (Port `80` or `3000`).
2. **Backend API:** Django 6.0 + DRF running via **Gunicorn WSGI** (Port `8000`).
3. **Database:** **PostgreSQL 16** with persistent volume storage.
4. **Task Queue & Cache:** **Redis 7** (In-memory message broker).
5. **Background Workers:** **Celery Worker** (chunked ingestion pipelines) and **Celery Beat** (scheduler).

---

## Method 1: 1-Command Docker Deployment (Recommended for VPS / Cloud VM)

*Best for: DigitalOcean Droplet ($6–$12/mo), AWS EC2, Hetzner Cloud, Linode, or any Ubuntu/Debian server.*

### Step 1: Provision your Virtual Machine
1. Create an Ubuntu 22.04 or 24.04 LTS instance with at least **2GB RAM** (recommended: 4GB for high-concurrency ingestion).
2. SSH into your server:
   ```bash
   ssh root@your-server-ip
   ```

### Step 2: Install Docker & Docker Compose
```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify Docker installation
docker --version
docker compose version
```

### Step 3: Clone the Repository
```bash
git clone https://github.com/vip23anchib/nexora.git
cd nexora
```

### Step 4: Configure Environment Variables
Copy `.env.example` and set production secrets:
```bash
cp .env.example .env
nano .env
```

Ensure the following variables are configured:
```env
# Security
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=generate-a-secure-50-character-random-string-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip,localhost,127.0.0.1,backend

# Database
POSTGRES_DB=nexora
POSTGRES_USER=nexora_user
POSTGRES_PASSWORD=use-a-strong-random-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis & Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com,http://your-server-ip:3000
```

### Step 5: Build & Launch with Docker Compose
```bash
# Build images and start all 5 containers in the background
docker compose up --build -d
```

### Step 6: Seed Deterministic Demo Data
Once containers are healthy, seed the database:
```bash
docker compose exec backend python manage.py seed_demo_data
```

### Step 7: Verify Running Containers
```bash
docker compose ps
```
You should see:
- `nexora-postgres` (healthy)
- `nexora-redis` (healthy)
- `nexora-backend` (up)
- `nexora-celery-worker` (up)
- `nexora-celery-beat` (up)
- `nexora-frontend` (up, ports `0.0.0.0:3000->80/tcp`)

Navigate to `http://your-server-ip:3000` in your browser!

---

## Method 2: Free / Low-Cost PaaS Deployment (Render / Railway)

If you don't want to manage a Linux server, you can deploy to **Render** or **Railway**.

### Strategy: Split Architecture
- **PostgreSQL:** Managed database (e.g. Render Postgres / Neon / Supabase).
- **Redis:** Managed Redis (e.g. Render Redis / Upstash Redis).
- **Backend API:** Web Service running Dockerfile (`backend/Dockerfile`).
- **Celery Worker:** Background Worker running Dockerfile (`backend/Dockerfile`) with command `celery -A config worker --loglevel=info`.
- **Frontend SPA:** Static Site built from `frontend/` (or Vercel / Netlify).

### Step-by-Step on Render:
1. **Create PostgreSQL Database:**
   - On [render.com](https://render.com), click **New +** $\to$ **PostgreSQL**.
   - Note the Internal Database URL.
2. **Create Redis Service:**
   - Click **New +** $\to$ **Redis**.
   - Note the Internal Redis URL.
3. **Deploy Backend (Web Service):**
   - Click **New +** $\to$ **Web Service**. Connect your GitHub repository.
   - Root Directory: `backend`
   - Runtime: `Docker` (Dockerfile Path: `Dockerfile`)
   - Environment Variables:
     - `DATABASE_URL`: *(Your Postgres Internal Connection String)*
     - `CELERY_BROKER_URL`: *(Your Redis Internal Connection String)*
     - `CELERY_RESULT_BACKEND`: *(Your Redis Internal Connection String)*
     - `SECRET_KEY`: *(Generate a secure random key)*
     - `DJANGO_SETTINGS_MODULE`: `config.settings.production`
     - `ALLOWED_HOSTS`: `.onrender.com,localhost`
4. **Deploy Celery Worker (Background Worker):**
   - Click **New +** $\to$ **Background Worker**. Connect the repository.
   - Root Directory: `backend`
   - Command: `celery -A config worker --loglevel=info --concurrency=2`
   - Add the same `DATABASE_URL` and `CELERY_BROKER_URL` environment variables.
5. **Deploy Frontend (Static Site):**
   - Click **New +** $\to$ **Static Site** (or deploy on [Vercel](https://vercel.com)).
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Publish Directory: `dist`
   - Environment Variable: `VITE_API_URL`: `https://your-backend.onrender.com/api/v1`

---

## Method 3: SSL / HTTPS Setup with Domain & Certbot (Production VPS)

To point a custom domain (e.g. `nexora.yourdomain.com`) with a free **Let's Encrypt SSL** certificate on your VPS:

### Step 1: Install Nginx on Host & Certbot
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### Step 2: Configure Host Nginx Reverse Proxy
Edit `/etc/nginx/sites-available/nexora`:
```nginx
server {
    server_name nexora.yourdomain.com;

    # Frontend SPA (forwarding to docker container on port 3000)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API (direct to port 8000 if not proxying via frontend container)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/nexora /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 3: Obtain Free Automated SSL Certificate
```bash
sudo certbot --nginx -d nexora.yourdomain.com
```
Certbot will automatically obtain the certificate and configure HTTPS redirection!

---

## Production Maintenance Runbook

### How to apply database migrations in production:
```bash
docker compose exec backend python manage.py migrate
```

### How to view real-time logs:
```bash
# View backend API logs
docker compose logs -f backend

# View Celery ingestion worker logs
docker compose logs -f celery_worker

# View all container logs
docker compose logs -f
```

### How to update to the latest code:
```bash
git pull origin main
docker compose up --build -d
```

### How to backup the database:
```bash
docker compose exec db pg_dump -U nexora_user nexora > nexora_backup_$(date +%F).sql
```

### How to restore a database backup:
```bash
cat nexora_backup_2026-10-20.sql | docker compose exec -T db psql -U nexora_user -d nexora
```
