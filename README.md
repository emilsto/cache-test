# Express TS Server

A draft Express server with PostgreSQL and Redis integration.

## Features
- Express server using TypeScript
- PostgreSQL connection
- Redis connection
- Sample routes for both services

## Getting Started

1. Install dependencies
2. Update PostgreSQL credentials in src/utils/dbUtils.ts
3. Start the server with:
   -  for development
   -  after building with 

## Routes
- POSTGRES:
  - GET /api/postgres/test - Fetch sample data
- REDIS:
  - GET /api/redis/get/:key - Retrieve value by key
  - POST /api/redis/set - Set key-value pair
