#!/bin/bash

# FastAPI EC2 배포 스크립트

set -e

echo "===== FastAPI 서버 배포 시작 ====="

# 1. 시스템 업데이트
echo "1. 시스템 패키지 업데이트..."
sudo apt update
sudo apt upgrade -y

# 2. Python 및 필수 패키지 설치
echo "2. Python 및 필수 패키지 설치..."
sudo apt install -y python3-pip python3-venv nginx

# 3. MySQL 설치 (선택사항)
echo "3. MySQL 설치 (y/n)?"
read -p "MySQL을 설치하시겠습니까? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt install -y mysql-server
    sudo systemctl start mysql
    sudo systemctl enable mysql
fi

# 4. 프로젝트 디렉토리 설정
echo "4. 프로젝트 디렉토리 설정..."
PROJECT_DIR="/home/ubuntu/FastAPIProject"
mkdir -p $PROJECT_DIR

# 5. 가상환경 설정
echo "5. Python 가상환경 설정..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# 6. 의존성 설치
echo "6. 의존성 패키지 설치..."
pip install --upgrade pip
pip install -r requirements.txt

# 7. .env 파일 설정
echo "7. 환경변수 설정..."
if [ ! -f .env ]; then
    echo ".env 파일이 없습니다. .env.example을 참고하여 .env 파일을 생성하세요."
    cp .env.example .env
    echo ">>> .env 파일을 수정해주세요! <<<"
fi

# 8. systemd 서비스 파일 생성
echo "8. systemd 서비스 설정..."
sudo tee /etc/systemd/system/fastapi.service > /dev/null <<EOF
[Unit]
Description=FastAPI Interview Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 9. Nginx 설정 (리버스 프록시)
echo "9. Nginx 리버스 프록시 설정..."
sudo tee /etc/nginx/sites-available/fastapi > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 10. 서비스 시작
echo "10. FastAPI 서비스 시작..."
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi

# 11. 상태 확인
echo "11. 서비스 상태 확인..."
sudo systemctl status fastapi --no-pager

echo ""
echo "===== 배포 완료! ====="
echo ""
echo "서비스 관리 명령어:"
echo "  - 서비스 시작: sudo systemctl start fastapi"
echo "  - 서비스 중지: sudo systemctl stop fastapi"
echo "  - 서비스 재시작: sudo systemctl restart fastapi"
echo "  - 로그 확인: sudo journalctl -u fastapi -f"
echo ""
echo "API 접속: http://YOUR_EC2_IP"
echo "Swagger 문서: http://YOUR_EC2_IP/docs"
