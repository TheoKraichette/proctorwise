#!/bin/bash
# ==============================================================================
# ProctorWise - VPS Setup Script for AlmaLinux 9
# ==============================================================================
# Usage: ssh root@YOUR_VPS_IP < scripts/setup-vps.sh
# Or:    ssh root@YOUR_VPS_IP
#        curl -sSL https://raw.githubusercontent.com/TheoKraichette/proctorwise/main/scripts/setup-vps.sh | bash
# ==============================================================================

set -e

echo "=============================="
echo "ProctorWise VPS Setup"
echo "=============================="

# 1. System update
echo "[1/8] Mise a jour du systeme..."
dnf update -y -q

# 2. Install utilities
echo "[2/8] Installation des utilitaires..."
dnf install -y -q git curl wget nano firewalld

# 3. Install Docker
echo "[3/8] Installation de Docker..."
dnf install -y -q dnf-plugins-core
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl start docker
systemctl enable docker

echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker compose version)"

# 4. Add swap (important for 8GB RAM VPS)
echo "[4/8] Configuration du swap (4GB)..."
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap cree: 4GB"
else
    echo "Swap deja configure"
fi

# Optimize swap usage
sysctl vm.swappiness=10
echo 'vm.swappiness=10' >> /etc/sysctl.conf

# 5. Configure firewall
echo "[5/8] Configuration du firewall..."
systemctl start firewalld
systemctl enable firewalld

# Ports necessaires
firewall-cmd --permanent --add-service=http      # 80 (Nginx)
firewall-cmd --permanent --add-service=https     # 443 (futur SSL)
firewall-cmd --permanent --add-service=ssh       # 22
firewall-cmd --permanent --add-port=8000/tcp     # ReservationService
firewall-cmd --permanent --add-port=8001/tcp     # UserService
firewall-cmd --permanent --add-port=8003/tcp     # MonitoringService
firewall-cmd --permanent --add-port=8004/tcp     # CorrectionService
firewall-cmd --permanent --add-port=8005/tcp     # NotificationService
firewall-cmd --permanent --add-port=8006/tcp     # AnalyticsService
firewall-cmd --reload

echo "Ports ouverts:"
firewall-cmd --list-ports
firewall-cmd --list-services

# 6. Generate SSH key for GitHub Actions
echo "[6/8] Generation de la cle SSH pour GitHub Actions..."
if [ ! -f /root/.ssh/github_actions ]; then
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f /root/.ssh/github_actions -N ""
    cat /root/.ssh/github_actions.pub >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
    echo ""
    echo "============================================"
    echo "CLE PRIVEE A COPIER DANS GITHUB SECRETS"
    echo "(Secret name: VPS_SSH_KEY)"
    echo "============================================"
    cat /root/.ssh/github_actions
    echo ""
    echo "============================================"
else
    echo "Cle SSH deja generee"
fi

# 7. Clone project
echo "[7/8] Clonage du projet..."
PROJECT_PATH="/opt/proctorwise"
if [ ! -d "$PROJECT_PATH/.git" ]; then
    mkdir -p "$PROJECT_PATH"
    git clone https://github.com/TheoKraichette/proctorwise.git "$PROJECT_PATH"
    echo "Projet clone dans $PROJECT_PATH"
else
    echo "Projet deja clone"
    cd "$PROJECT_PATH"
    git pull origin main
fi

# 8. Configure .env for production
echo "[8/8] Configuration de l'environnement..."
cd "$PROJECT_PATH"

# Detect public IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "YOUR_VPS_IP")

# Update .env with public IP
if grep -q "PUBLIC_HOST=" .env 2>/dev/null; then
    sed -i "s/PUBLIC_HOST=.*/PUBLIC_HOST=$PUBLIC_IP/" .env
else
    echo "PUBLIC_HOST=$PUBLIC_IP" >> .env
fi

echo ""
echo "=============================="
echo "Setup termine !"
echo "=============================="
echo ""
echo "IP publique detectee: $PUBLIC_IP"
echo ""
echo "Prochaines etapes:"
echo ""
echo "1. Configurez les GitHub Secrets:"
echo "   VPS_HOST     = $PUBLIC_IP"
echo "   VPS_USER     = root"
echo "   VPS_SSH_KEY  = (cle privee affichee ci-dessus)"
echo "   VPS_PORT     = 22"
echo ""
echo "2. Lancez les containers:"
echo "   cd $PROJECT_PATH"
echo "   docker compose up -d --build"
echo ""
echo "3. Verifiez les services:"
echo "   docker compose ps"
echo "   curl http://localhost:8001/health"
echo ""
echo "4. Accedez a l'application:"
echo "   http://$PUBLIC_IP:8001  (Login)"
echo "   http://$PUBLIC_IP:8000  (Examens)"
echo "   http://$PUBLIC_IP:8003  (Monitoring)"
echo "   http://$PUBLIC_IP:8006  (Analytics)"
echo "   http://$PUBLIC_IP       (Login via Nginx)"
echo ""
