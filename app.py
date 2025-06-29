import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 페이지 설정
st.set_page_config(
    page_title="Q-Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 네비게이션
st.sidebar.title("🤖 Q-Chatbot")
st.sidebar.markdown("AI 기반 문서 질의 시스템")

# 페이지 선택
page = st.sidebar.selectbox(
    "페이지 선택",
    [
        "📄 문서 업로드",
        "❓ 질의응답", 
        "🧪 임베딩 테스트",
        "📚 히스토리"
    ]
)

# 페이지 라우팅
if page == "📄 문서 업로드":
    import frontend.pages.upload
elif page == "❓ 질의응답":
    import frontend.pages.inquiry
elif page == "🧪 임베딩 테스트":
    import frontend.pages.embedding_test
elif page == "📚 히스토리":
    import frontend.pages.history

# 사이드바에 시스템 정보
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ 시스템 정보")
st.sidebar.markdown("""
**버전:** 1.0.0  
**백엔드:** FastAPI  
**프론트엔드:** Streamlit  
**데이터베이스:** PostgreSQL + pgvector  
**벡터 검색:** FAISS  
**임베딩:** OpenAI, BGE, Cohere 등
""")

# 사이드바에 도움말
st.sidebar.markdown("---")
st.sidebar.header("💡 사용법")
st.sidebar.markdown("""
1. **문서 업로드**: PDF/DOCX 파일을 업로드하세요
2. **질의응답**: 업로드된 문서에 대해 질문하세요
3. **임베딩 테스트**: 다양한 모델의 성능을 비교하세요
4. **히스토리**: 업로드 및 질의응답 기록을 관리하세요
""")

# 사이드바에 링크
st.sidebar.markdown("---")
st.sidebar.header("🔗 링크")
st.sidebar.markdown("""
- [API 문서](http://localhost:8000/docs)
- [GitHub](https://github.com/your-repo/q-chatbot)
- [문서](https://your-docs-url.com)
""")

# 푸터
st.sidebar.markdown("---")
st.sidebar.markdown("© 2024 Q-Chatbot Team") 