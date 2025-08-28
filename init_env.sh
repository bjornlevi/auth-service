#!/usr/bin/env bash
# init_env.sh - Generate a .env file with placeholder values for auth service

set -e

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
  echo "⚠️  $ENV_FILE already exists. Remove it first if you want to regenerate."
  exit 1
fi

cat > $ENV_FILE <<EOL
# =============================
# Auth Service Environment Config
# =============================

# MySQL
MYSQL_DATABASE=authdb
MYSQL_USER=authuser
MYSQL_PASSWORD=authpass
MYSQL_ROOT_PASSWORD=rootpass
MYSQL_HOST=db

# Flask
FLASK_ENV=development
SECRET_KEY=replace_with_a_secret_key

# Default admin bootstrap
DEFAULT_ADMIN=admin
DEFAULT_ADMIN_PASSWORD=adminpass
EOL

echo "✅ $ENV_FILE created. Please edit values before running 'make up'."
