# -------- Config --------
S ?= auth-service          # default service for logs/shell/etc.
HOST ?= 127.0.0.1          # public host to curl Traefik via :80
PREFIX ?= /auth-service    # external path prefix
API_PREFIX ?= /api         # internal API prefix in Flask
COMPOSE ?= docker compose

# -------- Networks --------
# Ensure the external networks exist (safe if already present)
net:
	@echo "🌐 Ensuring external networks exist..."
	-@docker network inspect authnet >/dev/null 2>&1 || docker network create authnet
	-@docker network inspect web >/dev/null 2>&1 || docker network create web

# -------- Lifecycle --------
up: net
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

ps:
	$(COMPOSE) ps

# -------- Logs / Shell --------
logs:
	$(COMPOSE) logs -f $(S)

tlogs:
	$(COMPOSE) logs -f traefik

shell:
	$(COMPOSE) exec $(S) sh -lc 'exec bash || exec sh'

flask-shell:
	$(COMPOSE) exec auth-service flask shell

# -------- Health / Smoke tests --------
# Internal (container-local) health
health-int:
	$(COMPOSE) exec auth-service sh -lc '\
	  BODY=$$(curl -sS http://127.0.0.1:5000/health) || exit $$?; \
	  python - <<PY 2>/dev/null || { echo "$$BODY"; exit 0; } \
import json,sys; print(json.dumps(json.loads(sys.stdin.read()), indent=2)) \
PY \
	  <<< "$$BODY"'

health-int-raw:
	$(COMPOSE) exec auth-service sh -lc 'curl -i http://127.0.0.1:5000/health'

# ---------- Curl via helper container (no curl in your images) ----------
# Usage:
#   make curl-net NET=authnet URL=http://auth-service:5000/health
#   make curl-net NET=web     URL=http://traefik/auth-service/api/health
curl-net:
	@test -n "$(NET)" || (echo "❗ Set NET=authnet|web (or any docker network)"; exit 1)
	@test -n "$(URL)" || (echo "❗ Set URL=http://..."; exit 1)
	docker run --rm --network $(NET) curlimages/curl:latest -si $(URL)

# ---------- Health checks ----------
# Internal service health (inside Docker, service-to-service path, no Traefik)
# Uses the shared app network "authnet"
health-authnet:
	docker run --rm --network authnet curlimages/curl:latest -si http://auth-service:5000/health

# Through Traefik on the "web" network (browser path with prefix)
# Hits the Traefik container by name
health-web:
	docker run --rm --network web curlimages/curl:latest -si http://traefik/auth-service/health

# From the host (Traefik published on :80). Override HOST if needed.
HOST ?= 127.0.0.1
health-host:
	@curl -si "http://$(HOST)/auth-service/health"

.PHONY: curl-net health-authnet health-web health-host

# Through Traefik with external prefix
health-ext:
	@echo "GET http://$(HOST)$(PREFIX)$(API_PREFIX)/health"
	@curl -si http://$(HOST)$(PREFIX)$(API_PREFIX)/health | sed -n '1,20p'

# Debug route map (if you kept /debug/routes endpoint)
routes:
	$(COMPOSE) exec auth-service sh -lc 'curl -s http://127.0.0.1:5000/debug/routes || true'

# -------- Build images (prod vs dev) --------
# Production image uses the final "runtime" stage of your multi-stage Dockerfile
build:
	docker build -t auth-service:prod .

# Dev image includes pytest et al (uses the "dev" stage)
build-dev:
	docker build --target dev -t auth-service:dev .

# -------- Tests (run in dev image; no compose needed) --------
# Mount the repo and run pytest inside the dev image, isolated from your prod container
test: build-dev
	docker run --rm -v "$$PWD":/app -w /app auth-service:dev pytest -v tests

# If your tests need env vars from .env (but NOT real DB), pass them explicitly:
test-env: build-dev
	docker run --rm --env-file .env -v "$$PWD":/app -w /app auth-service:dev pytest -v tests

# -------- Service-only controls (no DB down) --------
fdown:
	$(COMPOSE) stop auth-service && $(COMPOSE) rm -f auth-service

fup: net
	$(COMPOSE) up --build -d auth-service

# -------- Initialize / Reset --------
init:
	@echo "🔑 Creating .env (if missing) ..."
	@./init_env.sh
	@$(MAKE) net

reset: down
	@echo "⚠️  Removing DB volume and .env to start fresh..."
	-@docker volume rm $$(docker volume ls -q | grep -E '^auth-service_auth-db-data$$') || true
	-@rm -f .env
	@echo "🧹 Trying to delete external networks (safe to fail) ..."
	-@docker network rm authnet 2>/dev/null || true
	-@docker network rm web 2>/dev/null || true
	@echo "✅ Reset complete. Run 'make init' then 'make up'."

.PHONY: net up down restart ps logs tlogs shell flask-shell health-int health-ext routes build build-dev test test-env fdown fup init reset
