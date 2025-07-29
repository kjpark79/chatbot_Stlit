#!/usr/bin/env python3
"""
Streamlit 애플리케이션 실행 스크립트
"""
import subprocess
import sys
import os

def main():
    """Streamlit 애플리케이션 실행"""
    try:
        # 환경변수 확인
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️  경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            print("   .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        
        print("🚀 밀양시 AI 어시스턴트를 시작합니다...")
        print("📝 브라우저에서 http://localhost:8501 으로 접속하세요")
        
        # Streamlit 애플리케이션 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 애플리케이션을 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()