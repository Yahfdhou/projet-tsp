#!/bin/bash
# Deploy TSP-SBA on Sheikh server
# Usage: bash sheikh-deploy.sh

set -e

PROJECT_DIR="$HOME/projet-tsp"
IMAGE_NAME="tsp-sba:latest"
CONTAINER_NAME="tsp-sba-run"

echo "=== 1. Go to project directory ==="
cd "$PROJECT_DIR"

echo "=== 2. Pull latest code from GitHub ==="
git pull origin main

echo "=== 3. Remove all old Docker images and containers ==="
sudo docker system prune -a -f

echo "=== 4. Stop and remove old container (if exists) ==="
sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "=== 5. Build Docker image (no cache) ==="
sudo docker build --no-cache -t "$IMAGE_NAME" .

echo "=== 6. Run container in background (-d) ==="
mkdir -p "$PROJECT_DIR/results"

sudo docker run -d \
  --name "$CONTAINER_NAME" \
  --cpus 4 \
  -v "$PROJECT_DIR/results:/app/results" \
  "$IMAGE_NAME" \
  python -u experiments/run_comparison.py \
    --runs 30 \
    --instances berlin52 eil51 kroA100 \
    --decades-multiplier 100 \
    --workers 4 \
    --parallel-level run

echo ""
echo "=== Verify parallel mode in logs ==="
echo "  You MUST see: 'Multi-Core v2' and 'Distributing 270 runs'"
echo "  If you see 'Running SBA...' only → OLD code still running!"
echo ""
echo "Follow logs (live):"
echo "  sudo docker logs -f $CONTAINER_NAME"
echo ""
echo "Check if still running:"
echo "  sudo docker ps"
echo ""
echo "Results saved in:"
echo "  $PROJECT_DIR/results/"
echo ""
echo "Stop container:"
echo "  sudo docker stop $CONTAINER_NAME"
