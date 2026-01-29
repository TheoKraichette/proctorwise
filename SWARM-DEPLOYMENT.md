# ProctorWise - Docker Swarm Deployment

## Architecture

```
                    [Internet]
                        |
                    [Nginx LB]
                    /    |    \
        [UserService] [ReservationService] [MonitoringService] ...
              |              |                    |
           [MariaDB]     [Kafka]              [Kafka]
```

## Pre-requis

### Sur le VPS

```bash
# 1. Installer Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Initialiser Swarm
docker swarm init

# 3. Creer le repertoire
sudo mkdir -p /opt/proctorwise
sudo chown $USER:$USER /opt/proctorwise
```

### Secrets GitHub

Configurer dans **Settings > Secrets > Actions** :

| Secret | Description | Exemple |
|--------|-------------|---------|
| `VPS_HOST` | IP du VPS | `51.38.xxx.xxx` |
| `VPS_USER` | Utilisateur SSH | `ubuntu` |
| `VPS_SSH_KEY` | Cle privee SSH | `-----BEGIN OPENSSH...` |
| `VPS_PORT` | Port SSH (optionnel) | `22` |
| `DB_PASSWORD` | Mot de passe MariaDB | `strong_password_here` |
| `JWT_SECRET_KEY` | Cle secrete JWT | `64_char_random_string` |
| `SMTP_HOST` | Serveur SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Port SMTP | `587` |

## Deploiement

### Automatique (CI/CD)

Push sur la branche `main` ou `docker-swarm` :

```bash
git push origin docker-swarm
```

### Manuel

```bash
# Sur le VPS
cd /opt/proctorwise

# Deployer le stack
docker stack deploy -c docker-compose.swarm.yml proctorwise

# Verifier le statut
docker stack services proctorwise
```

## Commandes utiles

### Gestion du Stack

```bash
# Voir tous les services
docker stack services proctorwise

# Voir les logs d'un service
docker service logs proctorwise_userservice -f

# Voir les taches d'un service
docker service ps proctorwise_userservice

# Scaler un service
docker service scale proctorwise_userservice=3

# Mettre a jour un service
docker service update --image ghcr.io/user/proctorwise-userservice:latest proctorwise_userservice

# Rollback un service
docker service rollback proctorwise_userservice

# Supprimer le stack
docker stack rm proctorwise
```

### Monitoring

```bash
# Voir l'utilisation des ressources
docker stats

# Voir les noeuds du swarm
docker node ls

# Inspecter un service
docker service inspect proctorwise_userservice
```

## SSL/HTTPS

### Option 1: Let's Encrypt (Certbot)

```bash
# Installer certbot
sudo apt install certbot

# Obtenir un certificat
sudo certbot certonly --standalone -d proctorwise.example.com

# Copier les certificats
sudo cp /etc/letsencrypt/live/proctorwise.example.com/fullchain.pem /opt/proctorwise/docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/proctorwise.example.com/privkey.pem /opt/proctorwise/docker/nginx/ssl/

# Renouvellement auto (cron)
echo "0 0 1 * * certbot renew --quiet" | sudo crontab -
```

### Option 2: Certificat auto-signe (dev/test)

```bash
cd /opt/proctorwise/docker/nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=localhost"
```

## Configuration des replicas

Dans `docker-compose.swarm.yml`, ajuster selon la charge :

| Service | Replicas recommandes | Notes |
|---------|---------------------|-------|
| userservice | 2-3 | Auth, sessions |
| reservationservice | 2-3 | CRUD exams |
| monitoringservice | 2-4 | Charge ML, frames |
| correctionservice | 2 | Grading |
| notificationservice | 2 | Kafka consumer |
| analyticsservice | 1 | Reports |
| nginx | 1 | Load balancer |
| mariadb | 1 | Single master |
| kafka | 1 | Single broker |

## Rolling Updates

Les mises a jour se font sans downtime :

1. Swarm cree une nouvelle instance du service
2. Attend que le health check passe
3. Arrete l'ancienne instance
4. Repete pour chaque replica

Configuration dans le compose :

```yaml
deploy:
  update_config:
    parallelism: 1        # 1 instance a la fois
    delay: 10s            # Attendre 10s entre chaque
    failure_action: rollback
    order: start-first    # Demarre le nouveau avant d'arreter l'ancien
```

## Troubleshooting

### Service qui ne demarre pas

```bash
# Voir les erreurs
docker service ps proctorwise_userservice --no-trunc

# Voir les logs
docker service logs proctorwise_userservice
```

### Probleme de reseau

```bash
# Lister les reseaux
docker network ls

# Inspecter le reseau
docker network inspect proctorwise_proctorwise
```

### Probleme de volume

```bash
# Lister les volumes
docker volume ls

# Inspecter un volume
docker volume inspect proctorwise_mariadb_data
```

## Rollback d'urgence

```bash
# Rollback tous les services
for service in $(docker service ls --filter "label=com.docker.stack.namespace=proctorwise" -q); do
  docker service rollback $service
done

# Ou supprimer et redeployer
docker stack rm proctorwise
sleep 10
docker stack deploy -c docker-compose.swarm.yml proctorwise
```
