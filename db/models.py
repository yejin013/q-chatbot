from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.sql import func
from db.database import Base
import uuid

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    filetype = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536))  # Default OpenAI embedding dimension
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), nullable=False)
    answer = Column(Text, nullable=False)
    is_positive = Column(Boolean, nullable=True)  # User feedback
    embedding = Column(VECTOR(1536))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmbeddingTest(Base):
    __tablename__ = "embedding_tests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    topk_results = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 