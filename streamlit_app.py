import streamlit as st
import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import uuid
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStore
from utils.chat_handler import ChatHandler

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Streamlit 페이지 설정
st.set_page_config(
    page_title="밀양시 AI 어시스턴트",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    .main {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .main-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .main-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        font-weight: 300;
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(4px);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 0;
        max-width: 80%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .sidebar-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .document-item {
        background: rgba(255, 255, 255, 0.8);
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4facfe;
    }
    
    .upload-area {
        border: 2px dashed #4facfe;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.1);
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 초기화
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

@st.cache_resource
def initialize_components():
    """컴포넌트 초기화 (캐시된 리소스)"""
    try:
        os.makedirs('documents', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        doc_processor = DocumentProcessor()
        vector_store = VectorStore()
        chat_handler = ChatHandler(vector_store)
        
        logger.info("Components initialized successfully")
        return doc_processor, vector_store, chat_handler
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        st.error(f"초기화 중 오류가 발생했습니다: {str(e)}")
        return None, None, None

def allowed_file(filename):
    """허용된 파일 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_session_id():
    """세션 ID 생성"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def main():
    # 컴포넌트 초기화
    doc_processor, vector_store, chat_handler = initialize_components()
    if not all([doc_processor, vector_store, chat_handler]):
        st.error("애플리케이션 초기화에 실패했습니다.")
        return
    
    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = generate_session_id()
    
    # 메인 헤더
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🤖 밀양시 AI 어시스턴트</h1>
        <p class="main-subtitle">문서를 업로드하고 AI와 대화해보세요</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.markdown('<div class="sidebar-container">', unsafe_allow_html=True)
        st.markdown("### 📂 문서 관리")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "📄 문서 업로드",
            type=['pdf', 'txt'],
            help="PDF 또는 TXT 파일을 업로드하세요 (최대 16MB)"
        )
        
        if uploaded_file is not None:
            if uploaded_file.size > MAX_FILE_SIZE:
                st.error(f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 업로드 가능합니다.")
            elif allowed_file(uploaded_file.name):
                with st.spinner("문서를 처리하고 있습니다..."):
                    try:
                        # 파일 저장
                        file_path = os.path.join('documents', uploaded_file.name)
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 문서 처리
                        chunks = doc_processor.process_document(file_path)
                        
                        if len(chunks) > 100:
                            st.error(f"파일이 너무 큽니다: {len(chunks)}개 청크 (최대 100개)")
                            os.remove(file_path)
                        else:
                            # 벡터 스토어에 추가
                            vector_store.add_documents(chunks, uploaded_file.name)
                            st.success(f"✅ {uploaded_file.name} 업로드 완료!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"문서 처리 중 오류가 발생했습니다: {str(e)}")
                        logger.error(f"Document processing error: {str(e)}")
            else:
                st.error("지원하지 않는 파일 형식입니다. PDF 또는 TXT 파일만 업로드 가능합니다.")
        
        st.markdown("---")
        
        # 업로드된 문서 목록
        st.markdown("### 📋 업로드된 문서")
        try:
            documents = vector_store.list_documents()
            if documents:
                for doc in documents:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f'<div class="document-item">📄 {doc}</div>', unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️", key=f"delete_{doc}", help=f"{doc} 삭제"):
                            try:
                                vector_store.delete_document(doc)
                                # 파일 시스템에서도 삭제
                                file_path = os.path.join('documents', doc)
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                st.success(f"{doc} 삭제 완료!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"문서 삭제 중 오류: {str(e)}")
            else:
                st.info("업로드된 문서가 없습니다.")
        except Exception as e:
            st.error(f"문서 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")
        
        st.markdown("---")
        
        # 대화 초기화 버튼
        if st.button("🔄 대화 초기화", use_container_width=True):
            chat_handler.clear_conversation(st.session_state.session_id)
            st.session_state.messages = []
            st.success("대화가 초기화되었습니다!")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 통계 정보
        st.markdown("### 📊 통계")
        try:
            doc_count = len(vector_store.list_documents())
            message_count = len(st.session_state.messages)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="metric-card"><h3>{doc_count}</h3><p>문서</p></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-card"><h3>{message_count}</h3><p>메시지</p></div>', unsafe_allow_html=True)
        except:
            pass
    
    # 메인 채팅 영역
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # 채팅 기록 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
            # 출처 정보 표시
            if "sources" in message and message["sources"]:
                with st.expander("📚 참고한 문서"):
                    for source in message["sources"]:
                        st.write(f"• {source}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 채팅 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 채팅 영역 업데이트
        with st.spinner("답변을 생성하고 있습니다..."):
            try:
                response, sources = chat_handler.get_response(prompt, st.session_state.session_id)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sources": sources
                })
            except Exception as e:
                error_msg = f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg,
                    "sources": []
                })
                logger.error(f"Chat error: {str(e)}")
        
        st.rerun()

if __name__ == "__main__":
    main()