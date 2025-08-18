# Operational Runbooks
## AI-Enhanced Web Scraping & Data Collection System

### Table of Contents
1. [Incident Response Procedures](#incident-response-procedures)
2. [Performance Issue Resolution](#performance-issue-resolution)
3. [Database Operations](#database-operations)
4. [AI Service Management](#ai-service-management)
5. [Scraping Engine Operations](#scraping-engine-operations)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Security Incident Response](#security-incident-response)
8. [Capacity Management](#capacity-management)

---

## Incident Response Procedures

### Severity Levels

#### P1 - Critical (Response: Immediate)
- Complete system outage
- Data corruption or loss
- Security breach
- Critical AI service failures affecting all users

#### P2 - High (Response: < 1 hour)
- Significant performance degradation
- Partial system unavailability
- High error rates (>10%)
- Single AI service failures

#### P3 - Medium (Response: < 4 hours)
- Minor performance issues
- Non-critical feature unavailability
- Moderate error rates (5-10%)

#### P4 - Low (Response: < 24 hours)
- Minor bugs or issues
- Enhancement requests
- Low error rates (<5%)

### General Incident Response Process

#### 1. Detection and Alert
```bash
# Check overall system health
curl https://yourdomain.com/api/production/health

# Check recent errors
curl https://yourdomain.com/api/production/errors/stats

# Check system metrics
curl https://yourdomain.com/api/production/metrics
```

#### 2. Assessment and Triage
```bash
# Get comprehensive status
curl https://yourdomain.com/api/production/status

# Check component-specific health
curl https://yourdomain.com/api/production/health/database
curl https://yourdomain.com/api/production/health/ai_services
curl https://yourdomain.com/api/production/health/scraping_engine
```

#### 3. Immediate Stabilization
```bash
# Restart services if needed
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Check service status
sudo supervisorctl status

# Monitor logs in real-time
tail -f /var/log/ai-scraping/application.log | jq '.'
```

#### 4. Investigation and Resolution
```bash
# Check recent error patterns
curl https://yourdomain.com/api/production/errors/dashboard

# Review performance metrics
curl https://yourdomain.com/api/production/performance/metrics

# Check system resources
htop
iotop
df -h
```

#### 5. Communication and Documentation
- Update status page
- Notify stakeholders
- Document incident details
- Create post-incident review

---

## Performance Issue Resolution

### High CPU Usage

#### Investigation Steps
```bash
# Check current CPU usage
curl https://yourdomain.com/api/production/metrics | jq '.cpu_percent'

# Identify top CPU consumers
top -c
ps aux --sort=-%cpu | head -10

# Check for runaway processes
pgrep -f "python|node" | xargs ps -o pid,pcpu,pmem,time,cmd -p
```

#### Resolution Steps
```bash
# Scale backend workers if needed
sudo supervisorctl stop backend
# Edit supervisor config to increase workers
sudo nano /etc/supervisor/conf.d/scraping-api.conf
# Change: --workers 4 to --workers 2 (reduce if overloaded)
sudo supervisorctl start backend

# Check scraping job load
curl https://yourdomain.com/api/scraping/queue-status

# Pause high-resource scraping jobs if needed
curl -X PUT "https://yourdomain.com/api/scraping/jobs/{job_id}/pause"
```

### High Memory Usage

#### Investigation Steps
```bash
# Check memory usage
curl https://yourdomain.com/api/production/metrics | jq '.memory_percent'
free -h

# Identify memory consumers
ps aux --sort=-%mem | head -10

# Check for memory leaks
sudo netstat -tulpn | grep :8001  # Backend connections
sudo netstat -tulpn | grep :3000  # Frontend connections
```

#### Resolution Steps
```bash
# Restart services to clear memory
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Clear system caches if safe
sudo sync && sudo sysctl vm.drop_caches=1

# Monitor memory usage trends
curl https://yourdomain.com/api/production/metrics/history?hours=6
```

### Database Performance Issues

#### Investigation Steps
```bash
# Check database health
curl https://yourdomain.com/api/production/health/database

# Connect to MongoDB and check performance
mongo production_scraping_db --eval "
db.serverStatus().connections;
db.serverStatus().opcounters;
db.currentOp({active: true});
"

# Check slow queries
mongo production_scraping_db --eval "
db.setProfilingLevel(2, {slowms: 100});
db.system.profile.find().sort({ts: -1}).limit(5);
"
```

#### Resolution Steps
```bash
# Kill long-running operations if needed
mongo production_scraping_db --eval "
db.currentOp({active: true, secs_running: {$gte: 60}}).inprog.forEach(
  function(op) {
    if (op.secs_running > 60) db.killOp(op.opid);
  }
);
"

# Restart MongoDB if necessary
sudo systemctl restart mongod

# Reindex collections if needed
mongo production_scraping_db --eval "
db.enhanced_questions.reIndex();
db.scraping_jobs.reIndex();
"
```

### AI Service Performance Issues

#### Investigation Steps
```bash
# Check AI service health
curl https://yourdomain.com/api/production/health/ai_services

# Check AI processing performance
curl https://yourdomain.com/api/production/performance/metrics | jq '.performance_metrics'

# Test AI services individually
curl -X POST "https://yourdomain.com/api/ai-questions/generate" \
  -H "Content-Type: application/json" \
  -d '{"category": "logical", "difficulty": "medium", "count": 1}'
```

#### Resolution Steps
```bash
# Restart backend to reset AI connections
sudo supervisorctl restart backend

# Check API key validity
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
print('Gemini Key:', len(os.getenv('GEMINI_API_KEY', '')))
print('Groq Key:', len(os.getenv('GROQ_API_KEY', '')))
print('HF Token:', len(os.getenv('HUGGINGFACE_API_TOKEN', '')))
"

# Test network connectivity to AI services
ping -c 3 generativelanguage.googleapis.com
ping -c 3 api.groq.com
ping -c 3 huggingface.co
```

---

## Database Operations

### Backup Operations

#### Daily Backup
```bash
#!/bin/bash
# /opt/scripts/daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/daily"
DB_NAME="production_scraping_db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
mongodump --db $DB_NAME --out $BACKUP_DIR/$DATE

# Compress backup
cd $BACKUP_DIR
tar -czf backup_$DATE.tar.gz $DATE
rm -rf $DATE

# Upload to cloud storage (if configured)
# aws s3 cp backup_$DATE.tar.gz s3://your-backup-bucket/daily/

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

#### Restore Operations
```bash
# List available backups
ls -la /backups/daily/

# Restore from specific backup
BACKUP_FILE="/backups/daily/backup_20241201_120000.tar.gz"
RESTORE_DIR="/tmp/restore"

# Extract backup
mkdir -p $RESTORE_DIR
cd $RESTORE_DIR
tar -xzf $BACKUP_FILE

# Restore database (WARNING: This will overwrite existing data)
mongorestore --db production_scraping_db --drop $RESTORE_DIR/*/production_scraping_db/

# Verify restoration
mongo production_scraping_db --eval "
print('Collections:', db.getCollectionNames());
print('Enhanced Questions:', db.enhanced_questions.count());
print('Scraping Jobs:', db.scraping_jobs.count());
"
```

### Index Management

#### Check Index Usage
```javascript
// Connect to MongoDB
use production_scraping_db;

// Check index usage statistics
db.enhanced_questions.aggregate([{$indexStats: {}}]);
db.scraping_jobs.aggregate([{$indexStats: {}}]);
db.raw_extracted_questions.aggregate([{$indexStats: {}}]);
```

#### Rebuild Indexes
```bash
# Rebuild all indexes for a collection
mongo production_scraping_db --eval "
db.enhanced_questions.reIndex();
print('Enhanced questions indexes rebuilt');

db.scraping_jobs.reIndex();
print('Scraping jobs indexes rebuilt');

db.raw_extracted_questions.reIndex();
print('Raw questions indexes rebuilt');
"
```

### Data Maintenance

#### Clean Old Data
```javascript
// Remove old scraping jobs (older than 30 days)
use production_scraping_db;

db.scraping_jobs.deleteMany({
  created_at: {$lt: new Date(Date.now() - 30*24*60*60*1000)},
  status: {$in: ["COMPLETED", "FAILED"]}
});

// Archive old raw questions (move to archive collection)
db.raw_extracted_questions.find({
  extracted_at: {$lt: new Date(Date.now() - 60*24*60*60*1000)}
}).forEach(function(doc) {
  db.archived_raw_questions.insert(doc);
});

// Remove archived questions from main collection
db.raw_extracted_questions.deleteMany({
  extracted_at: {$lt: new Date(Date.now() - 60*24*60*60*1000)}
});
```

---

## AI Service Management

### Service Health Monitoring

#### Check AI Service Status
```bash
# Overall AI service health
curl https://yourdomain.com/api/production/health/ai_services

# Test individual services
python3 << 'EOF'
import os
import asyncio
from ai_services.gemini_service import GeminiService
from ai_services.groq_service import GroqService

async def test_services():
    try:
        # Test Gemini
        gemini = GeminiService()
        await gemini.initialize()
        print("✅ Gemini service: OK")
    except Exception as e:
        print(f"❌ Gemini service: {e}")
    
    try:
        # Test Groq
        groq = GroqService()
        await groq.initialize()
        print("✅ Groq service: OK")
    except Exception as e:
        print(f"❌ Groq service: {e}")

asyncio.run(test_services())
EOF
```

#### API Rate Limit Management
```bash
# Check current API usage (implement based on service)
python3 << 'EOF'
import requests
import os

# Check Gemini quota (if API supports it)
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print("Gemini API Key configured:", len(gemini_key))

# Check Groq rate limits
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    print("Groq API Key configured:", len(groq_key))

# Check HuggingFace token
hf_token = os.getenv('HUGGINGFACE_API_TOKEN')
if hf_token:
    print("HuggingFace Token configured:", len(hf_token))
EOF
```

### Service Recovery Procedures

#### AI Service Restart
```bash
# Restart backend to reinitialize AI services
sudo supervisorctl restart backend

# Wait for initialization
sleep 10

# Test AI functionality
curl -X POST "https://yourdomain.com/api/ai-questions/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "quantitative",
    "difficulty": "medium",
    "count": 1,
    "company_focus": "google"
  }'
```

#### API Key Rotation
```bash
# 1. Update .env file with new keys
sudo nano /app/backend/.env

# 2. Restart services
sudo supervisorctl restart backend

# 3. Verify new keys work
curl https://yourdomain.com/api/production/health/ai_services

# 4. Test AI endpoints
curl -X POST "https://yourdomain.com/api/ai-questions/instant-feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is 2+2?",
    "user_answer": "4",
    "correct_answer": "4"
  }'
```

---

## Scraping Engine Operations

### Job Management

#### Monitor Active Jobs
```bash
# Check queue status
curl https://yourdomain.com/api/scraping/queue-status

# List all jobs
curl https://yourdomain.com/api/scraping/jobs

# Get specific job details
curl https://yourdomain.com/api/scraping/jobs/{job_id}
```

#### Emergency Job Control
```bash
# Stop all running jobs
for job_id in $(curl -s https://yourdomain.com/api/scraping/jobs | jq -r '.jobs[].id'); do
  curl -X PUT "https://yourdomain.com/api/scraping/jobs/$job_id/stop"
  echo "Stopped job: $job_id"
done

# Clear job queue
curl -X DELETE "https://yourdomain.com/api/scraping/jobs/queue/clear"
```

#### Restart Scraping Engine
```bash
# Check scraping engine health
curl https://yourdomain.com/api/production/health/scraping_engine

# Restart backend (includes scraping engine)
sudo supervisorctl restart backend

# Verify scraping engine status
curl https://yourdomain.com/api/scraping/system-status
```

### Performance Optimization

#### Concurrent Job Adjustment
```bash
# Check current system load
curl https://yourdomain.com/api/production/metrics

# Adjust concurrent job limits based on load
python3 << 'EOF'
import requests
import json

# Get current metrics
response = requests.get('https://yourdomain.com/api/production/metrics')
metrics = response.json()

cpu_usage = metrics['cpu_percent']
memory_usage = metrics['memory_percent']

# Determine optimal job count
if cpu_usage > 80 or memory_usage > 80:
    max_jobs = 2
    print("High resource usage - limiting to 2 concurrent jobs")
elif cpu_usage > 60 or memory_usage > 60:
    max_jobs = 3
    print("Moderate resource usage - limiting to 3 concurrent jobs")
else:
    max_jobs = 5
    print("Normal resource usage - allowing 5 concurrent jobs")

# Update configuration would be done via API if implemented
print(f"Recommended max concurrent jobs: {max_jobs}")
EOF
```

---

## Monitoring and Alerting

### Alert Configuration

#### CPU Alert Setup
```bash
# Create CPU monitoring script
cat << 'EOF' > /opt/scripts/cpu_monitor.sh
#!/bin/bash
CPU_THRESHOLD=85
CURRENT_CPU=$(curl -s https://yourdomain.com/api/production/metrics | jq -r '.cpu_percent')

if (( $(echo "$CURRENT_CPU > $CPU_THRESHOLD" | bc -l) )); then
  curl -X POST "https://yourdomain.com/api/production/errors/capture" \
    -H "Content-Type: application/json" \
    -d "{
      \"message\": \"High CPU usage detected: ${CURRENT_CPU}%\",
      \"category\": \"system\",
      \"severity\": \"high\",
      \"context\": {\"cpu_percent\": $CURRENT_CPU, \"threshold\": $CPU_THRESHOLD}
    }"
  
  echo "$(date): High CPU alert sent - ${CURRENT_CPU}%" >> /var/log/alerts.log
fi
EOF

chmod +x /opt/scripts/cpu_monitor.sh

# Add to crontab (check every 5 minutes)
echo "*/5 * * * * /opt/scripts/cpu_monitor.sh" | sudo crontab -u root -
```

#### Error Rate Monitoring
```bash
# Create error rate monitoring script
cat << 'EOF' > /opt/scripts/error_monitor.sh
#!/bin/bash
ERROR_THRESHOLD=10
CURRENT_ERROR_RATE=$(curl -s https://yourdomain.com/api/production/errors/stats | jq -r '.error_rate_1h')

if (( $(echo "$CURRENT_ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )); then
  curl -X POST "https://yourdomain.com/api/production/errors/capture" \
    -H "Content-Type: application/json" \
    -d "{
      \"message\": \"High error rate detected: ${CURRENT_ERROR_RATE} errors/min\",
      \"category\": \"application\",
      \"severity\": \"critical\",
      \"context\": {\"error_rate_1h\": $CURRENT_ERROR_RATE, \"threshold\": $ERROR_THRESHOLD}
    }"
  
  echo "$(date): High error rate alert sent - ${CURRENT_ERROR_RATE}" >> /var/log/alerts.log
fi
EOF

chmod +x /opt/scripts/error_monitor.sh
echo "*/10 * * * * /opt/scripts/error_monitor.sh" | sudo crontab -u root -
```

### Log Analysis

#### Error Pattern Analysis
```bash
# Analyze error patterns from last 24 hours
python3 << 'EOF'
import json
import requests
from collections import defaultdict, Counter
from datetime import datetime, timedelta

# Get error dashboard data
response = requests.get('https://yourdomain.com/api/production/errors/dashboard')
data = response.json()

# Analyze top errors
print("=== TOP ERRORS ===")
for error in data['top_errors'][:5]:
    print(f"Count: {error['count']}, Severity: {error['severity']}")
    print(f"Message: {error['message'][:100]}...")
    print(f"Last seen: {error['last_seen']}")
    print("-" * 50)

# Analyze error trends
print("\n=== ERROR STATISTICS ===")
stats = data['statistics']
print(f"Total unique errors: {stats['total_unique_errors']}")
print(f"Total occurrences: {stats['total_occurrences']}")
print(f"Error rate (1h): {stats['error_rate_1h']:.2f} errors/min")

print("\n=== SEVERITY BREAKDOWN ===")
for severity, count in stats['severity_breakdown'].items():
    print(f"{severity}: {count}")

print("\n=== CATEGORY BREAKDOWN ===")
for category, count in stats['category_breakdown'].items():
    print(f"{category}: {count}")
EOF
```

#### Performance Analysis
```bash
# Analyze performance trends
python3 << 'EOF'
import requests
import json
from datetime import datetime

# Get performance metrics
response = requests.get('https://yourdomain.com/api/production/performance/metrics')
metrics = response.json()

print("=== PERFORMANCE ANALYSIS ===")
print(f"Total endpoints tracked: {metrics['total_endpoints']}")

print("\n=== ENDPOINT PERFORMANCE ===")
for endpoint, data in metrics['performance_metrics'].items():
    print(f"Endpoint: {endpoint}")
    print(f"  Average duration: {data['average_duration_ms']:.2f}ms")
    print(f"  Total requests: {data['count']}")
    print(f"  Error rate: {data['error_rate']:.2%}")
    print(f"  Total errors: {data['total_errors']}")
    print("-" * 40)
EOF
```

---

## Security Incident Response

### Security Alert Investigation

#### Authentication Failures
```bash
# Check recent authentication events
grep "authentication.*false" /var/log/ai-scraping/security.log | tail -20

# Analyze failed login patterns
python3 << 'EOF'
import re
import json
from collections import defaultdict, Counter

# Parse security logs (mock example - adapt to actual log format)
failed_attempts = defaultdict(list)

# This would parse actual log files in production
print("=== AUTHENTICATION FAILURE ANALYSIS ===")
print("Implementation needed based on actual security log format")
print("Check /var/log/ai-scraping/security.log for patterns")
EOF
```

#### Suspicious Activity Detection
```bash
# Check for rate limiting violations
curl https://yourdomain.com/api/production/errors/dashboard | \
  jq '.top_errors[] | select(.category == "rate_limiting")'

# Check for unusual API usage patterns
tail -100 /var/log/ai-scraping/security.log | \
  grep "rate_limit_violation\|suspicious_activity"
```

#### Security Incident Response Steps

1. **Immediate Assessment**
```bash
# Check system security status
curl https://yourdomain.com/api/production/health
curl https://yourdomain.com/api/production/errors/stats

# Check active connections
netstat -an | grep :8001 | wc -l
netstat -an | grep :3000 | wc -l
```

2. **Containment**
```bash
# Block suspicious IPs (if identified)
# sudo ufw deny from SUSPICIOUS_IP

# Temporarily increase rate limiting
# Update nginx configuration and reload
sudo nginx -t && sudo nginx -s reload
```

3. **Investigation**
```bash
# Review logs for suspicious patterns
grep -E "(error|warning|critical)" /var/log/ai-scraping/security.log | tail -50

# Check for unauthorized access attempts
grep -i "unauthorized\|forbidden\|denied" /var/log/nginx/access.log | tail -20
```

---

## Capacity Management

### Resource Planning

#### CPU Capacity Assessment
```bash
# Get CPU usage trends
curl "https://yourdomain.com/api/production/metrics/history?hours=24" | \
  jq '.metrics[] | {timestamp: .timestamp, cpu: .cpu_percent}'

# Calculate average CPU usage
python3 << 'EOF'
import requests
import json

response = requests.get('https://yourdomain.com/api/production/metrics/history?hours=24')
data = response.json()

if data['metrics']:
    cpu_values = [m['cpu_percent'] for m in data['metrics']]
    avg_cpu = sum(cpu_values) / len(cpu_values)
    max_cpu = max(cpu_values)
    
    print(f"24h Average CPU: {avg_cpu:.1f}%")
    print(f"24h Peak CPU: {max_cpu:.1f}%")
    
    if avg_cpu > 60:
        print("⚠️  Consider scaling up CPU resources")
    elif avg_cpu < 30:
        print("ℹ️  CPU resources may be over-provisioned")
    else:
        print("✅ CPU utilization is optimal")
else:
    print("No CPU metrics available")
EOF
```

#### Memory Capacity Assessment
```bash
# Memory usage analysis
python3 << 'EOF'
import requests
import json

response = requests.get('https://yourdomain.com/api/production/metrics/history?hours=24')
data = response.json()

if data['metrics']:
    memory_values = [m['memory_percent'] for m in data['metrics']]
    avg_memory = sum(memory_values) / len(memory_values)
    max_memory = max(memory_values)
    
    print(f"24h Average Memory: {avg_memory:.1f}%")
    print(f"24h Peak Memory: {max_memory:.1f}%")
    
    if avg_memory > 75:
        print("⚠️  Consider increasing memory allocation")
    elif max_memory > 90:
        print("❌ Memory peaks are critical - immediate scaling needed")
    else:
        print("✅ Memory utilization is acceptable")
else:
    print("No memory metrics available")
EOF
```

### Scaling Recommendations

#### Horizontal Scaling
```bash
# Check if load balancing would help
python3 << 'EOF'
import requests

# Get current performance metrics
response = requests.get('https://yourdomain.com/api/production/performance/metrics')
metrics = response.json()

print("=== SCALING ANALYSIS ===")
high_traffic_endpoints = []

for endpoint, data in metrics['performance_metrics'].items():
    if data['count'] > 1000 and data['average_duration_ms'] > 1000:
        high_traffic_endpoints.append((endpoint, data))
        
if high_traffic_endpoints:
    print("High traffic endpoints that could benefit from scaling:")
    for endpoint, data in high_traffic_endpoints:
        print(f"  {endpoint}: {data['count']} requests, {data['average_duration_ms']:.1f}ms avg")
    print("\nRecommendation: Consider horizontal scaling with load balancer")
else:
    print("Current load doesn't require horizontal scaling")
EOF
```

#### Vertical Scaling
```bash
# Resource utilization assessment
curl https://yourdomain.com/api/production/metrics | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)

cpu = data['cpu_percent']
memory = data['memory_percent']
disk = data['disk_percent']

print(f'Current Resource Utilization:')
print(f'  CPU: {cpu:.1f}%')
print(f'  Memory: {memory:.1f}%')
print(f'  Disk: {disk:.1f}%')

if cpu > 80 or memory > 80:
    print('\n⚠️  SCALING RECOMMENDATION: Increase resources')
    if cpu > 80:
        print('  - Add more CPU cores')
    if memory > 80:
        print('  - Increase memory allocation')
elif cpu < 40 and memory < 40:
    print('\nℹ️  Resources appear over-provisioned')
else:
    print('\n✅ Resource allocation is appropriate')
"
```

---

## Emergency Contacts and Escalation

### Contact Information
- **On-Call Engineer**: [phone/email]
- **System Administrator**: [phone/email]
- **Database Administrator**: [phone/email]
- **Security Team**: [security@yourdomain.com]
- **Management Escalation**: [management@yourdomain.com]

### Escalation Matrix

| Severity | Initial Response | Escalation Time | Escalation Contact |
|----------|------------------|-----------------|-------------------|
| P1 (Critical) | On-Call Engineer | Immediate | System Administrator + Management |
| P2 (High) | On-Call Engineer | 30 minutes | System Administrator |
| P3 (Medium) | Support Team | 2 hours | Team Lead |
| P4 (Low) | Support Team | Next business day | Team Lead |

### Emergency Procedures Checklist

#### P1 Critical Incident Response
- [ ] Acknowledge incident within 5 minutes
- [ ] Execute immediate stabilization procedures
- [ ] Notify management and stakeholders
- [ ] Begin investigation and resolution
- [ ] Provide updates every 15 minutes
- [ ] Document incident details
- [ ] Conduct post-incident review

---

*Document Version: 2.0.0*
*Last Updated: [Current Date]*
*Next Review: [Review Date]*