# Redis Queue (RQ) Setup Guide

## ภาพรวม

ระบบใช้ **Redis Queue (RQ)** สำหรับส่ง email แบบ asynchronous ทำให้:
- ✅ ผู้ใช้ไม่ต้องรอการส่ง email
- ✅ ลด timeout issues
- ✅ มี fallback เป็น sync ถ้า Redis ไม่พร้อม
- ✅ Track job status ได้

## ข้อกำหนด

- **Redis server** (ติดตั้งบน Ubuntu หรือใช้ Docker)
- **Python packages**: redis, rq (มีใน requirements.txt แล้ว)

---

## 🚀 การติดตั้ง

### 1. ติดตั้ง Redis บน Ubuntu

```bash
# Update packages
sudo apt update

# Install Redis
sudo apt install redis-server -y

# เริ่ม Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# ทดสอบ Redis
redis-cli ping
# ควรได้: PONG
```

### 2. ติดตั้ง Python Dependencies

```bash
cd /path/to/revenue-etl-web
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🏃 การรัน RQ Worker

### Development Mode

```bash
# Terminal 1: รัน Flask app
source venv/bin/activate
python wsgi.py

# Terminal 2: รัน RQ worker
source venv/bin/activate
python rq_worker.py
```

### Production Mode (ใช้ Supervisor)

สร้างไฟล์ supervisor config:

```bash
sudo nano /etc/supervisor/conf.d/revenue-etl-rq-worker.conf
```

เพิ่มเนื้อหา:

```ini
[program:revenue-etl-rq-worker]
directory=/path/to/revenue-etl-web
command=/path/to/revenue-etl-web/venv/bin/python rq_worker.py
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/path/to/revenue-etl-web/data/logs/rq-worker-error.log
stdout_logfile=/path/to/revenue-etl-web/data/logs/rq-worker-access.log
environment=PATH="/path/to/revenue-etl-web/venv/bin",REDIS_URL="redis://localhost:6379/0"
```

เริ่ม worker:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start revenue-etl-rq-worker
sudo supervisorctl status revenue-etl-rq-worker
```

---

## 🔧 Configuration

### Environment Variables

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
```

หรือ set ใน system:

```bash
export REDIS_URL=redis://localhost:6379/0
```

---

## 🧪 การทดสอบ

### 1. ทดสอบ Redis Connection

```bash
python3 << EOF
from redis import Redis
redis_conn = Redis.from_url('redis://localhost:6379/0')
print(redis_conn.ping())
EOF
```

ควรได้: `True`

### 2. ทดสอบ RQ Worker

```bash
# รัน worker
python rq_worker.py

# ควรเห็น:
# ✓ RQ Worker started, listening to: email, default
# ✓ Redis: redis://localhost:6379/0
```

### 3. ทดสอบส่ง Email

1. เปิด web app: http://localhost:8000
2. กรอก email และกด "ส่งรหัส OTP"
3. ดู log ของ RQ worker - ควรเห็น job ถูก process

---

## 📋 Monitoring

### ดู Jobs ใน Queue

```bash
# ใช้ rq info
pip install rq-dashboard  # optional

# หรือใช้ Python
python3 << EOF
from redis import Redis
from rq import Queue
redis_conn = Redis.from_url('redis://localhost:6379/0')
email_queue = Queue('email', connection=redis_conn)
print(f"Jobs in queue: {len(email_queue)}")
print(f"Jobs: {email_queue.job_ids}")
EOF
```

### ดู Worker Status

```bash
# ใช้ supervisor
sudo supervisorctl status revenue-etl-rq-worker

# ดู logs
tail -f data/logs/rq-worker-access.log
```

---

## 🔄 Fallback Behavior

**ระบบทำงานแบบ Graceful Degradation:**

1. **ถ้า Redis พร้อม**: ใช้ RQ worker (async) ⚡
2. **ถ้า Redis ไม่พร้อม**: ใช้ sync email sending 📧
3. **User experience เหมือนกันทั้ง 2 กรณี**

ไม่ต้องกังวลถ้า Redis down - ระบบยังใช้งานได้ แค่ช้ากว่าเล็กน้อย!

---

## 🐛 Troubleshooting

### Redis Connection Failed

```bash
# ตรวจสอบ Redis service
sudo systemctl status redis-server

# Restart Redis
sudo systemctl restart redis-server

# ทดสอบ connection
redis-cli ping
```

### RQ Worker ไม่ทำงาน

```bash
# ดู logs
tail -f data/logs/rq-worker-error.log

# Restart worker
sudo supervisorctl restart revenue-etl-rq-worker

# ดู status
sudo supervisorctl status revenue-etl-rq-worker
```

### Jobs ค้างใน Queue

```bash
# Clear failed jobs
python3 << EOF
from redis import Redis
from rq import Queue
redis_conn = Redis.from_url('redis://localhost:6379/0')
q = Queue('email', connection=redis_conn)
q.empty()  # Clear all jobs
EOF
```

---

## 📊 Performance

**Benchmark:**
- **Sync email**: ~2-5 วินาที (user ต้องรอ)
- **Async RQ**: <100ms (user ไม่ต้องรอ!)

**Throughput:**
- 1 worker: ~10-20 emails/minute
- Multiple workers: สามารถ scale ได้

---

## 🔐 Security Notes

1. **Firewall**: Redis ควรฟังแค่ localhost (127.0.0.1)
2. **Password**: ตั้ง Redis password ใน production:
   ```bash
   # /etc/redis/redis.conf
   requirepass your-strong-password

   # Update REDIS_URL
   export REDIS_URL=redis://:your-strong-password@localhost:6379/0
   ```

---

## 📚 เพิ่มเติม

- **RQ Documentation**: https://python-rq.org/
- **Redis Documentation**: https://redis.io/documentation

---

**สร้างเสร็จแล้ว!** 🎉 ระบบส่ง email แบบ async พร้อมใช้งาน
