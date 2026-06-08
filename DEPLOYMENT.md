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

## DNS

Required DNS records:

```text
A @   -> 185.26.121.36
A www -> 185.26.121.36
```

## Nginx

Nginx proxies the domain to the Dash app.

Config file:

```bash
/etc/nginx/sites-available/tabcad
```

Current HTTPS server block:

```nginx
server {
    server_name tabcad.ru www.tabcad.ru;

    location /assets/ {
        proxy_pass http://127.0.0.1:8050;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    location /_dash-component-suites/ {
        proxy_pass http://127.0.0.1:8050;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        expires 365d;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8050;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/tabcad.ru/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/tabcad.ru/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
```

HTTP server block redirects to HTTPS and is managed by Certbot:

```nginx
server {
    if ($host = www.tabcad.ru) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    if ($host = tabcad.ru) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name tabcad.ru www.tabcad.ru;
    return 404; # managed by Certbot
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
