# 🚀 RAG 챗봇 배포 가이드

## 1. 로컬 환경 배포

### 환경 설정
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# OpenAI API 키 설정 (필수)
OPENAI_API_KEY=your_openai_api_key_here
```

### 애플리케이션 실행
```bash
# Streamlit 앱 실행 (권장)
streamlit run streamlit_app.py

# 또는 실행 스크립트 사용
python run_streamlit.py
```

## 2. 클라우드 배포 옵션

### A. Streamlit Cloud 배포 (가장 간단)

1. **GitHub 저장소 준비**
   ```bash
   git add .
   git commit -m "Deploy ready"
   git push origin main
   ```

2. **Streamlit Cloud 설정**
   - [share.streamlit.io](https://share.streamlit.io) 접속
   - GitHub 연동 후 저장소 선택
   - `streamlit_app.py` 지정
   - Secrets에 `OPENAI_API_KEY` 추가

3. **자동 배포**
   - 코드 변경시 자동 재배포
   - HTTPS 도메인 자동 제공

### B. Heroku 배포

1. **Heroku 파일 추가**
   ```bash
   # Procfile 생성
   echo "web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
   
   # runtime.txt 생성
   echo "python-3.9.16" > runtime.txt
   ```

2. **Heroku 배포**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your_key
   git push heroku main
   ```

### C. Docker 컨테이너 배포

1. **Dockerfile 생성**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
   ```

2. **빌드 및 실행**
   ```bash
   # 이미지 빌드
   docker build -t rag-chatbot .
   
   # 컨테이너 실행
   docker run -p 8501:8501 -e OPENAI_API_KEY=your_key rag-chatbot
   ```

### D. AWS EC2 배포

1. **EC2 인스턴스 설정**
   ```bash
   # 패키지 업데이트
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   
   # 애플리케이션 코드 복사
   git clone your-repo
   cd ragchatbot_Stlit
   
   # 가상환경 설정
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **시스템 서비스 설정**
   ```bash
   # systemd 서비스 파일 생성
   sudo nano /etc/systemd/system/ragchatbot.service
   ```
   
   ```ini
   [Unit]
   Description=RAG Chatbot
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ragchatbot_Stlit
   Environment=PATH=/home/ubuntu/ragchatbot_Stlit/.venv/bin
   Environment=OPENAI_API_KEY=your_key
   ExecStart=/home/ubuntu/ragchatbot_Stlit/.venv/bin/streamlit run streamlit_app.py --server.port=8501
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Nginx 리버스 프록시**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### E. Google Cloud Platform (GCP) 배포

1. **App Engine 설정**
   ```yaml
   # app.yaml 파일 생성
   runtime: python39
   
   env_variables:
     OPENAI_API_KEY: "your_key_here"
   
   handlers:
   - url: /.*
     script: auto
   ```

2. **GCP 배포**
   ```bash
   # Google Cloud SDK 설치 후
   gcloud app deploy
   ```

### F. Azure Container Instances 배포

1. **Azure CLI로 배포**
   ```bash
   # 리소스 그룹 생성
   az group create --name ragchatbot-rg --location eastus
   
   # 컨테이너 인스턴스 생성
   az container create \
     --resource-group ragchatbot-rg \
     --name ragchatbot \
     --image your-docker-image \
     --dns-name-label ragchatbot-unique \
     --ports 8501 \
     --environment-variables OPENAI_API_KEY=your_key
   ```

## 3. 배포 체크리스트

### 필수 확인사항
- ✅ OpenAI API 키 설정
- ✅ 의존성 패키지 설치
- ✅ 포트 설정 (기본: 8501)
- ✅ 파일 업로드 디렉토리 권한
- ✅ 환경변수 보안 설정

### 성능 최적화
- ✅ ChromaDB 데이터 영구 저장
- ✅ 파일 크기 제한 (16MB)
- ✅ 메모리 사용량 모니터링
- ✅ 로그 관리 설정

### 보안 고려사항
- ✅ API 키 환경변수 관리
- ✅ 파일 업로드 검증
- ✅ HTTPS 설정 (프로덕션)
- ✅ 접근 제한 설정

## 4. 환경별 설정 가이드

### 개발 환경
```bash
# 개발용 설정
export FLASK_ENV=development
export DEBUG=True
streamlit run streamlit_app.py --server.runOnSave=true
```

### 스테이징 환경
```bash
# 스테이징용 설정
export FLASK_ENV=staging
export DEBUG=False
streamlit run streamlit_app.py --server.port=8502
```

### 프로덕션 환경
```bash
# 프로덕션용 설정
export FLASK_ENV=production
export DEBUG=False
streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501
```

## 5. 모니터링 및 유지보수

### 로그 확인
```bash
# 애플리케이션 로그
tail -f app.log

# 시스템 서비스 로그 (Linux)
sudo journalctl -u ragchatbot -f

# Docker 컨테이너 로그
docker logs -f ragchatbot
```

### 성능 모니터링
```bash
# 메모리 사용량 확인
ps aux | grep streamlit

# 디스크 사용량 확인
du -sh data/ documents/

# 네트워크 연결 확인
netstat -tulpn | grep 8501
```

### 데이터 백업
```bash
# ChromaDB 데이터 백업
tar -czf backup_$(date +%Y%m%d).tar.gz data/ documents/

# 정기 백업 스크립트 (crontab)
0 2 * * * /path/to/backup_script.sh
```

### 업데이트 및 유지보수
```bash
# 의존성 업데이트
pip list --outdated
pip install --upgrade package_name

# 애플리케이션 재시작
sudo systemctl restart ragchatbot  # Linux 서비스
docker restart ragchatbot          # Docker 컨테이너
```

## 6. 트러블슈팅

### 일반적인 문제 해결

**문제 1: OpenAI API 키 오류**
```bash
# 환경변수 확인
echo $OPENAI_API_KEY
# .env 파일 확인
cat .env
```

**문제 2: 포트 충돌**
```bash
# 포트 사용 확인
lsof -i :8501
# 다른 포트로 실행
streamlit run streamlit_app.py --server.port=8502
```

**문제 3: 메모리 부족**
```bash
# 메모리 사용량 확인
free -h
# ChromaDB 캐시 정리
rm -rf data/chroma.sqlite3-*
```

**문제 4: 파일 업로드 실패**
```bash
# 디렉토리 권한 확인
ls -la documents/
# 권한 설정
chmod 755 documents/
```

## 7. 보안 강화 가이드

### SSL/TLS 설정
```nginx
# Nginx SSL 설정
server {
    listen 443 ssl;
    ssl_certificate /path/to/certificate.pem;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8501;
    }
}
```

### 방화벽 설정
```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### API 키 보안
```bash
# AWS Systems Manager Parameter Store 사용
aws ssm put-parameter \
  --name "/ragchatbot/openai-api-key" \
  --value "your-api-key" \
  --type "SecureString"
```

이 배포 가이드를 따라하시면 로컬부터 클라우드까지 다양한 환경에서 RAG 챗봇을 성공적으로 배포할 수 있습니다.