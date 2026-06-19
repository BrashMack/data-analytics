up:
	docker compose up -d postgres

etl:
	docker compose run --rm etl

analytics:
	docker compose run --rm analytics

all: up etl analytics

down:
	docker compose down -v
