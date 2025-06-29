from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.upload.router import router as upload_router
from backend.qa.router import router as qa_router
from backend.embedding_test.router import router as embedding_test_router
from backend.history.router import router as history_router
from backend.core.exception_handler import (
    global_exception_handler,
    custom_api_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    CustomAPIException
)
from db.database import engine
from db.models import Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Q-Chatbot API",
    description="AI 기반 문서 질의 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(CustomAPIException, custom_api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# 라우터 등록
app.include_router(upload_router)
app.include_router(qa_router)
app.include_router(embedding_test_router)
app.include_router(history_router)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "success": True,
        "message": "Q-Chatbot API 서버가 실행 중입니다.",
        "data": {
            "version": "1.0.0",
            "endpoints": {
                "upload": "/upload",
                "qa": "/qa",
                "embedding_test": "/embedding-test",
                "history": "/history"
            }
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "success": True,
        "message": "서버 상태 정상",
        "data": {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 