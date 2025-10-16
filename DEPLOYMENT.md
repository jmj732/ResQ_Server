# AWS EC2 배포 가이드

## 📋 사전 준비사항

### 1. AWS EC2 인스턴스 생성
- **운영체제**: Ubuntu 22.04 LTS
- **인스턴스 타입**: t2.micro 이상 (t2.small 권장)
- **보안 그룹 설정**:
  - SSH (포트 22): 내 IP
  - HTTP (포트 80): 0.0.0.0/0
  - HTTPS (포트 443): 0.0.0.0/0 (SSL 사용 시)
  - MySQL (포트 3306): 필요시 (내부용은 제한)

### 2. 필수 파일 확인
```bash
FastAPIProject/
├── main.py
├── requirements.txt
├── .env.example
├── deploy.sh
└── app/
```

---

## 🚀 배포 방법

### 방법 1: 자동 배포 스크립트 사용 (권장)

#### 1단계: EC2 접속
```bash
ssh -i "your-key.pem" ubuntu@YOUR_EC2_IP
```

#### 2단계: 프로젝트 업로드
```bash
# 로컬에서 실행
scp -i "your-key.pem" -r /Users/jjm/Desktop/FastAPIProject ubuntu@YOUR_EC2_IP:/home/ubuntu/
```

#### 3단계: 배포 스크립트 실행
```bash
# EC2에서 실행
cd /home/ubuntu/FastAPIProject
chmod +x deploy.sh
./deploy.sh
```

#### 4단계: 환경변수 설정
```bash
nano .env
```

`.env` 파일 수정:
```env
# Database
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/interview_db

# JWT Security
SECRET_KEY=YOUR_STRONG_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# AI Service
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

# CORS
CORS_ORIGINS=*
```

#### 5단계: 서비스 재시작
```bash
sudo systemctl restart fastapi
```

---

### 방법 2: 수동 배포

#### 1. 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Python 및 필수 패키지 설치
```bash
sudo apt install -y python3-pip python3-venv nginx mysql-server
```

#### 3. 프로젝트 설정
```bash
cd /home/ubuntu/FastAPIProject
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. MySQL 데이터베이스 설정
```bash
sudo mysql
```

MySQL에서:
```sql
CREATE DATABASE interview_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fastapi'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';
GRANT ALL PRIVILEGES ON interview_db.* TO 'fastapi'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 5. systemd 서비스 생성
```bash
sudo nano /etc/systemd/system/fastapi.service
```

내용:
```ini
[Unit]
Description=FastAPI Interview Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/FastAPIProject
Environment="PATH=/home/ubuntu/FastAPIProject/venv/bin"
ExecStart=/home/ubuntu/FastAPIProject/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 6. Nginx 설정
```bash
sudo nano /etc/nginx/sites-available/fastapi
```

내용:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

활성화:
```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

#### 7. 서비스 시작
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
```

---

## 🔧 서비스 관리

### 서비스 제어
```bash
# 시작
sudo systemctl start fastapi

# 중지
sudo systemctl stop fastapi

# 재시작
sudo systemctl restart fastapi

# 상태 확인
sudo systemctl status fastapi
```

### 로그 확인
```bash
# 실시간 로그
sudo journalctl -u fastapi -f

# 최근 로그
sudo journalctl -u fastapi -n 100

# 에러만 보기
sudo journalctl -u fastapi -p err
```

### Nginx 로그
```bash
# 접속 로그
sudo tail -f /var/log/nginx/access.log

# 에러 로그
sudo tail -f /var/log/nginx/error.log
```

---

## 🔐 보안 설정

### 1. 방화벽 설정 (UFW)
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL/HTTPS 설정 (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. .env 파일 권한 설정
```bash
chmod 600 .env
```

---

## 📊 API 테스트

### 서버 접속
- **기본 URL**: `http://YOUR_EC2_IP`
- **Swagger 문서**: `http://YOUR_EC2_IP/docs`
- **ReDoc 문서**: `http://YOUR_EC2_IP/redoc`

### 헬스체크
```bash
curl http://YOUR_EC2_IP/docs
```

---

## 🐛 트러블슈팅

### 1. 서비스가 시작되지 않을 때
```bash
# 상세 로그 확인
sudo journalctl -u fastapi -xe

# Python 패키지 재설치
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 2. 데이터베이스 연결 오류
```bash
# MySQL 상태 확인
sudo systemctl status mysql

# 연결 테스트
mysql -u fastapi -p -h localhost interview_db
```

### 3. Nginx 502 Bad Gateway
```bash
# FastAPI 서비스 확인
sudo systemctl status fastapi

# Nginx 설정 테스트
sudo nginx -t

# 재시작
sudo systemctl restart fastapi nginx
```

### 4. 포트 충돌
```bash
# 8000번 포트 사용 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 PID
```

---

## 🔄 업데이트 방법

### 1. 코드 업데이트
```bash
# 로컬에서 EC2로 파일 전송
scp -i "your-key.pem" -r /Users/jjm/Desktop/FastAPIProject ubuntu@YOUR_EC2_IP:/home/ubuntu/

# EC2에서
cd /home/ubuntu/FastAPIProject
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fastapi
```

### 2. Git 사용 (추천)
```bash
# EC2에서
cd /home/ubuntu/FastAPIProject
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart fastapi
```

---

## 📈 성능 최적화

### 1. Gunicorn 사용 (프로덕션)
```bash
pip install gunicorn

# systemd 서비스 수정
ExecStart=/home/ubuntu/FastAPIProject/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. 로그 로테이션
```bash
sudo nano /etc/logrotate.d/fastapi
```

```
/var/log/fastapi/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0640 ubuntu ubuntu
}
```

---

## 📝 체크리스트

배포 전:
- [ ] `.env` 파일 설정 완료
- [ ] `requirements.txt` 최신화
- [ ] 보안 그룹 설정 확인
- [ ] 도메인 DNS 설정 (도메인 사용 시)

배포 후:
- [ ] API 동작 확인 (`/docs` 접속)
- [ ] 데이터베이스 연결 확인
- [ ] 로그 확인
- [ ] SSL 인증서 설치 (프로덕션)
- [ ] 모니터링 설정 (CloudWatch, Prometheus 등)

---

## 🆘 도움말

- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/deployment/
- **Nginx 설정**: https://nginx.org/en/docs/
- **Ubuntu 서버 관리**: https://ubuntu.com/server/docs
