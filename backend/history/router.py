from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from db.database import get_db
from db.models import Document as DocumentModel, Query as QueryModel, Answer as AnswerModel
from backend.core.exception_handler import CustomAPIException

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/documents")
async def get_document_history(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    filetype: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """업로드된 문서 히스토리 조회"""
    try:
        query = db.query(DocumentModel)
        
        # 파일 타입 필터
        if filetype:
            query = query.filter(DocumentModel.filetype == filetype)
        
        # 날짜 범위 필터
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(DocumentModel.uploaded_at >= from_date)
            except ValueError:
                raise CustomAPIException("잘못된 날짜 형식입니다. ISO 형식을 사용해주세요.")
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(DocumentModel.uploaded_at <= to_date)
            except ValueError:
                raise CustomAPIException("잘못된 날짜 형식입니다. ISO 형식을 사용해주세요.")
        
        # 정렬 및 페이징
        documents = query.order_by(DocumentModel.uploaded_at.desc()).offset(offset).limit(limit).all()
        
        # 전체 개수 조회
        total_count = query.count()
        
        return {
            "success": True,
            "message": "문서 히스토리 조회 완료",
            "data": {
                "documents": [
                    {
                        "id": str(doc.id),
                        "filename": doc.filename,
                        "filetype": doc.filetype,
                        "content_length": len(doc.content),
                        "uploaded_at": doc.uploaded_at.isoformat()
                    }
                    for doc in documents
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"문서 히스토리 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/qa")
async def get_qa_history(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    feedback: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """질의응답 히스토리 조회"""
    try:
        query = db.query(QueryModel, AnswerModel).join(
            AnswerModel, QueryModel.id == AnswerModel.question_id
        )
        
        # 피드백 필터
        if feedback is not None:
            query = query.filter(AnswerModel.is_positive == feedback)
        
        # 날짜 범위 필터
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(QueryModel.created_at >= from_date)
            except ValueError:
                raise CustomAPIException("잘못된 날짜 형식입니다. ISO 형식을 사용해주세요.")
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(QueryModel.created_at <= to_date)
            except ValueError:
                raise CustomAPIException("잘못된 날짜 형식입니다. ISO 형식을 사용해주세요.")
        
        # 정렬 및 페이징
        qa_history = query.order_by(QueryModel.created_at.desc()).offset(offset).limit(limit).all()
        
        # 전체 개수 조회
        total_count = query.count()
        
        history = []
        for query_obj, answer in qa_history:
            history.append({
                "question_id": str(query_obj.id),
                "answer_id": str(answer.id),
                "question": query_obj.question,
                "answer": answer.answer,
                "is_positive": answer.is_positive,
                "created_at": query_obj.created_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "질의응답 히스토리 조회 완료",
            "data": {
                "qa_history": history,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except CustomAPIException:
        raise
    except Exception as e:
        raise CustomAPIException(f"질의응답 히스토리 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/statistics")
async def get_history_statistics(db: Session = Depends(get_db)):
    """히스토리 통계 정보 조회"""
    try:
        # 문서 통계
        total_documents = db.query(DocumentModel).count()
        pdf_count = db.query(DocumentModel).filter(DocumentModel.filetype == ".pdf").count()
        docx_count = db.query(DocumentModel).filter(DocumentModel.filetype == ".docx").count()
        
        # 질의응답 통계
        total_queries = db.query(QueryModel).count()
        total_answers = db.query(AnswerModel).count()
        positive_feedback = db.query(AnswerModel).filter(AnswerModel.is_positive == True).count()
        negative_feedback = db.query(AnswerModel).filter(AnswerModel.is_positive == False).count()
        
        # 최근 7일 통계
        week_ago = datetime.now() - timedelta(days=7)
        recent_documents = db.query(DocumentModel).filter(
            DocumentModel.uploaded_at >= week_ago
        ).count()
        recent_queries = db.query(QueryModel).filter(
            QueryModel.created_at >= week_ago
        ).count()
        
        # 파일 타입별 통계
        filetype_stats = {}
        filetypes = db.query(DocumentModel.filetype).distinct().all()
        for filetype in filetypes:
            count = db.query(DocumentModel).filter(
                DocumentModel.filetype == filetype[0]
            ).count()
            filetype_stats[filetype[0]] = count
        
        return {
            "success": True,
            "message": "통계 정보 조회 완료",
            "data": {
                "documents": {
                    "total": total_documents,
                    "pdf": pdf_count,
                    "docx": docx_count,
                    "recent_7_days": recent_documents,
                    "by_filetype": filetype_stats
                },
                "qa": {
                    "total_queries": total_queries,
                    "total_answers": total_answers,
                    "positive_feedback": positive_feedback,
                    "negative_feedback": negative_feedback,
                    "recent_7_days": recent_queries,
                    "feedback_rate": (positive_feedback + negative_feedback) / total_answers if total_answers > 0 else 0
                }
            }
        }
        
    except Exception as e:
        raise CustomAPIException(f"통계 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document_from_history(document_id: str, db: Session = Depends(get_db)):
    """히스토리에서 문서 삭제"""
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

@router.delete("/qa/{question_id}")
async def delete_qa_from_history(question_id: str, db: Session = Depends(get_db)):
    """히스토리에서 질의응답 삭제"""
    try:
        # 질문과 관련된 응답들 삭제
        answers = db.query(AnswerModel).filter(AnswerModel.question_id == question_id).all()
        for answer in answers:
            db.delete(answer)
        
        # 질문 삭제
        query = db.query(QueryModel).filter(QueryModel.id == question_id).first()
        if query:
            db.delete(query)
        
        db.commit()
        
        return {
            "success": True,
            "message": "질의응답 삭제 완료",
            "data": None
        }
        
    except Exception as e:
        raise CustomAPIException(f"질의응답 삭제 중 오류가 발생했습니다: {str(e)}") 