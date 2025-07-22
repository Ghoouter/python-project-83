install:
	poetry install

dev:
	poetry run flask --debug --app page_analyzer:app run

lint:
	poetry run ruff check page_analyzer --fix

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

render-restart:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app