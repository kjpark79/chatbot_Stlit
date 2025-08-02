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

# 기본 Streamlit 디자인 사용

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
    st.title("🤖 밀양시 AI 어시스턴트")
    st.caption("문서를 업로드하고 AI와 대화해보세요")
    
    # 사이드바
    with st.sidebar:
        st.header("📂 문서 관리")
        
        
        # 처리된 파일 세션 상태 관리
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "📄 문서 업로드",
            type=['pdf', 'txt'],
            help="PDF 또는 TXT 파일을 업로드하세요 (최대 16MB)",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # 이미 이번 세션에서 처리한 파일인지 확인
            if uploaded_file.name in st.session_state.processed_files:
                st.success(f"✅ {uploaded_file.name}은 이미 업로드 완료되었습니다.")
            else:
                # DB에서 실제로 파일이 존재하는지 확인
                existing_docs = vector_store.list_documents()
                if uploaded_file.name in existing_docs:
                    st.warning(f"⚠️ {uploaded_file.name}은 이미 업로드된 파일입니다.")
                    st.session_state.processed_files.add(uploaded_file.name)
                elif uploaded_file.size > MAX_FILE_SIZE:
                    st.error(f"파일 크기가 너무 큽니다. 최대 {MAX_FILE_SIZE // (1024*1024)}MB까지 업로드 가능합니다.")
                elif not allowed_file(uploaded_file.name):
                    st.error("지원하지 않는 파일 형식입니다. PDF 또는 TXT 파일만 업로드 가능합니다.")
                else:
                    # 새로운 파일 업로드 처리
                    with st.spinner(f"{uploaded_file.name} 문서를 처리하고 있습니다..."):
                        try:
                            # 파일 저장
                            file_path = os.path.join('documents', uploaded_file.name)
                            with open(file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            
                            # 문서 처리
                            chunks = doc_processor.process_document(file_path)
                            
                            if len(chunks) > 400:
                                st.error(f"파일이 너무 큽니다: {len(chunks)}개 청크 (최대 400개)")
                                os.remove(file_path)
                            else:
                                # 벡터 스토어에 추가
                                progress_placeholder = st.empty()
                                progress_placeholder.info(f"{len(chunks)}개 청크를 임베딩 중입니다...")
                                
                                vector_store.add_documents(chunks, uploaded_file.name)
                                
                                # 업로드 완료 표시 및 세션에 기록
                                progress_placeholder.success(f"✅ {uploaded_file.name} 업로드 완료!")
                                st.session_state.processed_files.add(uploaded_file.name)
                                
                                                                
                        except Exception as e:
                            st.error(f"문서 처리 중 오류가 발생했습니다: {str(e)}")
                            logger.error(f"Document processing error: {str(e)}")
                            # 실패한 파일은 documents에서 제거
                            file_path = os.path.join('documents', uploaded_file.name)
                            if os.path.exists(file_path):
                                os.remove(file_path)
        
        st.markdown("---")
        
        # 업로드된 문서 목록
        st.subheader("📋 업로드된 문서")
        try:
            documents = vector_store.list_documents()
            if documents:
                for doc in documents:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 {doc}")
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
        
        
        # 통계 정보
        st.header("📊 통계")
        try:
            doc_count = len(vector_store.list_documents())
            message_count = len(st.session_state.messages)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("문서", doc_count)
            with col2:
                st.metric("메시지", message_count)
        except:
            pass
    
    # 메인 채팅 영역
    st.header("💬 ChatBot")
    
    # 채팅 기록 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                # 출처 정보 표시
                if "sources" in message and message["sources"]:
                    with st.expander("📚 참고한 문서"):
                        for source in message["sources"]:
                            st.write(f"• {source}")
    
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