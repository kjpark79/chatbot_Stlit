# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 필요한 안내를 제공합니다.

## 🛠️ 환경 설정 및 개발 명령어

### 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows
# 또는 source .venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 수정하여 OPENAI_API_KEY 추가
```

### 애플리케이션 실행

#### Streamlit 버전 (권장)
```bash
# 방법 1: 직접 실행
streamlit run streamlit_app.py

# 방법 2: 실행 스크립트 사용
python run_streamlit.py

# 서버가 http://localhost:8501 에서 실행됩니다
```

#### Flask 버전 (레거시)
```bash
python app.py
# 서버가 http://localhost:5000 에서 실행됩니다
```

### 필수 환경변수
- `OPENAI_API_KEY`: OpenAI API 호출에 필요 (임베딩 및 채팅 완성)

## 🏗️ 프로젝트 구조도

```
ragchatbot_Stlit/
├── 📄 streamlit_app.py          # Streamlit 메인 애플리케이션 (권장)
├── 📄 app.py                    # Flask 메인 애플리케이션 (레거시)
├── 📄 run_streamlit.py          # Streamlit 실행 스크립트
├── 📄 requirements.txt          # Python 패키지 의존성
├── 📄 .env.example             # 환경변수 설정 예시
├── 📄 CLAUDE.md                # 이 파일
├── 📁 utils/                    # 핵심 비즈니스 로직 모듈
│   ├── 🐍 __init__.py
│   ├── 🐍 document_processor.py  # 문서 처리 및 텍스트 추출
│   ├── 🐍 vector_store.py        # ChromaDB 벡터 데이터베이스 관리
│   └── 🐍 chat_handler.py        # OpenAI API 및 RAG 로직
├── 📁 templates/                # HTML 템플릿
│   └── 🌐 index.html            # 메인 웹 인터페이스
├── 📁 static/                   # 프론트엔드 정적 파일
│   ├── 🎨 style.css             # CSS 스타일시트
│   └── 📜 script.js             # JavaScript 기능
├── 📁 documents/                # 업로드된 문서 저장소
│   └── 📄 *.pdf, *.txt         # 사용자 업로드 파일
└── 📁 data/                     # ChromaDB 데이터베이스 파일
    ├── 🗄️ chroma.sqlite3       # 메타데이터 저장
    └── 📊 벡터 인덱스 파일들    # 임베딩 벡터 저장
```

## 🏛️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    🌐 웹 브라우저 (사용자)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP 요청/응답
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                🖥️ Flask 웹 애플리케이션                      │
│                     (app.py)                               │
├─────────────────────┬───────────────────────────────────────┤
│ 📤 파일 업로드       │ 💬 채팅 API      │ 📋 문서 목록 API    │
│ /upload             │ /chat           │ /documents         │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  🧠 비즈니스 로직 레이어                     │
├─────────────────────┬─────────────────┬───────────────────┤
│ 📄 DocumentProcessor │ 💾 VectorStore   │ 🤖 ChatHandler    │
│                     │                 │                   │
│ • PDF/TXT 파싱      │ • ChromaDB 관리  │ • 대화 기록 관리   │
│ • 텍스트 청킹       │ • 벡터 검색     │ • RAG 로직        │
│ • 전처리           │ • 임베딩 저장    │ • OpenAI 호출     │
└─────────────────────┼─────────────────┼───────────────────┘
                      │                 │
                      ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   🔌 외부 API 레이어                        │
├─────────────────────────────────────────────────────────────┤
│ 🤖 OpenAI API                    │ 💾 ChromaDB              │
│ • text-embedding-ada-002         │ • 로컬 벡터 데이터베이스   │
│ • gpt-3.5-turbo                  │ • 코사인 유사도 검색       │
│ • 임베딩 생성                    │ • 영구 저장              │
│ • 텍스트 생성                    │                         │
└─────────────────────────────────────────────────────────────┘
```

