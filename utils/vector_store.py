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
        
        try:
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i+batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
                
                embeddings = self._get_embeddings(batch_chunks)
                
                ids = [f"{document_name}_{i+j}" for j in range(len(batch_chunks))]
                metadatas = [{"source": document_name, "chunk_id": i+j} for j in range(len(batch_chunks))]
                
                self.collection.add(
                    documents=batch_chunks,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
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
        all_docs = self.collection.get()
        ids_to_delete = []
        
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata.get('source') == document_name:
                ids_to_delete.append(all_docs['ids'][i])
        
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)