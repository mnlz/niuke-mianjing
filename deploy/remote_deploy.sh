#!/usr/bin/env bash
set -euo pipefail

APP_NAME="niuke-mianjing"
APP_DIR="/opt/${APP_NAME}"
CURRENT_DIR="${APP_DIR}/current"
RELEASE_SRC="/tmp/niuke-deploy"
WEB_PORT="${WEB_PORT:-8080}"
API_PORT="${API_PORT:-8000}"

dnf install -y python3 python3-pip nginx mariadb-server curl policycoreutils-python-utils >/dev/null
systemctl enable --now mariadb nginx >/dev/null

mkdir -p "$APP_DIR"
rm -rf "${CURRENT_DIR}.new"
mkdir -p "${CURRENT_DIR}.new"
cp -a "${RELEASE_SRC}/." "${CURRENT_DIR}.new/"

if [ ! -f "${CURRENT_DIR}.new/.env" ]; then
  echo "Missing .env in deploy package. Configure GitHub secret SERVER_ENV." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${CURRENT_DIR}.new/.env"
set +a

DB_NAME="${DB_NAME:-mianjing}"
DB_USER="${DB_USER:-niuke_app}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_CHARSET="${DB_CHARSET:-utf8mb4}"
API_PORT="${API_PORT:-8000}"

if [ -z "$DB_PASSWORD" ]; then
  echo "DB_PASSWORD cannot be empty on the server." >&2
  exit 1
fi

mysql -uroot <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET ${DB_CHARSET} COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
USE \`${DB_NAME}\`;
CREATE TABLE IF NOT EXISTS \`niuke\` (
  \`id\` INT AUTO_INCREMENT PRIMARY KEY,
  \`content_id\` VARCHAR(100) NULL,
  \`title\` VARCHAR(500) NOT NULL,
  \`content\` MEDIUMTEXT NULL,
  \`edit_time\` DATETIME NULL,
  \`read\` INT DEFAULT 0,
  \`post\` VARCHAR(100) NULL,
  \`company\` VARCHAR(100) NULL,
  \`status\` TINYINT DEFAULT 1,
  \`created_at\` DATETIME DEFAULT CURRENT_TIMESTAMP,
  \`updated_at\` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY \`idx_content_id\` (\`content_id\`),
  KEY \`idx_post_company\` (\`post\`, \`company\`),
  KEY \`idx_edit_time\` (\`edit_time\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS \`update\` (
  \`id\` INT AUTO_INCREMENT PRIMARY KEY,
  \`time\` DATETIME NULL,
  \`totalPage\` INT DEFAULT 0,
  \`total\` INT DEFAULT 0,
  \`post\` VARCHAR(100) NULL,
  KEY \`idx_post_time\` (\`post\`, \`time\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS \`crawl_log\` (
  \`id\` INT AUTO_INCREMENT PRIMARY KEY,
  \`post\` VARCHAR(50) NOT NULL,
  \`start_time\` DATETIME NULL,
  \`end_time\` DATETIME NULL,
  \`total_pages\` INT NULL,
  \`new_records\` INT DEFAULT 0,
  \`updated_records\` INT DEFAULT 0,
  \`status\` VARCHAR(20) NULL,
  \`error_message\` TEXT NULL,
  \`created_at\` DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY \`idx_post_start_time\` (\`post\`, \`start_time\`),
  KEY \`idx_status\` (\`status\`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL

python3 -m venv "${CURRENT_DIR}.new/.venv"
"${CURRENT_DIR}.new/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"${CURRENT_DIR}.new/.venv/bin/pip" install -r "${CURRENT_DIR}.new/requirements.txt"

if [ -d "$CURRENT_DIR" ]; then
  rm -rf "${CURRENT_DIR}.previous"
  mv "$CURRENT_DIR" "${CURRENT_DIR}.previous"
fi
mv "${CURRENT_DIR}.new" "$CURRENT_DIR"

cat >/etc/systemd/system/niuke-mianjing.service <<SERVICE
[Unit]
Description=Niuke Mianjing FastAPI service
After=network.target mariadb.service

[Service]
Type=simple
WorkingDirectory=${CURRENT_DIR}
EnvironmentFile=${CURRENT_DIR}/.env
ExecStart=/bin/bash -lc 'source ${CURRENT_DIR}/.env && exec ${CURRENT_DIR}/.venv/bin/uvicorn niuke_mianjing_backend.api.app:app --host 127.0.0.1 --port \${API_PORT:-8000}'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

cat >/etc/nginx/conf.d/niuke-mianjing.conf <<NGINX
server {
    listen ${WEB_PORT};
    server_name 120.26.3.11;
    root ${CURRENT_DIR}/frontend-dist;
    index index.html;

    client_max_body_size 20m;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location = /health {
        proxy_pass http://127.0.0.1:${API_PORT}/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/ws/ {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 3600s;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:${API_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
NGINX

setsebool -P httpd_can_network_connect 1 >/dev/null 2>&1 || true
firewall-cmd --add-port=${WEB_PORT}/tcp --permanent >/dev/null 2>&1 || true
firewall-cmd --reload >/dev/null 2>&1 || true

systemctl daemon-reload
systemctl enable --now niuke-mianjing
systemctl restart niuke-mianjing
nginx -t
systemctl reload nginx

for i in {1..20}; do
  if curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null; then
    echo "Backend health check passed."
    exit 0
  fi
  sleep 1
done

echo "Backend health check failed." >&2
journalctl -u niuke-mianjing --no-pager -n 120 >&2
exit 1
