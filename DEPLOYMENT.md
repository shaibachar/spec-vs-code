# Deployment Guide

This guide covers deploying the Spec Compliance Checker Service to various environments.

## Table of Contents

- [Docker Compose Deployment](#docker-compose-deployment)
- [Standalone Docker Deployment](#standalone-docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)

## Docker Compose Deployment

The easiest way to deploy the service is using Docker Compose.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ disk space

### Steps

1. **Prepare the environment**:

```bash
# Clone repository
git clone https://github.com/shaibachar/spec-vs-code.git
cd spec-vs-code

# Create .env file
cp .env.example .env
```

2. **Configure environment variables**:

Edit `.env` and set:
- `GIT_TOKEN`: Your Git access token
- `SPEC_REPO_URL`: URL where TODO.md files will be committed
- `API_KEY`: Secure API key for authentication
- Other optional settings

3. **Start the services**:

```bash
docker-compose up -d
```

4. **Verify deployment**:

```bash
# Check service status
docker-compose ps

# Check service health
curl http://localhost:8080/api/v1/health

# View logs
docker-compose logs -f
```

5. **Initialize Ollama model** (first time):

The model will be automatically pulled on first startup. Monitor progress:

```bash
docker-compose logs -f ollama-init
```

### Production Recommendations

For production deployments:

1. **Use Docker secrets** for sensitive data:

```yaml
# docker-compose.override.yml
services:
  spec-checker:
    secrets:
      - git_token
      - api_key
    environment:
      - GIT_TOKEN_FILE=/run/secrets/git_token
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  git_token:
    external: true
  api_key:
    external: true
```

2. **Enable restart policies**:

Already configured as `restart: unless-stopped`

3. **Set resource limits**:

```yaml
services:
  spec-checker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
  
  ollama:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          memory: 4G
```

4. **Use external volumes**:

```yaml
volumes:
  ollama-data:
    driver: local
    driver_opts:
      type: none
      device: /data/ollama
      o: bind
```

## Standalone Docker Deployment

Deploy service and Ollama separately.

### 1. Deploy Ollama

```bash
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama-data:/root/.ollama \
  ollama/ollama:latest

# Pull model
docker exec ollama ollama pull codellama:7b-instruct
```

### 2. Deploy Spec Checker

```bash
# Build image
docker build -t spec-checker:latest .

# Run container
docker run -d \
  --name spec-checker \
  -p 8080:8080 \
  -e OLLAMA_HOST=http://ollama:11434 \
  -e OLLAMA_MODEL=codellama:7b-instruct \
  -e GIT_TOKEN=your_token \
  -e SPEC_REPO_URL=https://github.com/your/repo.git \
  -e API_KEY=your_api_key \
  --link ollama:ollama \
  spec-checker:latest
```

## Cloud Deployment

### AWS ECS Deployment

1. **Create ECR repositories**:

```bash
aws ecr create-repository --repository-name spec-checker
aws ecr create-repository --repository-name ollama
```

2. **Push images**:

```bash
# Build and tag
docker build -t spec-checker:latest .
docker tag spec-checker:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/spec-checker:latest

# Push
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/spec-checker:latest
```

3. **Create ECS task definition**:

```json
{
  "family": "spec-checker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "containerDefinitions": [
    {
      "name": "ollama",
      "image": "ollama/ollama:latest",
      "memory": 6144,
      "portMappings": [
        {
          "containerPort": 11434,
          "protocol": "tcp"
        }
      ]
    },
    {
      "name": "spec-checker",
      "image": "$AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/spec-checker:latest",
      "memory": 2048,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OLLAMA_HOST",
          "value": "http://localhost:11434"
        }
      ],
      "secrets": [
        {
          "name": "GIT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:spec-checker/git-token"
        }
      ]
    }
  ]
}
```

### Google Cloud Run

Cloud Run may have limitations due to resource requirements and stateful nature.

Consider using **Google Compute Engine** or **GKE** instead:

```bash
# Create VM
gcloud compute instances create spec-checker \
  --machine-type=n1-standard-4 \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --metadata-from-file=startup-script=startup.sh

# startup.sh contains docker-compose installation and service startup
```

### Azure Container Instances

```bash
az container create \
  --resource-group spec-checker-rg \
  --name spec-checker \
  --image spec-checker:latest \
  --cpu 2 \
  --memory 8 \
  --port 8080 \
  --environment-variables \
    OLLAMA_HOST=http://localhost:11434 \
  --secure-environment-variables \
    GIT_TOKEN=$GIT_TOKEN \
    API_KEY=$API_KEY
```

## Configuration

### Persistent Configuration

Create `config/config.local.yaml` to override defaults:

```yaml
analysis:
  depth: deep
  max_repo_size_mb: 2048

ollama:
  model: codellama:13b-instruct
  temperature: 0.05

service:
  max_concurrent_checks: 5
```

### Environment-Specific Settings

Use environment variables to override configuration:

```bash
# Development
export LOG_LEVEL=DEBUG
export ANALYSIS_DEPTH=quick

# Production
export LOG_LEVEL=INFO
export ANALYSIS_DEPTH=standard
export MAX_CONCURRENT_CHECKS=10
```

## Monitoring

### Health Checks

The service exposes a health endpoint:

```bash
curl http://localhost:8080/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T04:09:29Z",
  "ollama_status": "connected",
  "ollama_model": "codellama:7b-instruct"
}
```

### Logging

View logs:

```bash
# Docker Compose
docker-compose logs -f spec-checker
docker-compose logs -f ollama

# Standalone Docker
docker logs -f spec-checker
docker logs -f ollama
```

### Metrics (Future)

Consider adding Prometheus metrics:

```yaml
# Add Prometheus exporter
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## Backup and Recovery

### Backup Ollama Models

Models are stored in Docker volumes:

```bash
# Backup
docker run --rm \
  -v ollama-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/ollama-data.tar.gz /data

# Restore
docker run --rm \
  -v ollama-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/ollama-data.tar.gz -C /
```

### Backup Configuration

```bash
# Backup .env and configs
tar czf config-backup.tar.gz .env config/
```

### Disaster Recovery

1. **Save configuration files**: `.env`, `config/`, `docker-compose.yml`
2. **Document custom settings**: API keys, Git tokens
3. **Backup Ollama volumes**: Models take time to download
4. **Test recovery process**: Periodically test restoring from backups

## Scaling

### Horizontal Scaling

Deploy multiple instances behind a load balancer:

```yaml
# docker-compose.scale.yml
services:
  spec-checker:
    deploy:
      replicas: 3
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

**Note**: Each instance needs its own Ollama or share one Ollama instance.

### Vertical Scaling

Increase resources for better performance:

```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
```

## Security Hardening

### 1. Use Non-Root User

Already configured in Dockerfile:
```dockerfile
USER specchecker
```

### 2. Network Isolation

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  spec-checker:
    networks:
      - frontend
      - backend
  
  ollama:
    networks:
      - backend  # Not exposed publicly
```

### 3. Secret Management

Use Docker secrets or external secret managers:

```bash
# Create secrets
echo "my-git-token" | docker secret create git_token -
echo "my-api-key" | docker secret create api_key -
```

### 4. Regular Updates

```bash
# Update images
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### Service Won't Start

1. Check logs: `docker-compose logs`
2. Verify environment variables are set
3. Check port 8080 is not in use
4. Verify Docker has enough resources

### Ollama Not Responding

1. Check if container is running: `docker-compose ps`
2. Verify model is loaded: `docker-compose exec ollama ollama list`
3. Check memory usage: `docker stats`

### Out of Memory

Increase Docker memory limits or use smaller Ollama model:

```env
OLLAMA_MODEL=codellama:7b-instruct  # Instead of 13b or 34b
```

### Slow Performance

- Use SSD for Docker volumes
- Allocate more CPU/RAM to Ollama
- Reduce `MAX_CONCURRENT_CHECKS`
- Use smaller model or `quick` analysis depth

## Maintenance

### Regular Tasks

1. **Update models**: `docker-compose exec ollama ollama pull codellama:7b-instruct`
2. **Clean up old workspaces**: Handled automatically
3. **Review logs**: Check for errors or warnings
4. **Monitor disk usage**: Clean up Docker images/volumes periodically

### Upgrading

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## Support

For deployment issues:
- Check logs first
- Review documentation in `spec/` folder
- Open issue on GitHub with deployment details
