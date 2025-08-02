import chromadb
from chromadb.config import Settings
import openai
import os
from typing import List

class VectorStore:
    def __init__(self, collection_name="documents", persist_directory="data"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = openai.embeddings.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        return [item.embedding for item in response.data]
    
    def add_documents(self, chunks: List[str], document_name: str):
        if not chunks:
            raise ValueError("No chunks to process")
        
        print(f"Processing {len(chunks)} chunks for {document_name}")
        
        # 기존 문서가 있다면 먼저 삭제
        try:
            self.delete_document(document_name)
            print(f"Removed existing data for {document_name}")
        except:
            pass  # 기존 데이터가 없으면 무시
        
        try:
            batch_size = 10
            processed_batches = 0
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(chunks) + batch_size - 1)//batch_size
                print(f"Processing batch {batch_num}/{total_batches}")
                
                try:
                    embeddings = self._get_embeddings(batch_chunks)
                    
                    ids = [f"{document_name}_{i+j}" for j in range(len(batch_chunks))]
                    metadatas = [{"source": document_name, "chunk_id": i+j} for j in range(len(batch_chunks))]
                    
                    self.collection.add(
                        documents=batch_chunks,
                        embeddings=embeddings,
                        metadatas=metadatas,
                        ids=ids
                    )
                    processed_batches += 1
                    print(f"Successfully processed batch {batch_num}/{total_batches}")
                    
                except Exception as batch_error:
                    print(f"Error in batch {batch_num}: {str(batch_error)}")
                    # 오류 발생 시 이미 추가된 부분 데이터 정리
                    if processed_batches > 0:
                        print(f"Cleaning up partially added data for {document_name}")
                        self.delete_document(document_name)
                    raise batch_error
                    
            print(f"Successfully processed all {total_batches} batches for {document_name}")
            
        except Exception as e:
            print(f"Error in add_documents: {str(e)}")
            raise
    
    def search(self, query: str, n_results: int = 5) -> List[dict]:
        query_embedding = self._get_embeddings([query])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        search_results = []
        for i in range(len(results['documents'][0])):
            search_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })
        
        return search_results
    
    def list_documents(self) -> List[str]:
        try:
            all_docs = self.collection.get()
            sources = set()
            for metadata in all_docs['metadatas']:
                if 'source' in metadata:
                    sources.add(metadata['source'])
            return list(sources)
        except Exception as e:
            return []
    
    def delete_document(self, document_name: str):
        try:
            all_docs = self.collection.get()
            ids_to_delete = []
            
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('source') == document_name:
                    ids_to_delete.append(all_docs['ids'][i])
            
            if ids_to_delete:
                print(f"Deleting {len(ids_to_delete)} chunks for {document_name}")
                self.collection.delete(ids=ids_to_delete)
                print(f"Successfully deleted {document_name}")
            else:
                print(f"No data found for {document_name}")
        except Exception as e:
            print(f"Error deleting document {document_name}: {str(e)}")
            raise