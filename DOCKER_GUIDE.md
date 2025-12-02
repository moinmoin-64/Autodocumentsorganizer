# Docker & Kubernetes Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available

### Build and Run
```bash
# Build the image
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

The application will be available at `http://localhost:5001`

### With Monitoring (Prometheus)
```bash
docker-compose --profile monitoring up -d
```

Prometheus available at `http://localhost:9090`

---

## Production Deployment with Kubernetes

### Prerequisites
- Kubernetes cluster (minikube, GKE, EKS, AKS, etc.)
- kubectl configured
- Container registry access

### Step 1: Build and Push Image
```bash
# Build image
docker build -t organisationsai:latest .

# Tag for your registry
docker tag organisationsai:latest your-registry/organisationsai:latest

# Push to registry
docker push your-registry/organisationsai:latest
```

### Step 2: Update Deployment
Edit `k8s/deployment.yml` and update the image:
```yaml
image: your-registry/organisationsai:latest
```

### Step 3: Deploy to Kubernetes
```bash
# Create persistent volumes
kubectl apply -f k8s/pvc.yml

# Deploy Redis
kubectl apply -f k8s/redis.yml

# Deploy application
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml

# Check status
kubectl get pods
kubectl get services
```

### Step 4: Access Application
```bash
# Get external IP (LoadBalancer)
kubectl get service organisationsai-service

# Port forward (for testing)
kubectl port-forward svc/organisationsai-service 5001:80
```

---

## Environment Variables

### Docker Compose
Set in `docker-compose.yml`:
```yaml
environment:
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - FLASK_ENV=production
```

### Kubernetes
Create ConfigMap:
```bash
kubectl create configmap app-config \
  --from-literal=REDIS_HOST=redis-service \
  --from-literal=REDIS_PORT=6379
```

---

## Monitoring & Health Checks

### Health Endpoint
```bash
curl http://localhost:5001/health
```

### Metrics (Prometheus)
```bash
curl http://localhost:5001/metrics
```

### Logs
Docker:
```bash
docker-compose logs -f app
```

Kubernetes:
```bash
kubectl logs -f deployment/organisationsai
```

---

## Scaling

### Docker Compose
```bash
docker-compose up -d --scale app=3
```

### Kubernetes
```bash
kubectl scale deployment organisationsai --replicas=5

# Auto-scaling
kubectl autoscale deployment organisationsai \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs organisationsai

# Or in Kubernetes
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Connection issues
- Ensure Redis is running and accessible
- Check network configuration
- Verify environment variables

### Performance issues
- Increase resource limits in deployment.yml
- Check Redis memory usage
- Monitor with Prometheus

---

## Production Checklist

- [ ] Build with proper version tag
- [ ] Configure persistent volumes
- [ ] Set resource limits
- [ ] Enable monitoring
- [ ] Configure backups
- [ ] Set up log aggregation
- [ ] Enable HTTPS/TLS
- [ ] Configure secrets management
- [ ] Set up CI/CD pipeline
- [ ] Test disaster recovery
