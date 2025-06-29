from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
from pathlib import Path
import PyPDF2
from docx import Document
import io

from db.database import get_db
from db.models import Document as DocumentModel
from backend.retrieval.vector_search import EmbeddingGenerator
from backend.config import settings
from backend.core.exception_handler import CustomAPIException

router = APIRouter(prefix="/upload", tags=["upload"])

embedding_generator = EmbeddingGenerator()

def extract_text_from_pdf(file_content: bytes) -> str:
    """PDF 파일에서 텍스트 추출"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise CustomAPIException(f"PDF 텍스트 추출 실패: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """DOCX 파일에서 텍스트 추출"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise CustomAPIException(f"DOCX 텍스트 추출 실패: {str(e)}")

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """파일 업로드 및 임베딩 생성"""
    try:
        # 파일 확장자 검증
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise CustomAPIException(
                f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise CustomAPIException(
                f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 텍스트 추출
        if file_extension == ".pdf":
            content = extract_text_from_pdf(file_content)
        elif file_extension == ".docx":
            content = extract_text_from_docx(file_content)
        else:
            raise CustomAPIException("지원하지 않는 파일 형식입니다.")
        
        if not content.strip():
            raise CustomAPIException("파일에서 텍스트를 추출할 수 없습니다.")
        
        # 임베딩 생성
        embedding = embedding_generator.get_embedding(
            content, 
            settings.DEFAULT_EMBEDDING_MODEL
        )
        
        # 데이터베이스에 저장
        document = DocumentModel(
            id=uuid.uuid4(),
            filename=file.filename,
            filetype=file_extension,
            content=content,
            embedding=embedding
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "success": True,
            "message": "파일 업로드 완료",
            "data": {
                "id": str(document.id),
                "filename": document.filename,
                "filetype": document.filetype,
                "content_length": len(document.content),
                "uploaded_at": document.uploaded_at.isoformat()
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")

@router.get("/")
async def get_uploaded_files(db: Session = Depends(get_db)):
    """업로드된 파일 목록 조회"""
    try:
        documents = db.query(DocumentModel).order_by(DocumentModel.uploaded_at.desc()).all()
        
        return {
            "success": True,
            "message": "업로드된 파일 목록 조회 완료",
            "data": [
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "filetype": doc.filetype,
                    "content_length": len(doc.content),
                    "uploaded_at": doc.uploaded_at.isoformat()
                }
                for doc in documents
            ]
        }
        
    except Exception as e:
        raise CustomAPIException(f"파일 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """업로드된 문서 삭제"""
    try:
        document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            raise CustomAPIException("문서를 찾을 수 없습니다.")
        
        db.delete(document)
        db.commit()
        
        return {
            "success": True,
            "message": "문서 삭제 완료",
            "data": None
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"문서 삭제 중 오류가 발생했습니다: {str(e)}") 