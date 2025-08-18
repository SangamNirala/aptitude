# Production Deployment Guide
## AI-Enhanced Web Scraping & Data Collection System

### Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Setup](#database-setup)
4. [Security Configuration](#security-configuration)
5. [Monitoring & Logging](#monitoring--logging)
6. [Deployment Steps](#deployment-steps)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

---

## Prerequisites

### System Requirements
- **CPU**: Minimum 2 cores, Recommended 4+ cores
- **Memory**: Minimum 4GB RAM, Recommended 8GB+ RAM
- **Disk**: Minimum 20GB available space
- **Network**: Stable internet connection with minimum 10Mbps
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Dependencies
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- Nginx (for reverse proxy)
- Supervisord (for process management)

### API Keys Required
- **Gemini API Key**: For AI question generation
- **Groq API Key**: For ultra-fast AI feedback
- **HuggingFace Token**: For semantic analysis and duplicate detection

---

## Environment Configuration

### Production Environment Variables

Create `/app/backend/.env.production` with the following configuration:

```bash
# Environment Configuration
ENVIRONMENT=production
APP_NAME=ai-enhanced-scraping-system
APP_VERSION=2.0.0
DEBUG_MODE=false

# Database Configuration
MONGO_URL=mongodb://production-mongodb:27017
DB_NAME=production_scraping_db
DB_MAX_POOL_SIZE=100
DB_MIN_POOL_SIZE=20
DB_CONNECTION_TIMEOUT_MS=10000

# Security Configuration
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=1000
SESSION_TIMEOUT_MINUTES=60
MAX_REQUEST_SIZE_MB=10

# AI Service Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
AI_SERVICE_TIMEOUT_SECONDS=60
AI_SERVICE_RETRY_ATTEMPTS=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_DIRECTORY=/var/log/ai-scraping
ENABLE_STRUCTURED_LOGS=true
ENABLE_PERFORMANCE_LOGS=true
ENABLE_SECURITY_LOGS=true

# Performance Configuration
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT_SECONDS=30
WORKER_PROCESSES=4
MAX_MEMORY_MB=4096

# Monitoring Configuration
ENABLE_HEALTH_CHECKS=true
HEALTH_CHECK_INTERVAL_SECONDS=30
ENABLE_ERROR_TRACKING=true
ALERT_ON_ERROR_RATE_PERCENT=5.0
ALERT_ON_RESPONSE_TIME_MS=3000

# Scraping Configuration
MAX_CONCURRENT_SCRAPING_JOBS=10
SCRAPING_TIMEOUT_MINUTES=60
MAX_QUESTIONS_PER_JOB=5000
```

### Configuration Validation

Before deployment, validate your configuration:

```bash
cd /app/backend
python -c "
from config.production_config import validate_production_readiness
if validate_production_readiness():
    print('✅ Configuration is valid for production')
else:
    print('❌ Configuration validation failed')
    exit(1)
"
```

---

## Database Setup

### MongoDB Production Configuration

1. **Install MongoDB**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

2. **Create Production Database**:
```bash
mongo --eval "
use production_scraping_db;
db.createUser({
  user: 'scraping_user',
  pwd: 'secure_password_here',
  roles: [
    { role: 'readWrite', db: 'production_scraping_db' }
  ]
});
"
```

3. **Configure MongoDB for Production**:
```bash
# Edit /etc/mongod.conf
sudo nano /etc/mongod.conf

# Add these configurations:
security:
  authorization: enabled

net:
  port: 27017
  bindIp: 127.0.0.1

storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
```

4. **Create Database Indexes**:
The application will automatically create required indexes on startup, but you can manually create them:

```javascript
// Connect to MongoDB
use production_scraping_db;

// Question indexes
db.enhanced_questions.createIndex({"category": 1, "difficulty": 1, "is_active": 1});
db.enhanced_questions.createIndex({"ai_metrics.quality_score": -1});
db.enhanced_questions.createIndex({"metadata.company_patterns": 1});

// Scraping indexes
db.scraping_jobs.createIndex({"status": 1, "created_at": -1});
db.scraping_jobs.createIndex({"source_name": 1, "status": 1});
db.raw_extracted_questions.createIndex({"source": 1, "extracted_at": -1});

// Analytics indexes
db.question_attempts.createIndex({"question_id": 1, "timestamp": -1});
```

---

## Security Configuration

### 1. Firewall Setup
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (if using)
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MongoDB (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 27017
```

### 2. SSL/TLS Configuration
For production, configure SSL certificates:

```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### 3. Nginx Configuration
Create `/etc/nginx/sites-available/scraping-api`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # API specific settings
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        client_max_body_size 10M;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring & Logging

### 1. Log Directory Setup
```bash
# Create log directories
sudo mkdir -p /var/log/ai-scraping
sudo chown $USER:$USER /var/log/ai-scraping

# Setup log rotation
sudo nano /etc/logrotate.d/ai-scraping

# Add this configuration:
/var/log/ai-scraping/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 user user
    postrotate
        supervisorctl restart backend
    endscript
}
```

### 2. Monitoring Dashboard
The system provides built-in monitoring endpoints:

- **Health Status**: `GET /api/production/health`
- **System Metrics**: `GET /api/production/metrics`
- **Error Dashboard**: `GET /api/production/errors/dashboard`
- **Performance Metrics**: `GET /api/production/performance/metrics`

### 3. Alert Configuration
Configure alerts in your monitoring system:

```bash
# Example alert rules for CPU usage
curl -X POST "https://yourdomain.com/api/production/errors/capture" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test alert",
    "category": "system",
    "severity": "medium",
    "context": {"test": true}
  }'
```

---

## Deployment Steps

### 1. Pre-deployment Checklist
- [ ] All environment variables configured
- [ ] Database setup completed
- [ ] SSL certificates installed
- [ ] Nginx configured
- [ ] API keys obtained and validated
- [ ] Security settings configured
- [ ] Log directories created

### 2. Application Deployment
```bash
# 1. Clone/update application code
cd /app
git pull origin main  # Or your deployment branch

# 2. Install/update backend dependencies
cd backend
pip install -r requirements.txt

# 3. Install/update frontend dependencies
cd ../frontend
yarn install
yarn build

# 4. Start services with supervisord
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all
```

### 3. Supervisor Configuration
Create `/etc/supervisor/conf.d/scraping-api.conf`:

```ini
[program:backend]
command=/usr/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
directory=/app/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-scraping/backend.log
environment=ENVIRONMENT=production

[program:frontend]
command=/usr/bin/yarn start
directory=/app/frontend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai-scraping/frontend.log

[group:scraping-api]
programs=backend,frontend
priority=999
```

### 4. Deployment Verification
```bash
# Check service status
sudo supervisorctl status

# Test API endpoints
curl https://yourdomain.com/api/production/health
curl https://yourdomain.com/api/production/status

# Check logs
tail -f /var/log/ai-scraping/backend.log
tail -f /var/log/ai-scraping/application.log
```

---

## Health Checks

### Automated Health Monitoring
The system includes comprehensive health checks:

1. **System Resources**: CPU, Memory, Disk usage
2. **Database**: MongoDB connectivity and performance
3. **AI Services**: API key validation and service availability
4. **Scraping Engine**: Job queue status and performance

### Manual Health Check Commands
```bash
# Overall system health
curl https://yourdomain.com/api/production/health

# Specific component health
curl https://yourdomain.com/api/production/health/database
curl https://yourdomain.com/api/production/health/ai_services

# System metrics
curl https://yourdomain.com/api/production/metrics

# Performance test
curl -X POST https://yourdomain.com/api/production/performance/test
```

### Health Check Thresholds
- **CPU Usage**: Warning > 70%, Critical > 85%
- **Memory Usage**: Warning > 75%, Critical > 90%
- **Disk Usage**: Warning > 80%, Critical > 95%
- **Response Time**: Warning > 1000ms, Critical > 3000ms
- **Error Rate**: Warning > 5%, Critical > 10%

---

## Troubleshooting

### Common Issues

#### 1. Service Startup Failures
```bash
# Check supervisor logs
sudo supervisorctl tail backend stderr
sudo supervisorctl tail frontend stderr

# Check system logs
journalctl -u supervisor -f
```

#### 2. Database Connection Issues
```bash
# Test MongoDB connection
mongo --eval "db.adminCommand('ping')"

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Restart MongoDB
sudo systemctl restart mongod
```

#### 3. AI Service Failures
```bash
# Test AI service configuration
curl https://yourdomain.com/api/production/health/ai_services

# Check API key configuration
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Gemini:', bool(os.getenv('GEMINI_API_KEY')))
print('Groq:', bool(os.getenv('GROQ_API_KEY')))
print('HuggingFace:', bool(os.getenv('HUGGINGFACE_API_TOKEN')))
"
```

#### 4. High Resource Usage
```bash
# Check system resources
curl https://yourdomain.com/api/production/metrics

# Monitor processes
htop
iotop

# Check for memory leaks
ps aux --sort=-%mem | head -10
```

#### 5. Performance Issues
```bash
# Run performance diagnostics
curl -X POST https://yourdomain.com/api/production/performance/test

# Check error rates
curl https://yourdomain.com/api/production/errors/stats

# Monitor active jobs
curl https://yourdomain.com/api/scraping/queue-status
```

### Log Analysis

#### Application Logs
```bash
# Real-time application logs
tail -f /var/log/ai-scraping/application.log | jq '.'

# Error logs only
tail -f /var/log/ai-scraping/errors.log | jq '.'

# Performance logs
tail -f /var/log/ai-scraping/performance.log | jq '.'
```

#### Security Logs
```bash
# Security events
tail -f /var/log/ai-scraping/security.log | jq '.'

# Failed authentication attempts
grep "authentication.*false" /var/log/ai-scraping/security.log
```

---

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
- [ ] Check system health status
- [ ] Review error logs and rates
- [ ] Monitor resource usage
- [ ] Verify backup completion

#### Weekly Tasks
- [ ] Review performance metrics
- [ ] Update security patches
- [ ] Clean up old log files
- [ ] Review and resolve alerts

#### Monthly Tasks
- [ ] Update dependencies
- [ ] Review and update configurations
- [ ] Performance optimization review
- [ ] Disaster recovery testing

### Backup Procedures

#### Database Backup
```bash
# Create daily backup
mongodump --db production_scraping_db --out /backups/$(date +%Y%m%d)

# Compress backup
tar -czf /backups/backup-$(date +%Y%m%d).tar.gz /backups/$(date +%Y%m%d)

# Upload to cloud storage (example)
aws s3 cp /backups/backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

#### Configuration Backup
```bash
# Backup configuration files
tar -czf /backups/config-$(date +%Y%m%d).tar.gz \
  /app/backend/.env \
  /etc/nginx/sites-available/ \
  /etc/supervisor/conf.d/
```

### Update Procedures

#### Application Updates
```bash
# 1. Backup current version
cp -r /app /app-backup-$(date +%Y%m%d)

# 2. Update code
cd /app
git pull origin main

# 3. Update dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && yarn install && yarn build

# 4. Run tests
python -m pytest tests/

# 5. Restart services
sudo supervisorctl restart all

# 6. Verify deployment
curl https://yourdomain.com/api/production/health
```

#### Security Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip list --outdated
pip install --upgrade package_name

# Update Node.js packages
yarn outdated
yarn upgrade
```

### Performance Tuning

#### Database Optimization
```bash
# Analyze slow queries
db.setProfilingLevel(2, { slowms: 100 })

# Compact database
db.runCommand({ compact: 'collection_name' })

# Rebuild indexes
db.collection_name.reIndex()
```

#### Application Optimization
- Monitor memory usage patterns
- Optimize database queries
- Implement caching strategies
- Tune worker process counts
- Configure connection pooling

---

## Emergency Procedures

### Service Recovery
```bash
# Emergency restart
sudo supervisorctl restart all

# Check service status
sudo supervisorctl status

# View recent errors
tail -n 100 /var/log/ai-scraping/errors.log
```

### Database Recovery
```bash
# Restore from backup
mongorestore --db production_scraping_db /backups/latest/

# Check database integrity
mongo --eval "db.runCommand({validate: 'enhanced_questions'})"
```

### Rollback Procedures
```bash
# Rollback to previous version
cp -r /app-backup-YYYYMMDD/* /app/
sudo supervisorctl restart all
```

---

## Support and Contacts

- **Technical Support**: [support@yourdomain.com]
- **Emergency Contact**: [emergency@yourdomain.com]
- **Documentation**: [https://docs.yourdomain.com]
- **Status Page**: [https://status.yourdomain.com]

---

## Compliance and Security

### Data Protection
- All personal data encrypted at rest and in transit
- Regular security audits and penetration testing
- GDPR/CCPA compliance measures implemented
- Data retention policies enforced

### Monitoring and Alerting
- 24/7 system monitoring
- Automated alert notifications
- Performance baseline monitoring
- Security incident response procedures

---

*Last Updated: [Current Date]*
*Version: 2.0.0*