import openai
import os
import json
from utils.vector_store import VectorStore
from typing import List, Dict, Tuple

class ChatHandler:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.conversation_sessions = {}
    
    def get_response(self, user_message: str, session_id: str = "default") -> Tuple[str, List[str]]:
        if session_id not in self.conversation_sessions:
            self.conversation_sessions[session_id] = []
        
        relevant_docs = self.vector_store.search(user_message, n_results=8)
        
        # 출처 정보 수집 및 관련도 기반 컨텍스트 구성
        sources = []
        context = ""
        doc_relevance_scores = {}
        
        for i, doc in enumerate(relevant_docs):
            source_name = doc['metadata']['source']
            if source_name not in sources:
                sources.append(source_name)
            
            # 관련도 점수 계산 (상위 결과일수록 높은 점수)
            relevance_score = (len(relevant_docs) - i) / len(relevant_docs)
            
            # 문서별 관련도 점수 누적
            if source_name not in doc_relevance_scores:
                doc_relevance_scores[source_name] = 0
            doc_relevance_scores[source_name] += relevance_score
            
            context += f"🔍 **출처: {source_name}** (관련도: {relevance_score:.2f})\n"
            context += f"📝 내용: {doc['document']}\n\n"
        
        system_prompt = """안녕하세요! 저는 여러분의 문서를 꼼꼼히 살펴보고 친근하게 도와드리는 AI 어시스턴트입니다. 😊

제가 도와드릴 때 이런 점들을 중요하게 생각해요:
- 업로드하신 문서 내용에서 질문하신 내용과 정확히 일치하는 부분을 우선적으로 찾아서 답변드려요
- 문서에서 찾은 구체적인 내용을 바탕으로 정확하고 상세하게 설명해드려요  
- 이전 대화 내용도 함께 고려해서 맥락에 맞는 답변을 드려요
- 친근하고 이해하기 쉬운 말투로 설명해드려요
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
            
            # 관련도 점수가 높은 출처 순으로 정렬
            sorted_sources = sorted(sources, key=lambda x: doc_relevance_scores.get(x, 0), reverse=True)
            return assistant_response, sorted_sources
            
        except Exception as e:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}", []
    
    def clear_conversation(self, session_id: str = "default"):
        if session_id in self.conversation_sessions:
            self.conversation_sessions[session_id] = []
    
    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        return self.conversation_sessions.get(session_id, [])