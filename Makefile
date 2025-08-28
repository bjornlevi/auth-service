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