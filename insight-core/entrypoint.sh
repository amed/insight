#!/bin/sh
set -e

echo "Running database migrations..."
npx sequelize-cli db:migrate

echo "Starting insight-core..."
exec node src/server.js
