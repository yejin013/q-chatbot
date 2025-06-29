from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid
import openai
from openai import AzureOpenAI

from db.database import get_db
from db.models import Query as QueryModel, Answer as AnswerModel, Document as DocumentModel
from backend.retrieval.vector_search import VectorSearch
from backend.config import settings
from backend.core.exception_handler import CustomAPIException

router = APIRouter(prefix="/qa", tags=["qa"])

vector_search = VectorSearch()

class QuestionRequest(BaseModel):
    question: str
    model_name: Optional[str] = "text-embedding-ada-002"

class FeedbackRequest(BaseModel):
    is_positive: bool

def generate_llm_response(question: str, context_docs: List[dict]) -> str:
    """LLM을 사용하여 응답 생성"""
    try:
        # Azure OpenAI 사용
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            # 컨텍스트 문서들을 요약하여 프롬프트 구성
            context_text = "\n\n".join([
                f"문서 {i+1}: {doc['content'][:500]}..." 
                for i, doc in enumerate(context_docs[:3])  # Top 3 문서만 사용
            ])
            
            prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

문서 내용:
{context_text}

질문: {question}

답변:"""
            
            response = client.chat.completions.create(
                model="gpt-35-turbo",  # Azure OpenAI 모델명
                messages=[
                    {"role": "system", "content": "당신은 문서를 기반으로 정확하고 유용한 답변을 제공하는 AI 어시스턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        # OpenAI fallback
        elif settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            
            context_text = "\n\n".join([
                f"문서 {i+1}: {doc['content'][:500]}..." 
                for i, doc in enumerate(context_docs[:3])
            ])
            
            prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

문서 내용:
{context_text}

질문: {question}

답변:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 문서를 기반으로 정확하고 유용한 답변을 제공하는 AI 어시스턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        else:
            # LLM이 없는 경우 벡터 검색 결과만 반환
            if context_docs:
                return f"관련 문서를 찾았습니다:\n\n" + "\n\n".join([
                    f"문서: {doc['filename']}\n유사도: {doc['similarity']:.3f}\n내용: {doc['content'][:200]}..."
                    for doc in context_docs
                ])
            else:
                return "관련 문서를 찾을 수 없습니다."
                
    except Exception as e:
        raise CustomAPIException(f"LLM 응답 생성 중 오류가 발생했습니다: {str(e)}")

@router.post("/ask")
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """질문에 대한 답변 생성"""
    try:
        # 1. 벡터 검색으로 관련 문서 찾기
        relevant_docs = vector_search.search_pgvector(
            db=db,
            query=request.question,
            model_name=request.model_name,
            top_k=settings.TOP_K_RESULTS
        )
        
        # 2. 질문 임베딩 생성
        question_embedding = vector_search.embedding_generator.get_embedding(
            request.question, 
            request.model_name
        )
        
        # 3. 질문 저장
        query = QueryModel(
            id=uuid.uuid4(),
            question=request.question,
            embedding=question_embedding
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 4. LLM 응답 생성
        answer_text = generate_llm_response(request.question, relevant_docs)
        
        # 5. 응답 저장
        answer = AnswerModel(
            id=uuid.uuid4(),
            question_id=query.id,
            answer=answer_text,
            embedding=question_embedding  # 질문 임베딩을 응답에도 저장
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        
        return {
            "success": True,
            "message": "질문 처리 완료",
            "data": {
                "question_id": str(query.id),
                "answer_id": str(answer.id),
                "question": request.question,
                "answer": answer_text,
                "relevant_documents": [
                    {
                        "filename": doc["filename"],
                        "similarity": doc["similarity"],
                        "content_preview": doc["content"][:200] + "..."
                    }
                    for doc in relevant_docs
                ],
                "created_at": answer.created_at.isoformat()
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"질문 처리 중 오류가 발생했습니다: {str(e)}")

@router.patch("/answers/{answer_id}")
async def update_feedback(
    answer_id: str,
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """응답에 대한 피드백 업데이트"""
    try:
        answer = db.query(AnswerModel).filter(AnswerModel.id == answer_id).first()
        if not answer:
            raise CustomAPIException("응답을 찾을 수 없습니다.")
        
        answer.is_positive = feedback.is_positive
        db.commit()
        
        return {
            "success": True,
            "message": "피드백 업데이트 완료",
            "data": {
                "answer_id": str(answer.id),
                "is_positive": answer.is_positive
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"피드백 업데이트 중 오류가 발생했습니다: {str(e)}")

@router.get("/history")
async def get_qa_history(db: Session = Depends(get_db)):
    """질의응답 히스토리 조회"""
    try:
        # 최근 질의응답 조회
        qa_history = db.query(QueryModel, AnswerModel).join(
            AnswerModel, QueryModel.id == AnswerModel.question_id
        ).order_by(QueryModel.created_at.desc()).limit(50).all()
        
        history = []
        for query, answer in qa_history:
            history.append({
                "question_id": str(query.id),
                "answer_id": str(answer.id),
                "question": query.question,
                "answer": answer.answer,
                "is_positive": answer.is_positive,
                "created_at": query.created_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "질의응답 히스토리 조회 완료",
            "data": history
        }
        
    except Exception as e:
        raise CustomAPIException(f"히스토리 조회 중 오류가 발생했습니다: {str(e)}") 