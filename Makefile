init:
	@echo "🔑 Creating .env file..."
	./init_env.sh
	@echo "🌐 Ensuring shared authnet network exists..."
	-docker network create authnet || true

net:
	docker network inspect authnet >/dev/null 2>&1 || docker network create authnet

up: net
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f auth-service

shell:
	docker compose exec auth-service flask shell

test:
	docker compose run --rm auth-service pytest -v tests

# Flask-only shortcuts
fdown:
	docker compose stop auth-service && docker compose rm -f auth-service

fup:
	docker compose up --build -d auth-service

reset: down
	@echo "⚠️  Removing .env and DB volumes to start fresh..."
	@rm -f .env
	@docker volume rm $$(docker volume ls -q | grep auth-service_auth-db-data) || true
	docker network rm authnet
	@echo "✅ Reset complete. Run 'make init' to create a new .env."
