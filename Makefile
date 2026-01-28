# ==============================================================================
# ProctorWise - Makefile
# ==============================================================================

.PHONY: help dev dev-up dev-down dev-logs full full-up full-down full-logs reset clean

# Couleurs
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
NC     := \033[0m

help: ## Affiche cette aide
	@echo "$(CYAN)ProctorWise - Commandes disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ==============================================================================
# Mode Développement (infrastructure légère)
# ==============================================================================

dev: dev-up ## Alias pour dev-up

dev-up: ## Démarre l'infrastructure de développement
	@echo "$(YELLOW)Démarrage de l'infrastructure de développement...$(NC)"
	docker compose -f docker-compose.dev.yml up -d
	@echo "$(GREEN)Infrastructure prête!$(NC)"
	@echo ""
	@echo "Services disponibles:"
	@echo "  MariaDB:    localhost:3306"
	@echo "  Kafka:      localhost:9092"
	@echo "  Kafka UI:   http://localhost:8080"
	@echo "  MailHog:    http://localhost:8025"
	@echo "  Adminer:    http://localhost:8083"

dev-down: ## Arrête l'infrastructure de développement
	@echo "$(YELLOW)Arrêt de l'infrastructure de développement...$(NC)"
	docker compose -f docker-compose.dev.yml down

dev-logs: ## Affiche les logs de l'infrastructure de développement
	docker compose -f docker-compose.dev.yml logs -f

# ==============================================================================
# Mode Complet (tout conteneurisé)
# ==============================================================================

full: full-up ## Alias pour full-up

full-up: ## Démarre la stack complète
	@echo "$(YELLOW)Démarrage de la stack complète...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Stack complète prête!$(NC)"

full-down: ## Arrête la stack complète
	@echo "$(YELLOW)Arrêt de la stack complète...$(NC)"
	docker compose down

full-logs: ## Affiche les logs de la stack complète
	docker compose logs -f

full-build: ## Rebuild et démarre la stack complète
	docker compose up -d --build

# ==============================================================================
# Services individuels
# ==============================================================================

user: ## Lance UserService localement
	cd userservice && uvicorn main:app --reload --port 8001

reservation: ## Lance ReservationService localement
	cd reservationservice && uvicorn main:app --reload --port 8000

monitoring: ## Lance MonitoringService localement
	cd monitoringservice && uvicorn main:app --reload --port 8003

correction: ## Lance CorrectionService localement
	cd correctionservice && uvicorn main:app --reload --port 8004

notification: ## Lance NotificationService localement
	cd notificationservice && uvicorn main:app --reload --port 8005

analytics: ## Lance AnalyticsService localement
	cd analyticsservice && uvicorn main:app --reload --port 8006

# ==============================================================================
# Utilitaires
# ==============================================================================

reset: ## Reset complet (supprime les données)
	@echo "$(YELLOW)ATTENTION: Ceci va supprimer toutes les données!$(NC)"
	@read -p "Appuyez sur Enter pour continuer ou Ctrl+C pour annuler"
	docker compose -f docker-compose.dev.yml down -v
	docker compose down -v
	@echo "$(GREEN)Reset terminé!$(NC)"

clean: ## Nettoie les fichiers temporaires Python
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)Nettoyage terminé!$(NC)"

status: ## Affiche l'état des conteneurs
	docker compose ps
	docker compose -f docker-compose.dev.yml ps

# ==============================================================================
# Kafka
# ==============================================================================

kafka-topics: ## Liste les topics Kafka
	docker exec proctorwise-kafka-dev kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || \
	docker exec proctorwise-kafka kafka-topics --list --bootstrap-server localhost:9092

# ==============================================================================
# Base de données
# ==============================================================================

db-shell: ## Ouvre un shell MySQL
	docker exec -it proctorwise-mariadb-dev mysql -u proctorwise -pproctorwise_secret 2>/dev/null || \
	docker exec -it proctorwise-mariadb mysql -u proctorwise -pproctorwise_secret
