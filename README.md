# 🤖 Q-Chatbot

AI 기반 문서 질의 시스템으로, PDF 및 DOCX 파일을 업로드하고 자연어로 질문하여 AI의 답변을 받을 수 있는 웹 애플리케이션입니다.

## ✨ 주요 기능

- **📄 문서 업로드**: PDF, DOCX 파일 업로드 및 텍스트 추출
- **❓ AI 질의응답**: 업로드된 문서에 대한 자연어 질의응답
- **🧪 임베딩 테스트**: 다양한 임베딩 모델의 성능 비교
- **📚 히스토리 관리**: 업로드 및 질의응답 기록 관리
- **📊 통계 대시보드**: 시스템 사용 현황 및 분석

## 🏗️ 기술 스택

### 백엔드
- **FastAPI**: 고성능 Python 웹 프레임워크
- **PostgreSQL + pgvector**: 벡터 데이터베이스
- **SQLAlchemy**: ORM
- **FAISS**: 벡터 검색 엔진

### 프론트엔드
- **Streamlit**: 데이터 과학 웹 애플리케이션 프레임워크
- **Plotly**: 인터랙티브 차트 및 시각화

### AI/ML
- **OpenAI**: GPT 모델 및 임베딩
- **Azure OpenAI**: 클라우드 AI 서비스
- **BGE**: BAAI 임베딩 모델
- **Cohere**: 임베딩 모델
- **Sentence Transformers**: 다양한 임베딩 모델

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/q-chatbot.git
cd q-chatbot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp env.example .env
# .env 파일을 편집하여 실제 API 키와 데이터베이스 정보를 입력
```

### 5. PostgreSQL 데이터베이스 설정
```sql
-- PostgreSQL에 pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 데이터베이스 생성
CREATE DATABASE qchatbot;
```

### 6. 백엔드 서버 실행
```bash
python main.py
# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 프론트엔드 실행
```bash
streamlit run app.py
```

## 📋 환경 변수 설정

`.env` 파일에서 다음 설정을 구성하세요:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost/qchatbot

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15

# OpenAI (fallback)
OPENAI_API_KEY=your_openai_api_key

# Cohere
COHERE_API_KEY=your_cohere_api_key

# HuggingFace
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

## 🎯 사용법

### 1. 문서 업로드
- PDF 또는 DOCX 파일을 업로드
- 시스템이 자동으로 텍스트를 추출하고 임베딩을 생성
- 업로드된 문서 목록에서 관리 가능

### 2. 질의응답
- 업로드된 문서에 대해 자연어로 질문
- 다양한 임베딩 모델 선택 가능
- AI가 관련 문서를 찾아 답변 생성
- 답변에 대한 피드백 제공 가능

### 3. 임베딩 테스트
- 다양한 임베딩 모델의 성능 비교
- 파일 업로드 또는 샘플 텍스트로 테스트
- 유사도 점수 및 차트로 결과 시각화

### 4. 히스토리 관리
- 업로드된 문서 및 질의응답 기록 조회
- 필터링 및 페이징 기능
- 통계 대시보드로 사용 현황 확인

## 📁 프로젝트 구조

```
q-chatbot/
├── backend/                 # FastAPI 백엔드
│   ├── upload/             # 파일 업로드 기능
│   ├── qa/                 # 질의응답 기능
│   ├── embedding_test/     # 임베딩 테스트 기능
│   ├── history/            # 히스토리 관리
│   ├── retrieval/          # 벡터 검색
│   ├── core/               # 핵심 기능
│   └── config.py           # 설정 관리
├── db/                     # 데이터베이스
│   ├── models.py           # 데이터 모델
│   └── database.py         # 데이터베이스 연결
├── frontend/               # Streamlit 프론트엔드
│   ├── pages/              # 페이지별 UI
│   └── components/         # 재사용 컴포넌트
├── main.py                 # FastAPI 메인 애플리케이션
├── app.py                  # Streamlit 메인 애플리케이션
├── requirements.txt        # Python 의존성
└── README.md              # 프로젝트 문서
```

## 🔧 API 엔드포인트

### 문서 업로드
- `POST /upload/`: 파일 업로드
- `GET /upload/`: 업로드된 파일 목록
- `DELETE /upload/{document_id}`: 파일 삭제

### 질의응답
- `POST /qa/ask`: 질문하기
- `PATCH /qa/answers/{answer_id}`: 피드백 업데이트
- `GET /qa/history`: 질의응답 히스토리

### 임베딩 테스트
- `POST /embedding-test/test-with-file`: 파일로 테스트
- `POST /embedding-test/test-with-text`: 텍스트로 테스트
- `GET /embedding-test/available-models`: 사용 가능한 모델
- `GET /embedding-test/history`: 테스트 히스토리

### 히스토리
- `GET /history/documents`: 문서 히스토리
- `GET /history/qa`: 질의응답 히스토리
- `GET /history/statistics`: 통계 정보

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

## 🙏 감사의 말

- [FastAPI](https://fastapi.tiangolo.com/) - 고성능 웹 프레임워크
- [Streamlit](https://streamlit.io/) - 데이터 앱 프레임워크
- [OpenAI](https://openai.com/) - AI 모델 제공
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL 벡터 확장
- [FAISS](https://github.com/facebookresearch/faiss) - 벡터 검색 라이브러리