#!/bin/bash
# Deploy TSP-SBA on Sheikh server (2 workers, 2 vCPUs)
# Usage: bash sheikh-deploy.sh

set -e

PROJECT_DIR="$HOME/projet-tsp"
IMAGE_NAME="tsp-sba:latest"
CONTAINER_NAME="tsp-sba-run"
WORKERS=2
# TSP + 2-opt: ×20 decades (paper ×100 is for continuous functions, too slow for TSP)
DECADES_MULTIPLIER=20

echo "=== 1. Go to project directory ==="
cd "$PROJECT_DIR"

echo "=== 2. Pull latest code from GitHub ==="
git pull origin main

echo "=== 3. Add swap (prevents OOM with $WORKERS workers) ==="
if ! swapon --show | grep -q '/swapfile'; then
  if [ ! -f /swapfile ]; then
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
  fi
  sudo swapon /swapfile
  echo "Swap enabled:"
  free -h
else
  echo "Swap already active:"
  free -h
fi

echo "=== 4. Stop and remove old container (if exists) ==="
sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true

echo "=== 5. Build Docker image ==="
sudo docker build -t "$IMAGE_NAME" .

echo "=== 6. Run container ($WORKERS vCPUs, $WORKERS workers) ==="
mkdir -p "$PROJECT_DIR/results"
sudo chown -R "$USER:$USER" "$PROJECT_DIR/results" 2>/dev/null || true

CPUSET="0-$((WORKERS - 1))"

sudo docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --cpus "$WORKERS" \
  --cpuset-cpus="$CPUSET" \
  -e TSP_WORKERS="$WORKERS" \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -v "$PROJECT_DIR/results:/app/results" \
  "$IMAGE_NAME" \
  python -u experiments/run_comparison.py \
    --runs 30 \
    --instances berlin52 eil51 kroA100 \
    --decades-multiplier "$DECADES_MULTIPLIER" \
    --workers "$WORKERS"

echo ""
echo "=== Auto-resume enabled ==="
echo "  After server reboot, same container restarts and continues from last saved run."
echo "  Check progress: cat $PROJECT_DIR/results/active_experiment.txt"
echo "  Check last run:   cat $PROJECT_DIR/results/experiment_*/checkpoint_state.json"
echo "=== Done! $WORKERS workers on $WORKERS vCPUs ==="
echo ""
echo "Follow logs:"
echo "  sudo docker logs -f $CONTAINER_NAME"
echo ""
echo "Check CPUs (both should be busy):"
echo "  sudo docker stats $CONTAINER_NAME"
echo ""
echo "Check container running:"
echo "  sudo docker ps"
echo ""
echo "Results: $PROJECT_DIR/results/"
