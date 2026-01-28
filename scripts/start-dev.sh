#!/bin/bash
# ==============================================================================
# ProctorWise - Script de démarrage développement
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=========================================="
echo "  ProctorWise - Démarrage dev"
echo "=========================================="

# Démarrer l'infrastructure avec docker-compose.dev.yml
echo "[1/3] Démarrage de l'infrastructure..."
docker compose -f docker-compose.dev.yml up -d

echo "[2/3] Attente que les services soient prêts..."
sleep 10

# Vérifier que MariaDB est prêt
echo "    - Vérification MariaDB..."
until docker exec proctorwise-mariadb-dev healthcheck.sh --connect --innodb_initialized 2>/dev/null; do
    echo "    - MariaDB pas encore prêt, attente..."
    sleep 2
done
echo "    - MariaDB OK"

# Vérifier que Kafka est prêt
echo "    - Vérification Kafka..."
until docker exec proctorwise-kafka-dev kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null; do
    echo "    - Kafka pas encore prêt, attente..."
    sleep 2
done
echo "    - Kafka OK"

echo "[3/3] Infrastructure prête!"
echo ""
echo "=========================================="
echo "  Services disponibles:"
echo "=========================================="
echo "  MariaDB:    localhost:3306"
echo "  Kafka:      localhost:9092"
echo "  Kafka UI:   http://localhost:8080"
echo "  MailHog:    http://localhost:8025"
echo "  Adminer:    http://localhost:8083"
echo "=========================================="
echo ""
echo "Pour lancer un microservice:"
echo "  cd userservice && uvicorn main:app --reload --port 8001"
echo "  cd reservationservice && uvicorn main:app --reload --port 8000"
echo "  cd monitoringservice && uvicorn main:app --reload --port 8003"
echo "  cd correctionservice && uvicorn main:app --reload --port 8004"
echo "  cd notificationservice && uvicorn main:app --reload --port 8005"
echo "  cd analyticsservice && uvicorn main:app --reload --port 8006"
echo ""
