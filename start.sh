#!/bin/bash

# Cloudtype 배포용 시작 스크립트
echo "🚀 Starting RAG Chatbot on Cloudtype..."

# 필요한 디렉토리 생성
mkdir -p documents data

# Streamlit 실행
streamlit run streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=${PORT:-8501} \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false