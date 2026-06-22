# TabletCAD Deployment

This document describes how TabletCAD is deployed to the external server hosting
`tabcad.ru`.

## Project

- Repository: `https://github.com/obmenok/tabcad.git`
- Development branch: `feat/geometry-validation-clamping`
- Server deployment branch: `main`
- Local project path: `C:\Users\User\Documents\Buyakov\tabcad`
- Server project path: `/opt/tabcad`

## Server

- IP: `185.26.121.36`
- Domain: `tabcad.ru`
- `www.tabcad.ru` should point to the same IP.
- Recommended access method: VS Code Remote SSH.
- VS Code SSH alias used previously: `tabcad-vps`
- The app runs on the server through Docker Compose.
- Docker Compose service/container: `tabcad`
- Internal app port: `8050`
- Dash is launched through `gunicorn`.

## Environment Variables

Optional runtime settings for access codes and export rate limits:

```bash
TABCAD_TOKEN_SECRET="replace-with-long-random-secret"
TABCAD_DB_PATH="/app/data/presets.db"
TABCAD_ADMIN_TOKENS="ABCDE-12345-FGHIJ-67890"
TABCAD_DEFAULT_PRESET_LIMIT=50
TABCAD_ADMIN_PRESET_LIMIT=1000000
TABCAD_EMPTY_USER_RETENTION_DAYS=30
TABCAD_CLEANUP_INTERVAL_SECONDS=86400
TABCAD_MAX_PRESET_JSON_BYTES=100000
TABCAD_PDF_LIMIT_PER_HOUR=10
TABCAD_PDF_COOLDOWN_SECONDS=20
TABCAD_STL_LIMIT_PER_HOUR=20
TABCAD_STL_COOLDOWN_SECONDS=10
```

`TABCAD_ADMIN_TOKENS` is a comma-separated list of access codes that bypass
PDF/STL rate limits and receive the admin preset limit.

`TABCAD_DB_PATH` should point to a persistent Docker volume/bind mount. Do not
store production presets only inside the container filesystem, because
`docker compose down && docker compose up -d --build` recreates the container.

## DNS

Required DNS records:

```text
A @   -> 185.26.121.36
A www -> 185.26.121.36
```
Note: If using Cloudflare in the future, ensure Anti-DDoS protections on the hosting provider do not block Cloudflare's IP addresses, as this causes HTTP/2 Protocol Errors.

## Nginx

Nginx is configured to serve static assets directly from the disk (bypassing Gunicorn) to heavily optimize memory usage and response times. Dynamic requests are proxied to the Dash app.

Config file:

```bash
/etc/nginx/sites-available/tabcad
```

Current HTTPS server block:

```nginx
server {
    server_name tabcad.ru www.tabcad.ru;

    location /assets/ {
        root /opt/tabcad;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;

        proxy_read_timeout 180s;
        proxy_send_timeout 180s;
    }

    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/tabcad.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tabcad.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    listen 80;
    server_name tabcad.ru www.tabcad.ru;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/tabcad /etc/nginx/sites-enabled/tabcad
sudo nginx -t
sudo systemctl reload nginx
```

### Nginx Gzip

Dash sends large text payloads for 2D SVG and 3D Plotly JSON. Gzip should be
enabled for JSON, CSS, JavaScript, XML, and SVG responses.

Global config file:

```bash
/etc/nginx/nginx.conf
```

Recommended gzip block inside `http { ... }`:

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
        # multi_accept on;
}

http {

        # Basic Settings

        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;
        server_tokens off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        # SSL Settings

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;

        # Logging Settings

        access_log /var/log/nginx/access.log;

        # Gzip Settings

        gzip on;
        gzip_vary on;
        gzip_proxied any;
        gzip_comp_level 5;
        gzip_buffers 16 8k;
        gzip_http_version 1.1;
        gzip_min_length 1024;
        gzip_types
                text/plain
                text/css
                text/xml
                text/javascript
                application/json
                application/javascript
                application/xml
                application/xml+rss
                image/svg+xml;

        # Virtual Host Configs

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
```

After nginx changes:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Check gzip:

```bash
curl -I -H "Accept-Encoding: gzip" https://tabcad.ru/_dash-layout
curl -I -H "Accept-Encoding: gzip" https://tabcad.ru/_dash-dependencies
curl -I -H "Accept-Encoding: gzip" https://tabcad.ru/assets/apollo_viewer.css
```

Expected header:

```text
Content-Encoding: gzip
```

Check static cache headers:

```bash
curl -I https://tabcad.ru/assets/apollo_viewer.css
curl -I https://tabcad.ru/_dash-component-suites/dash/dcc/dash_core_components.v4_1_0m1780781398.js
```

Expected cache behavior:

```text
/assets/...                  -> Cache-Control: public, max-age=2592000
/_dash-component-suites/...  -> Cache-Control: public, max-age=31536000, immutable
```

Do not cache dynamic Dash endpoints such as `/_dash-update-component`,
`/_dash-layout`, or `/_dash-dependencies`.

## HTTPS

If DNS already points to the server:

```bash
sudo certbot --nginx -d tabcad.ru -d www.tabcad.ru
```

If `www` is not configured in DNS, certbot fails with `NXDOMAIN`.

## Server Checks

Check app state and logs:

```bash
cd /opt/tabcad
docker compose ps
docker compose logs -f --tail=200 tabcad
```

Check Dash versions inside the container:

```bash
docker compose exec tabcad python -c "import dash, dash_bootstrap_components as dbc; print(dash.__version__, dbc.__version__)"
```

At the last known sync:

```text
dash 4.1.0
dash-bootstrap-components 2.0.4
```

Check the current server commit:

```bash
cd /opt/tabcad
git rev-parse --short HEAD
```

## Standard Deployment

After changes are merged into `main` and pushed to GitHub:

```bash
cd /opt/tabcad
git fetch origin
git checkout main
git pull --ff-only origin main
docker compose down
docker compose up -d --build
docker compose logs -f --tail=200 tabcad
```

## Local Workflow

Development usually happens on the feature branch:

```bash
git checkout feat/geometry-validation-clamping
git pull --ff-only origin feat/geometry-validation-clamping
```

After a batch of changes:

```bash
git status --short
git add .
git commit -m "..."
git push origin feat/geometry-validation-clamping
```

Merge into `main`:

```bash
git checkout main
git pull --ff-only origin main
git merge feat/geometry-validation-clamping
git push origin main
git checkout feat/geometry-validation-clamping
```

Then deploy on the server using the standard deployment commands.

## Troubleshooting

### Duplicate Component ID

If the server reports `Duplicate component id`, the layout usually contains two
components with the same `id`. One previous case involved `sidebar-container`.

Check with:

```bash
rg "sidebar-container|id=" app.py components callbacks
```

### Old Styles After Deploy

Check that the server is on the expected commit:

```bash
cd /opt/tabcad
git rev-parse --short HEAD
```

Rebuild the container:

```bash
docker compose down
docker compose up -d --build
```

Then hard refresh the browser:

```text
Ctrl+F5
```

### PDF Or 3D Issues On Server

Check logs:

```bash
docker compose logs -f --tail=200 tabcad
```

PDF with 3D on the VPS previously started working after adding system
dependencies to `Dockerfile` and running the app through the container.

The app should run through Docker on the server, not directly through
`python app.py`.

## Important Rules

- Server code should come from `main`.
- Development continues on `feat/geometry-validation-clamping`.
- Do not edit files directly on the server except for emergency diagnostics.
- Normal path: local changes -> commit -> push -> merge into `main` -> deploy.
