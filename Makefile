.PHONY: up down build

up:
	docker-compose up --build

down:
	docker-compose down --volumes

build:
	docker-compose build
