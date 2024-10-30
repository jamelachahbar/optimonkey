version: '3.8'

services:
  flask-api:
    build: ./backend/flask-api
    ports:
      - "5000:5000"
    volumes:
      - ./backend/flask-api:/app
    environment:
      - FLASK_ENV=development

  fastapi-api:
    build: ./backend/fastapi-api
    ports:
      - "8081:8081"
    volumes:
      - ./backend/fastapi-api:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/frontend
    environment:
      - CHOKIDAR_USEPOLLING=true
