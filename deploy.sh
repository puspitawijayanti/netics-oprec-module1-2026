#!/bin/bash
set -e

cd ~/app

docker rm -f netics-api || true
docker build -t netics-health-api ./src
docker run -d --name netics-api -p 3000:3000 --restart unless-stopped netics-health-api