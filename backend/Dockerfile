version: '3.8'

services:
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
