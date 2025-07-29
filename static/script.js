document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const documentList = document.getElementById('documentList');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInputText = document.getElementById('fileInputText');
    const selectedFileName = document.getElementById('selectedFileName');
    const fileName = document.getElementById('fileName');

    // 세션 ID 생성 (브라우저 세션당 고유)
    const sessionId = generateSessionId();

    // 페이지 로드 시 문서 목록 불러오기
    loadDocuments();

    // 마크다운 설정
    marked.setOptions({
        breaks: true,
        gfm: false, // GitHub Flavored Markdown 비활성화 (삭선 방지)
        headerIds: false,
        mangle: false
    });

    // 채팅 폼 제출
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (message) {
            sendMessage(message);
            messageInput.value = '';
        }
    });

    // 파일 업로드 폼 제출
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        uploadFile();
    });

    // 파일 선택 이벤트 리스너
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // 선택된 파일명 표시
            fileName.textContent = file.name;
            selectedFileName.style.display = 'block';
            fileInputText.textContent = '다른 파일 선택';
            uploadBtn.disabled = false;
            uploadBtn.classList.remove('disabled');
        } else {
            // 파일이 선택되지 않은 경우 초기 상태로
            selectedFileName.style.display = 'none';
            fileInputText.textContent = '파일 선택';
            uploadBtn.disabled = true;
            uploadBtn.classList.add('disabled');
        }
    });

    // 대화 초기화 버튼 클릭
    clearChatBtn.addEventListener('click', function() {
        if (confirm('대화 기록을 모두 삭제하시겠습니까?')) {
            clearConversation();
        }
    });

    function sendMessage(message) {
        // 사용자 메시지 표시
        addMessage(message, 'user');
        
        // 로딩 표시
        const loadingDiv = addMessage('답변을 생성하고 있습니다...', 'bot', true);
        
        // 스트리밍 응답을 위한 새로운 메시지 컨테이너 생성
        const responseMessageDiv = createEmptyMessage('bot');
        const responseContentDiv = responseMessageDiv.querySelector('.message-content');
        
        fetch('/chat-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            // 로딩 메시지 제거
            loadingDiv.remove();
            
            // 스트리밍 메시지 표시
            chatMessages.appendChild(responseMessageDiv);
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        return;
                    }
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6);
                            if (data === '[DONE]') {
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                                return;
                            }
                            
                            try {
                                // JSON 데이터 파싱
                                const jsonData = JSON.parse(data);
                                const text = jsonData.text;
                                const sources = jsonData.sources || [];
                                
                                // 마크다운을 HTML로 변환하고 XSS 방지
                                const htmlContent = marked.parse(text);
                                const cleanHtml = DOMPurify.sanitize(htmlContent);
                                
                                // 응답 텍스트 표시
                                responseContentDiv.innerHTML = cleanHtml;
                                
                                // 출처 정보가 있고 마지막 청크인 경우 출처 표시
                                if (sources.length > 0) {
                                    const sourcesDiv = document.createElement('div');
                                    sourcesDiv.className = 'message-sources';
                                    sourcesDiv.innerHTML = `
                                        <div class="sources-title">
                                            <i class="fas fa-file-alt"></i> 참고 문서
                                        </div>
                                        <div class="sources-list">
                                            ${sources.map(source => `<span class="source-item">${source}</span>`).join('')}
                                        </div>
                                    `;
                                    responseContentDiv.appendChild(sourcesDiv);
                                }
                                
                                // 스크롤을 맨 아래로
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            } catch (e) {
                                // JSON 파싱 실패시 기존 방식으로 처리
                                const htmlContent = marked.parse(data);
                                const cleanHtml = DOMPurify.sanitize(htmlContent);
                                responseContentDiv.innerHTML = cleanHtml;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        }
                    }
                    
                    readStream();
                });
            }
            
            readStream();
        })
        .catch(error => {
            loadingDiv.remove();
            if (responseMessageDiv.parentNode) {
                responseMessageDiv.remove();
            }
            addMessage('오류: 서버와 통신할 수 없습니다.', 'bot');
            console.error('Error:', error);
        });
    }

    function addMessage(text, sender, isLoading = false, isMarkdown = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        if (isLoading) {
            messageDiv.className += ' loading';
        }
        
        // 아바타 추가
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        if (sender === 'bot') {
            avatarDiv.innerHTML = '<i class="fas fa-city"></i>'; // 밀양시 로고 (도시 아이콘)
        } else {
            avatarDiv.innerHTML = '<i class="fas fa-user-circle"></i>'; // 사용자 아이콘
        }
        
        // 메시지 내용
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isMarkdown && sender === 'bot') {
            // 마크다운을 HTML로 변환하고 XSS 방지를 위해 sanitize
            const htmlContent = marked.parse(text);
            const cleanHtml = DOMPurify.sanitize(htmlContent);
            contentDiv.innerHTML = cleanHtml;
        } else {
            contentDiv.textContent = text;
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function createEmptyMessage(sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // 아바타 추가
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        if (sender === 'bot') {
            avatarDiv.innerHTML = '<i class="fas fa-city"></i>'; // 밀양시 로고 (도시 아이콘)
        } else {
            avatarDiv.innerHTML = '<i class="fas fa-user-circle"></i>'; // 사용자 아이콘
        }
        
        // 메시지 내용 (빈 컨테이너)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        return messageDiv;
    }

    function uploadFile() {
        const file = fileInput.files[0];
        if (!file) {
            alert('파일을 선택해주세요.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const statusDiv = document.createElement('div');
        statusDiv.className = 'upload-status text-info';
        statusDiv.textContent = '업로드 중...';
        uploadForm.appendChild(statusDiv);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            statusDiv.remove();
            
            if (data.success) {
                const successDiv = document.createElement('div');
                successDiv.className = 'upload-status text-success';
                successDiv.textContent = data.success;
                uploadForm.appendChild(successDiv);
                
                // 파일 입력 및 UI 초기화
                fileInput.value = '';
                selectedFileName.style.display = 'none';
                fileInputText.textContent = '파일 선택';
                uploadBtn.disabled = true;
                uploadBtn.classList.add('disabled');
                loadDocuments();
                
                setTimeout(() => {
                    successDiv.remove();
                }, 3000);
            } else if (data.error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'upload-status text-danger';
                errorDiv.textContent = '오류: ' + data.error;
                uploadForm.appendChild(errorDiv);
                
                setTimeout(() => {
                    errorDiv.remove();
                }, 5000);
            }
        })
        .catch(error => {
            statusDiv.remove();
            const errorDiv = document.createElement('div');
            errorDiv.className = 'upload-status text-danger';
            errorDiv.textContent = '업로드 실패: 서버와 통신할 수 없습니다.';
            uploadForm.appendChild(errorDiv);
            
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
            
            console.error('Error:', error);
        });
    }

    function loadDocuments() {
        fetch('/documents')
        .then(response => response.json())
        .then(data => {
            documentList.innerHTML = '';
            
            if (data.documents && data.documents.length > 0) {
                data.documents.forEach(doc => {
                    const docDiv = document.createElement('div');
                    docDiv.className = 'document-item';
                    
                    const docName = document.createElement('span');
                    docName.className = 'document-name';
                    docName.textContent = doc;
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'document-delete-btn';
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                    deleteBtn.title = '문서 삭제';
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        if (confirm(`"${doc}" 문서를 삭제하시겠습니까?`)) {
                            deleteDocument(doc);
                        }
                    };
                    
                    docDiv.appendChild(docName);
                    docDiv.appendChild(deleteBtn);
                    documentList.appendChild(docDiv);
                });
            } else {
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'text-muted';
                emptyDiv.textContent = '업로드된 문서가 없습니다.';
                documentList.appendChild(emptyDiv);
            }
        })
        .catch(error => {
            console.error('Error loading documents:', error);
        });
    }

    function clearConversation() {
        fetch('/clear_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: sessionId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 채팅 메시지 영역 초기화
                chatMessages.innerHTML = '<div class="alert alert-info">대화가 초기화되었습니다. 새로운 질문을 해보세요!</div>';
            } else if (data.error) {
                console.error('Error clearing conversation:', data.error);
            }
        })
        .catch(error => {
            console.error('Error clearing conversation:', error);
        });
    }

    function deleteDocument(documentName) {
        fetch(`/documents/${encodeURIComponent(documentName)}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const successDiv = document.createElement('div');
                successDiv.className = 'upload-status text-success';
                successDiv.textContent = `문서 "${documentName}"이(가) 삭제되었습니다.`;
                uploadForm.appendChild(successDiv);
                
                loadDocuments(); // 문서 목록 새로고침
                
                setTimeout(() => {
                    successDiv.remove();
                }, 3000);
            } else if (data.error) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'upload-status text-danger';
                errorDiv.textContent = '삭제 오류: ' + data.error;
                uploadForm.appendChild(errorDiv);
                
                setTimeout(() => {
                    errorDiv.remove();
                }, 5000);
            }
        })
        .catch(error => {
            console.error('Error deleting document:', error);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'upload-status text-danger';
            errorDiv.textContent = '문서 삭제 중 오류가 발생했습니다.';
            uploadForm.appendChild(errorDiv);
            
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        });
    }

    function generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
});