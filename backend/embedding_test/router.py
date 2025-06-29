from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import io
from pathlib import Path
import PyPDF2
from docx import Document

from db.database import get_db
from db.models import EmbeddingTest as EmbeddingTestModel
from backend.retrieval.vector_search import VectorSearch
from backend.config import settings
from backend.core.exception_handler import CustomAPIException

router = APIRouter(prefix="/embedding-test", tags=["embedding-test"])

vector_search = VectorSearch()

class TestRequest(BaseModel):
    question: str
    model_names: List[str] = ["text-embedding-ada-002", "BAAI/bge-base-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"]

def extract_text_from_file(file_content: bytes, file_extension: str) -> str:
    """파일에서 텍스트 추출"""
    try:
        if file_extension == ".pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        elif file_extension == ".docx":
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        else:
            raise CustomAPIException("지원하지 않는 파일 형식입니다.")
    except Exception as e:
        raise CustomAPIException(f"텍스트 추출 실패: {str(e)}")

@router.post("/test-with-file")
async def test_embedding_with_file(
    file: UploadFile = File(...),
    question: str = None,
    model_names: List[str] = None,
    db: Session = Depends(get_db)
):
    """파일을 업로드하여 임베딩 모델 성능 테스트"""
    try:
        # 기본값 설정
        if model_names is None:
            model_names = ["text-embedding-ada-002", "BAAI/bge-base-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"]
        
        if question is None:
            question = "이 문서의 주요 내용은 무엇인가요?"
        
        # 파일 검증
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise CustomAPIException(
                f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # 파일 읽기
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise CustomAPIException(
                f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 텍스트 추출
        content = extract_text_from_file(file_content, file_extension)
        if not content.strip():
            raise CustomAPIException("파일에서 텍스트를 추출할 수 없습니다.")
        
        # 문서를 문장 단위로 분할 (간단한 분할)
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) < 3:
            sentences = [content]  # 문장이 적으면 전체를 하나로
        
        # 각 모델별로 FAISS 검색 수행
        results = {}
        for model_name in model_names:
            try:
                if model_name in vector_search.embedding_generator.models:
                    faiss_results = vector_search.search_faiss(
                        documents=sentences,
                        query=question,
                        model_name=model_name,
                        top_k=3
                    )
                    results[model_name] = {
                        "status": "success",
                        "results": faiss_results
                    }
                else:
                    results[model_name] = {
                        "status": "error",
                        "error": f"Model {model_name} not available"
                    }
            except Exception as e:
                results[model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # 테스트 결과 저장
        test_record = EmbeddingTestModel(
            id=uuid.uuid4(),
            model_name="multiple",
            question=question,
            topk_results=results
        )
        db.add(test_record)
        db.commit()
        
        return {
            "success": True,
            "message": "임베딩 테스트 완료",
            "data": {
                "test_id": str(test_record.id),
                "question": question,
                "filename": file.filename,
                "content_length": len(content),
                "results": results,
                "created_at": test_record.created_at.isoformat()
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"임베딩 테스트 중 오류가 발생했습니다: {str(e)}")

@router.post("/test-with-text")
async def test_embedding_with_text(
    request: TestRequest,
    db: Session = Depends(get_db)
):
    """텍스트를 직접 입력하여 임베딩 모델 성능 테스트"""
    try:
        # 샘플 문서들 (테스트용)
        sample_documents = [
            "인공지능은 컴퓨터 시스템이 인간의 지능을 모방하여 학습하고 추론하는 기술입니다.",
            "머신러닝은 데이터로부터 패턴을 학습하여 예측이나 분류를 수행하는 AI의 한 분야입니다.",
            "딥러닝은 신경망을 사용하여 복잡한 패턴을 학습하는 머신러닝의 하위 분야입니다.",
            "자연어처리는 인간의 언어를 컴퓨터가 이해하고 처리할 수 있도록 하는 기술입니다.",
            "컴퓨터 비전은 이미지나 비디오에서 의미 있는 정보를 추출하는 AI 기술입니다."
        ]
        
        # 각 모델별로 FAISS 검색 수행
        results = {}
        for model_name in request.model_names:
            try:
                if model_name in vector_search.embedding_generator.models:
                    faiss_results = vector_search.search_faiss(
                        documents=sample_documents,
                        query=request.question,
                        model_name=model_name,
                        top_k=3
                    )
                    results[model_name] = {
                        "status": "success",
                        "results": faiss_results
                    }
                else:
                    results[model_name] = {
                        "status": "error",
                        "error": f"Model {model_name} not available"
                    }
            except Exception as e:
                results[model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # 테스트 결과 저장
        test_record = EmbeddingTestModel(
            id=uuid.uuid4(),
            model_name="multiple",
            question=request.question,
            topk_results=results
        )
        db.add(test_record)
        db.commit()
        
        return {
            "success": True,
            "message": "임베딩 테스트 완료",
            "data": {
                "test_id": str(test_record.id),
                "question": request.question,
                "results": results,
                "created_at": test_record.created_at.isoformat()
            }
        }
        
    except Exception as e:
        raise CustomAPIException(f"임베딩 테스트 중 오류가 발생했습니다: {str(e)}")

@router.get("/available-models")
async def get_available_models():
    """사용 가능한 임베딩 모델 목록 조회"""
    try:
        available_models = list(vector_search.embedding_generator.models.keys())
        
        model_info = {}
        for model_name in available_models:
            dimension = vector_search.embedding_generator.get_dimension(model_name)
            model_info[model_name] = {
                "dimension": dimension,
                "available": True
            }
        
        # 모든 지원 모델 정보 추가
        for model_name, dimension in settings.EMBEDDING_DIMENSIONS.items():
            if model_name not in model_info:
                model_info[model_name] = {
                    "dimension": dimension,
                    "available": model_name in available_models
                }
        
        return {
            "success": True,
            "message": "사용 가능한 모델 목록 조회 완료",
            "data": model_info
        }
        
    except Exception as e:
        raise CustomAPIException(f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/history")
async def get_test_history(db: Session = Depends(get_db)):
    """임베딩 테스트 히스토리 조회"""
    try:
        tests = db.query(EmbeddingTestModel).order_by(
            EmbeddingTestModel.created_at.desc()
        ).limit(20).all()
        
        history = []
        for test in tests:
            history.append({
                "id": str(test.id),
                "model_name": test.model_name,
                "question": test.question,
                "created_at": test.created_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "테스트 히스토리 조회 완료",
            "data": history
        }
        
    except Exception as e:
        raise CustomAPIException(f"히스토리 조회 중 오류가 발생했습니다: {str(e)}") 