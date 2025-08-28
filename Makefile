init:
	./init_env.sh

net:
	docker network inspect authnet >/dev/null 2>&1 || docker network create authnet

up: net
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f web

shell:
	docker compose exec web flask shell

test:
	docker compose run --rm web pytest -v tests

# Flask-only shortcuts
fdown:
	docker compose stop web && docker compose rm -f web

fup:
	docker compose up --build -d web

reset: down
	@echo "⚠️  Removing .env and DB volumes to start fresh..."
	@rm -f .env
	@docker volume rm $$(docker volume ls -q | grep auth_auth-db-data) || true
	@echo "✅ Reset complete. Run 'make init' to create a new .env."
