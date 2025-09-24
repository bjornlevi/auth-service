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

# ---------- Curl via helper container (no curl in your images) ----------
# Usage:
#   make curl-net NET=authnet URL=http://auth-service:5000/health
#   make curl-net NET=web     URL=http://traefik/auth-service/health
curl-net:
	@test -n "$(NET)" || (echo "❗ Set NET=authnet|web (or any docker network)"; exit 1)
	@test -n "$(URL)" || (echo "❗ Set URL=http://..."; exit 1)
	docker run --rm --network $(NET) curlimages/curl:latest -si "$(URL)"

# -------- Health / Smoke tests --------

# Internal (container-local) health: pretty JSON if possible, else raw body
health-int:
	$(COMPOSE) exec auth-service sh -lc 'python -c "import json,urllib.request,sys; u=urllib.request.urlopen(\"http://127.0.0.1:5000/health\",timeout=3); print(json.dumps(json.loads(u.read().decode()), indent=2))" 2>/dev/null || python -c "import urllib.request; print(urllib.request.urlopen(\"http://127.0.0.1:5000/health\",timeout=3).read().decode())"'

# Internal service health from another container on authnet
health-authnet:
	@echo "GET http://auth-service:5000/health (on network authnet)"
	@docker run --rm --network authnet curlimages/curl:latest -sS -i http://auth-service:5000/health

# Through Traefik (inside the web network)
health-web:
	@echo "GET http://traefik/auth-service/health (on network web)"
	@docker run --rm --network web curlimages/curl:latest -sS -i http://traefik/auth-service/health

# From the host (Traefik published on :80). Override HOST if needed.
HOST ?= 127.0.0.1
HOST := $(strip $(HOST))
health-host:
	@URL="http://$(HOST)/auth-service/health"; echo "GET $$URL"
	@curl -sS -i "$$URL"

# Through Traefik with external prefix (e.g. what browsers use)
PREFIX ?= /auth-service
API_PREFIX ?=
API_PREFIX := $(strip $(API_PREFIX))
PREFIX := $(strip $(PREFIX))
health-ext:
	@URL="http://$(HOST)$(PREFIX)$(API_PREFIX)/health"; \
	echo "GET $$URL"; \
	tmpdir=$$(mktemp -d); \
	code=$$(curl -sS -o $$tmpdir/body -D $$tmpdir/headers -w '%{http_code}' "$$URL"); \
	cat $$tmpdir/headers | sed -n '1,20p'; echo; cat $$tmpdir/body | sed -n '1,20p'; \
	rm -rf $$tmpdir; \
	[ "$$code" -lt 400 ] || { echo "HTTP $$code FAIL"; exit 1; }

# Run all health checks; show PASS/FAIL per step and final summary
health-all:
	@ec=0; \
	step() { name="$$1"; shift; echo "── $$name ─────────────────────────────────────────"; if "$$@"; then echo "✔ $$name PASS"; else code=$$?; echo "✘ $$name FAIL (exit $$code)"; ec=1; fi; echo; }; \
	step health-int      $(COMPOSE) exec auth-service sh -lc 'python -c "import json,urllib.request,sys; u=urllib.request.urlopen(\"http://127.0.0.1:5000/health\",timeout=3); print(json.dumps(json.loads(u.read().decode()), indent=2))" 2>/dev/null || python -c "import urllib.request; print(urllib.request.urlopen(\"http://127.0.0.1:5000/health\",timeout=3).read().decode())"'; \
	step health-authnet  sh -lc "docker run --rm --network authnet curlimages/curl:latest -sS -i http://auth-service:5000/health"; \
	step health-web      sh -lc "docker run --rm --network web curlimages/curl:latest -sS -i http://traefik/auth-service/health"; \
	step health-host     sh -lc 'URL="http://$(HOST)/auth-service/health"; echo "GET $$URL"; curl -sS -i "$$URL"'; \
	step health-ext      sh -lc 'URL="http://$(HOST)$(PREFIX)$(API_PREFIX)/health"; echo "GET $$URL"; curl -sS -i "$$URL" | sed -n "1,20p"'; \
	if [ $$ec -eq 0 ]; then echo "✅ ALL HEALTH CHECKS PASSED"; else echo "❌ SOME HEALTH CHECKS FAILED"; fi; exit $$ec

.PHONY: health-int health-authnet health-web health-host health-ext health-all

# -------- API Smoke Test --------
test-api:
	@echo "🔑 Testing API login → userinfo → verify..."
	@HOST=$${HOST:-127.0.0.1}; \
	BASE="http://$$HOST/auth-service/api"; \
	APIKEY=$$(grep '^AUTH_SERVICE_API_KEY=' .env | cut -d= -f2); \
	USER=$$(grep '^DEFAULT_ADMIN=' .env | cut -d= -f2); \
	PASS=$$(grep '^DEFAULT_ADMIN_PASSWORD=' .env | cut -d= -f2); \
	echo "→ Login as $$USER..."; \
	TOKEN=$$(curl -s -X POST "$$BASE/login" \
	  -H "Content-Type: application/json" \
	  -H "X-API-Key: $$APIKEY" \
	  -d "{\"username\":\"$$USER\",\"password\":\"$$PASS\"}" | jq -r .token); \
	if [ "$$TOKEN" = "null" ] || [ -z "$$TOKEN" ]; then \
	  echo "❌ Login failed"; exit 1; fi; \
	TOKEN_PREFIX=$$(echo $$TOKEN | cut -c1-16); \
	echo "✅ Got token: $${TOKEN_PREFIX}..."; \
	echo; echo "→ /userinfo"; \
	curl -s -X POST "$$BASE/userinfo" \
	  -H "Content-Type: application/json" \
	  -H "X-API-Key: $$APIKEY" \
	  -d "{\"token\":\"$$TOKEN\"}" | jq .; \
	echo; echo "→ /verify"; \
	curl -s -X POST "$$BASE/verify" \
	  -H "Content-Type: application/json" \
	  -H "X-API-Key: $$APIKEY" \
	  -d "{\"token\":\"$$TOKEN\"}" | jq .


# Show Flask routes through Traefik (from host)
routes:
	@curl -s http://$(HOST)/auth-service/debug/routes | python3 -m json.tool || \
	 (echo "❌ Failed to fetch routes from host"; exit 1)

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
	@echo "⚠️  Removing DB volume(s) and .env to start fresh..."
	-@docker volume rm auth-db-data 2>/dev/null || true
	-@docker volume rm $$(docker volume ls -q | grep -E '(^|_)auth-db-data$$') 2>/dev/null || true
	-@rm -f .env
	@echo "🧹 Trying to delete external networks (safe to fail) ..."
	-@docker network rm authnet 2>/dev/null || true
	-@docker network rm web 2>/dev/null || true
	@echo "✅ Reset complete. Run 'make init', edit .env, then 'make up'."

.PHONY: net up down restart ps logs tlogs shell flask-shell health-int health-ext routes build build-dev test test-env fdown fup init reset