## 📖 아키텍처 개요

이 프로젝트는 Flask로 구축된 RAG(Retrieval-Augmented Generation) 챗봇으로, 사용자가 문서를 업로드하고 해당 문서에 대해 질문할 수 있게 해줍니다. OpenAI 임베딩을 사용한 문서 벡터화와 GPT를 통한 응답 생성을 활용합니다.

### 핵심 컴포넌트

**Flask 애플리케이션 (`app.py`)**
- 파일 업로드, 채팅, 문서 관리를 위한 라우트가 있는 메인 웹서버
- 대화 기록을 위한 세션 관리 처리
- 한글 파일명 지원하는 파일 업로드 관리
- 시작시 `documents/` 및 `data/` 디렉토리 생성

**문서 처리기 (`utils/document_processor.py`)**
- PDF 및 TXT 파일 텍스트 추출 처리
- 청킹을 위해 RecursiveCharacterTextSplitter 사용 (기본값: 1000자, 200자 중복)
- 한글 텍스트 파일을 위한 UTF-8 및 CP949 인코딩 지원

**벡터 저장소 (`utils/vector_store.py`)**
- 코사인 유사도를 사용하는 ChromaDB persistent client 관리
- text-embedding-ada-002를 사용한 OpenAI 임베딩 생성 처리
- 메타데이터(소스 파일명, chunk_id)와 함께 문서 청크 저장
- 상위 k개 유사 문서를 반환하는 검색 기능 제공

**채팅 핸들러 (`utils/chat_handler.py`)**
- 메모리가 있는 대화 세션 관리 (최근 10개 대화 턴 유지)
- RAG 파이프라인 구현: 관련 문서 검색, 컨텍스트 구축, 응답 생성
- 한국어 문서 Q&A에 최적화된 시스템 프롬프트와 함께 GPT-3.5-turbo 사용
- 프론트엔드 렌더링을 위해 마크다운 형식으로 응답 포맷

### 🔄 데이터 플로우

1. **문서 업로드**: 파일 → DocumentProcessor → VectorStore (OpenAI 임베딩을 통해) → ChromaDB
2. **채팅 쿼리**: 사용자 메시지 → VectorStore 검색 → 컨텍스트 구축 → OpenAI GPT → 마크다운 응답
3. **세션 관리**: 각 브라우저 세션마다 고유 ID 부여, 세션별 대화 기록 유지

### 프론트엔드 아키텍처

- **모던 UI**: 한글 타이포그래피(Noto Sans KR)와 함께 Bootstrap 5 + 커스텀 CSS
- **실시간 채팅**: JavaScript가 AJAX 호출, 마크다운 렌더링(marked.js + DOMPurify) 처리
- **파일 업로드**: 진행 표시기가 있는 커스텀 드래그 앤 드롭 인터페이스
- **반응형 디자인**: 전문적인 프레젠테이션 스타일링으로 모바일 친화적

### 주요 설정

- 최대 파일 크기: 16MB
- 지원 파일 형식: PDF, TXT
- ChromaDB 컬렉션: 코사인 유사도를 사용하는 "documents"
- 문서 청크: 200자 중복으로 1000자
- 채팅 컨텍스트: 세션당 최근 10개 대화 턴
- OpenAI 모델: text-embedding-ada-002 (임베딩), gpt-3.5-turbo (채팅)

### 데이터베이스 저장소

- `data/`: SQLite 메타데이터가 있는 ChromaDB 영구 저장소
- `documents/`: 보안 파일명으로 저장된 업로드 파일
- 세션 기반 대화 기록은 메모리에 저장 (영구적이지 않음)

### 밀양시 브랜딩 특징

- 헤더에 "밀양시 AI 어시스턴트" 브랜딩
- 챗봇 메시지에 도시 아이콘 사용
- 사용자 메시지에 사용자 아이콘 사용
- 전문적인 프레젠테이션을 위한 그라데이션 및 모던 디자인