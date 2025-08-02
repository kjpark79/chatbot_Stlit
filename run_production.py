#!/usr/bin/env python3
"""
배포용 Streamlit 애플리케이션 실행 스크립트
"""
import subprocess
import sys
import os

def main():
    """배포용 Streamlit 애플리케이션 실행"""
    try:
        print("🚀 밀양시 AI 어시스턴트를 배포 모드로 시작합니다...")
        
        # 배포 환경용 Streamlit 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--global.config", ".streamlit/config.prod.toml"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 애플리케이션을 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()