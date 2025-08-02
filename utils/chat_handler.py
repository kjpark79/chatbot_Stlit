import openai
import os
import json
from utils.vector_store import VectorStore
from typing import List, Dict, Tuple

class ChatHandler:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.conversation_sessions = {}
    
    def get_response(self, user_message: str, session_id: str = "default") -> Tuple[str, List[str]]:
        if session_id not in self.conversation_sessions:
            self.conversation_sessions[session_id] = []
        
        relevant_docs = self.vector_store.search(user_message, n_results=8)
        
        # 컨텍스트 구성을 위한 문서 정보
        context = ""
        doc_metadata = {}
        
        for i, doc in enumerate(relevant_docs):
            source_name = doc['metadata']['source']
            
            # 관련도 점수 계산 (상위 결과일수록 높은 점수)
            relevance_score = (len(relevant_docs) - i) / len(relevant_docs)
            
            # 문서별 관련도 점수 누적
            if source_name not in doc_metadata:
                doc_metadata[source_name] = {'score': 0, 'content': []}
            doc_metadata[source_name]['score'] += relevance_score
            doc_metadata[source_name]['content'].append(doc['document'])
            
            context += f"🔍 **출처: {source_name}** (관련도: {relevance_score:.2f})\n"
            context += f"📝 내용: {doc['document']}\n\n"
        
        system_prompt = """안녕하세요! 저는 여러분의 문서를 꼼꼼히 살펴보고 친근하게 도와드리는 AI 어시스턴트입니다. 😊

제가 도와드릴 때 이런 점들을 중요하게 생각해요:
- 업로드하신 문서 내용에서 질문하신 내용과 정확히 일치하는 부분을 우선적으로 찾아서 답변드려요
- 문서에서 찾은 구체적인 내용을 바탕으로 정확하고 상세하게 설명해드려요  
- 이전 대화 내용도 함께 고려해서 맥락에 맞는 답변을 드려요
- 친근하고 이해하기 쉬운 말투로 설명해드려요
- 부연설명은 자제하고 원래 문서의 내용이 최대한 정확하게 전달되도록 해요
- 답변은 마크다운 형식으로 깔끔하게 정리해드려요

만약 문서에서 관련 정보를 찾을 수 없다면 솔직하게 말씀드릴게요. 궁금한 것이 있으시면 언제든지 편하게 물어보세요!"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 이전 대화 내역 추가 (최대 10개 턴)
        conversation_history = self.conversation_sessions[session_id][-10:]
        for turn in conversation_history:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        
        user_prompt = f"""📄 **업로드하신 문서에서 찾은 관련 내용:**

{context}

💬 **질문:** {user_message}

위 문서 내용에서 질문과 정확히 일치하는 부분이 있다면 그 내용을 중심으로 자세히 답변해주세요. 문서의 구체적인 정보를 최대한 활용해서 정확하고 친근하게 설명해주세요!"""
        
        messages.append({"role": "user", "content": user_prompt})
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            assistant_response = response.choices[0].message.content
            
            # 대화 내역에 추가
            self.conversation_sessions[session_id].append({
                "user": user_message,
                "assistant": assistant_response
            })
            
            # 답변에서 실제 사용된 문서 추출 (중복 제거)
            used_sources = set()
            
            # 관련도 점수가 높은 순으로 정렬
            sorted_docs = sorted(doc_metadata.items(), key=lambda x: x[1]['score'], reverse=True)
            
            # 상위 관련도 문서 중에서 실제 답변에 활용된 것만 선별
            for doc_name, doc_info in sorted_docs:
                # 답변에 문서명이 직접 언급되었는지 확인
                if doc_name in assistant_response:
                    used_sources.add(doc_name)
                    continue
                
                # 문서 내용이 답변에 실질적으로 활용되었는지 다중 방식으로 확인
                is_used = False
                for content_chunk in doc_info['content']:
                    # 공백과 줄바꿈 제거한 버전으로 비교
                    clean_content = content_chunk.replace(' ', '').replace('\n', '').replace('\t', '')
                    clean_response = assistant_response.replace(' ', '').replace('\n', '').replace('\t', '')
                    
                    # 방법 1: 연속된 긴 텍스트 매칭 (30자 이상)
                    for i in range(0, len(clean_content) - 30, 10):
                        snippet = clean_content[i:i+30]
                        if snippet in clean_response:
                            is_used = True
                            break
                    
                    if is_used:
                        break
                    
                    # 방법 2: 핵심 키워드 밀도 체크 (한국어 특성 고려)
                    content_words = [word for word in content_chunk.split() if len(word) > 1]
                    response_words = assistant_response.split()
                    
                    # 문서의 주요 단어들이 답변에 얼마나 포함되어 있는지 확인
                    if len(content_words) > 0:
                        word_matches = sum(1 for word in content_words[:20] if word in assistant_response)
                        match_ratio = word_matches / min(len(content_words), 20)
                        
                        # 30% 이상 매칭되면 사용된 것으로 판단
                        if match_ratio > 0.3:
                            is_used = True
                            break
                
                if is_used:
                    used_sources.add(doc_name)
            
            # 실제 사용된 문서가 없다면 최상위 관련도 문서 1개만 포함
            if not used_sources and sorted_docs:
                used_sources.add(sorted_docs[0][0])
            
            used_sources = list(used_sources)
            
            return assistant_response, used_sources
            
        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}", []
    
    def clear_conversation(self, session_id: str = "default"):
        if session_id in self.conversation_sessions:
            self.conversation_sessions[session_id] = []
    
    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        return self.conversation_sessions.get(session_id, [])