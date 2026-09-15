#!/usr/bin/env bash
# issue_cert.sh — выписать LE-сертификат для поддомена кабинета через webroot.
# Трафик 80 -> nginx -> /.well-known, поэтому перед этим должен быть поднят стек
# `docker compose -f docker/docker-compose.yml up -d` (нужен nginx).
#
# Использование:
#   DOMAIN=cab.nyxvps.space EMAIL=admin@nyxvps.space bash docker/scripts/issue_cert.sh
# По умолчанию берёт cab.nyxvps.space / первый ADMIN_EMAIL или admin@домен.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.yml"

DOMAIN="${DOMAIN:-cab.nyxvps.space}"
# почта для уведомлений LE
EMAIL="${EMAIL:-${ADMIN_EMAIL:-admin@${DOMAIN#*.}}}"
CERTBOT_WWW="$PROJECT_ROOT/docker/certbot/www"
CERTBOT_CONF="$PROJECT_ROOT/docker/certbot/conf"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "compose file not found: $COMPOSE_FILE" >&2; exit 1
fi

# A-запись уже можно проверить: dig +short "$DOMAIN"
echo "[issue_cert] DOMAIN=$DOMAIN EMAIL=$EMAIL"
mkdir -p "$CERTBOT_WWW" "$CERTBOT_CONF"

# nginx уже слушает 80 + пробрасывает ACME. Запустим certbot в контейнере, томы совпадают с compose.
docker run --rm \
  -v "$CERTBOT_WWW:/var/www/certbot" \
  -v "$CERTBOT_CONF:/etc/letsencrypt" \
  certbot/certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" --agree-tos --no-eff-email

echo "[issue_cert] done: $CERTBOT_CONF/live/$DOMAIN/"
echo "Перезапусти nginx:  docker compose -f docker/docker-compose.yml restart nginx"
echo "Продление:  docker run ... certbot/certbot renew  +  nginx -s reload (размести в cron/systemd)"
