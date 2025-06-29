import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import openai
import cohere
from sentence_transformers import SentenceTransformer
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """다양한 임베딩 모델을 지원하는 클래스"""
    
    def __init__(self):
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """사용 가능한 임베딩 모델들을 초기화"""
        try:
            if settings.OPENAI_API_KEY:
                openai.api_key = settings.OPENAI_API_KEY
                self.models["text-embedding-ada-002"] = "openai"
            
            if settings.COHERE_API_KEY:
                self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
                self.models["cohere-embed-v3"] = "cohere"
            
            if settings.HUGGINGFACE_API_KEY:
                # HuggingFace 모델들 초기화
                self.models["BAAI/bge-large-en-v1.5"] = "hf"
                self.models["BAAI/bge-base-en-v1.5"] = "hf"
                self.models["intfloat/e5-large-v2"] = "hf"
                self.models["intfloat/e5-base-v2"] = "hf"
                self.models["sentence-transformers/all-MiniLM-L6-v2"] = "hf"
                
        except Exception as e:
            logger.error(f"Error initializing embedding models: {e}")
    
    def get_embedding(self, text: str, model_name: str = "text-embedding-ada-002") -> List[float]:
        """텍스트를 임베딩 벡터로 변환"""
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not available")
            
            model_type = self.models[model_name]
            
            if model_type == "openai":
                response = openai.Embedding.create(
                    input=text,
                    model=model_name
                )
                return response['data'][0]['embedding']
            
            elif model_type == "cohere":
                response = self.cohere_client.embed(
                    texts=[text],
                    model=model_name
                )
                return response.embeddings[0]
            
            elif model_type == "hf":
                if model_name not in self._hf_models:
                    self._hf_models[model_name] = SentenceTransformer(model_name)
                
                embedding = self._hf_models[model_name].encode(text)
                return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding with {model_name}: {e}")
            raise
    
    def get_dimension(self, model_name: str) -> int:
        """모델의 임베딩 차원 수 반환"""
        return settings.EMBEDDING_DIMENSIONS.get(model_name, 1536)

class VectorSearch:
    """벡터 검색 기능을 제공하는 클래스"""
    
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
    
    def search_pgvector(self, db: Session, query: str, model_name: str = "text-embedding-ada-002", 
                       top_k: int = 5) -> List[Dict[str, Any]]:
        """PostgreSQL pgvector를 사용한 벡터 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_generator.get_embedding(query, model_name)
            
            # pgvector를 사용한 유사도 검색
            sql = text("""
                SELECT id, filename, content, 
                       1 - (embedding <=> :embedding) as similarity
                FROM documents 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :embedding
                LIMIT :top_k
            """)
            
            result = db.execute(sql, {
                "embedding": query_embedding,
                "top_k": top_k
            })
            
            documents = []
            for row in result:
                documents.append({
                    "id": str(row.id),
                    "filename": row.filename,
                    "content": row.content,
                    "similarity": float(row.similarity)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in pgvector search: {e}")
            raise
    
    def search_faiss(self, documents: List[str], query: str, 
                    model_name: str = "text-embedding-ada-002", 
                    top_k: int = 5) -> List[Dict[str, Any]]:
        """FAISS를 사용한 벡터 검색 (테스트용)"""
        try:
            # 문서들 임베딩 생성
            doc_embeddings = []
            for doc in documents:
                embedding = self.embedding_generator.get_embedding(doc, model_name)
                doc_embeddings.append(embedding)
            
            # FAISS 인덱스 생성
            dimension = self.embedding_generator.get_dimension(model_name)
            index = faiss.IndexFlatIP(dimension)  # Inner Product for cosine similarity
            
            # 정규화된 벡터로 인덱스 생성
            doc_embeddings_np = np.array(doc_embeddings, dtype=np.float32)
            faiss.normalize_L2(doc_embeddings_np)
            index.add(doc_embeddings_np)
            
            # 쿼리 임베딩 생성 및 검색
            query_embedding = self.embedding_generator.get_embedding(query, model_name)
            query_embedding_np = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_embedding_np)
            
            similarities, indices = index.search(query_embedding_np, top_k)
            
            # 결과 반환
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if idx < len(documents):
                    results.append({
                        "index": int(idx),
                        "content": documents[idx],
                        "similarity": float(similarity)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in FAISS search: {e}")
            raise
    
    def compare_models(self, documents: List[str], query: str, 
                      model_names: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """여러 임베딩 모델의 성능을 비교"""
        if model_names is None:
            model_names = ["text-embedding-ada-002", "BAAI/bge-base-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"]
        
        results = {}
        
        for model_name in model_names:
            try:
                if model_name in self.embedding_generator.models:
                    faiss_results = self.search_faiss(documents, query, model_name)
                    results[model_name] = faiss_results
                else:
                    results[model_name] = {"error": f"Model {model_name} not available"}
            except Exception as e:
                results[model_name] = {"error": str(e)}
        
        return results 