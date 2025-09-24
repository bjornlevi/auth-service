#!/usr/bin/env bash
# init_env.sh - Generate a .env file with secure random values for auth service

set -e

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
  echo "⚠️  $ENV_FILE already exists. Remove it first if you want to regenerate."
  exit 1
fi

# Generate secure random values
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DEFAULT_API_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
MYSQL_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')
MYSQL_ROOT_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')
DEFAULT_ADMIN_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')

cat > $ENV_FILE <<EOL
# =============================
# Auth Service Environment Config
# =============================

# MySQL
MYSQL_DATABASE=authdb
MYSQL_USER=authuser
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_HOST=db

# Flask
FLASK_ENV=development
SECRET_KEY=${SECRET_KEY}

# Site identity
SITE_NAME=site_name_replace
UI_PREFIX=/ui
API_PREFIX=/api

# Default admin bootstrap
DEFAULT_ADMIN=admin
DEFAULT_ADMIN_PASSWORD=${DEFAULT_ADMIN_PASSWORD}

# Default service API key (first allowed service)
AUTH_SERVICE_API_KEY=${DEFAULT_API_KEY}
EOL

echo "✅ $ENV_FILE created with secure random values."
echo "   Default admin = admin / ${DEFAULT_ADMIN_PASSWORD}"
