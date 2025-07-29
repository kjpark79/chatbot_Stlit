import os
import time
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStore
from utils.chat_handler import ChatHandler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'documents'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

doc_processor = DocumentProcessor()
vector_store = VectorStore()
chat_handler = ChatHandler(vector_store)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("=== FILE UPLOAD REQUEST STARTED ===")
    
    try:
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request content length: {request.content_length}")
        
        if 'file' not in request.files:
            logger.warning("No file in request")
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        logger.info(f"File object received: {file}")
        logger.info(f"File filename: {file.filename}")
        logger.info(f"File content type: {file.content_type}")
        
        if file.filename == '':
            logger.warning("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            original_filename = file.filename
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            logger.info(f"Original filename: {original_filename}")
            logger.info(f"Secure filename: {filename}")
            logger.info(f"File path: {filepath}")
            
            logger.info("Starting file save...")
            file.save(filepath)
            logger.info("File saved successfully")
            
            file_size = os.path.getsize(filepath)
            logger.info(f"Saved file size: {file_size} bytes")
            
            logger.info("Starting document processing...")
            chunks = doc_processor.process_document(filepath)
            logger.info(f"Document processing completed. Generated {len(chunks)} chunks")
            
            if len(chunks) > 100:
                logger.warning(f"File too large: {len(chunks)} chunks (max 100)")
                return jsonify({'error': f'File too large: {len(chunks)} chunks (max 100)'}), 400
            
            logger.info("Adding documents to vector store...")
            vector_store.add_documents(chunks, original_filename)
            logger.info("Documents added to vector store successfully")
            
            logger.info(f"=== FILE UPLOAD COMPLETED SUCCESSFULLY: {original_filename} ===")
            return jsonify({'success': f'Successfully uploaded and processed {original_filename}'}), 200
            
        else:
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only TXT and PDF files are allowed.'}), 400
            
    except Exception as e:
        logger.error(f"=== UPLOAD ERROR OCCURRED ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_traceback}")
        
        logger.error("=== UPLOAD ERROR END ===")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        response = chat_handler.get_response(user_message, session_id)
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    def generate():
        try:
            response, sources = chat_handler.get_response(user_message, session_id)
            
            # 타자 효과를 위해 문자 단위로 전송
            words = response.split(' ')
            accumulated_text = ""
            
            for i, word in enumerate(words):
                accumulated_text += word
                if i < len(words) - 1:
                    accumulated_text += " "
                
                # 응답과 출처 정보를 JSON으로 전송
                data = {
                    "text": accumulated_text,
                    "sources": sources if i == len(words) - 1 else []  # 마지막에만 출처 전송
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                time.sleep(0.05)  # 50ms 딜레이
            
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            error_data = {
                "text": f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": []
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield f"data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/plain')

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    try:
        chat_handler.clear_conversation(session_id)
        return jsonify({'success': 'Conversation cleared'}), 200
    except Exception as e:
        return jsonify({'error': f'Error clearing conversation: {str(e)}'}), 500

@app.route('/documents')
def list_documents():
    try:
        documents = vector_store.list_documents()
        return jsonify({'documents': documents}), 200
    except Exception as e:
        return jsonify({'error': f'Error listing documents: {str(e)}'}), 500

@app.route('/documents/<document_name>', methods=['DELETE'])
def delete_document(document_name):
    try:
        # ChromaDB에서 문서 삭제
        vector_store.delete_document(document_name)
        
        # 파일 시스템에서도 삭제 (secure_filename으로 변환된 파일명으로 삭제)
        safe_filename = secure_filename(document_name)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({'success': f'Document {document_name} deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Error deleting document: {str(e)}'}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        os.makedirs('documents', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        logger.info("Directories created/verified")
        
        logger.info("Initializing components...")
        logger.info(f"Document processor: {doc_processor}")
        logger.info(f"Vector store: {vector_store}")
        logger.info(f"Chat handler: {chat_handler}")
        
        logger.info("Starting Flask server on 0.0.0.0:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        import traceback
        logger.error(f"Startup error traceback:\n{traceback.format_exc()}")
        raise