import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="질의응답",
    page_icon="❓",
    layout="wide"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

def ask_question(question, model_name="text-embedding-ada-002"):
    """질문 API 호출"""
    try:
        data = {
            "question": question,
            "model_name": model_name
        }
        response = requests.post(f"{API_BASE_URL}/qa/ask", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"질문 처리 실패: {response.text}")
            return None
    except Exception as e:
        st.error(f"질문 처리 중 오류 발생: {str(e)}")
        return None

def update_feedback(answer_id, is_positive):
    """피드백 업데이트"""
    try:
        data = {"is_positive": is_positive}
        response = requests.patch(f"{API_BASE_URL}/qa/answers/{answer_id}", json=data)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"피드백 업데이트 실패: {response.text}")
            return False
    except Exception as e:
        st.error(f"피드백 업데이트 중 오류 발생: {str(e)}")
        return False

def get_qa_history():
    """질의응답 히스토리 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/qa/history")
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"히스토리 조회 실패: {response.text}")
            return []
    except Exception as e:
        st.error(f"히스토리 조회 중 오류 발생: {str(e)}")
        return []

# 메인 UI
st.title("❓ AI 질의응답")
st.markdown("업로드된 문서에 대해 질문하고 AI의 답변을 받아보세요.")

# 질문 입력 섹션
st.header("질문하기")

# 임베딩 모델 선택
model_options = {
    "text-embedding-ada-002": "OpenAI Ada (기본)",
    "BAAI/bge-base-en-v1.5": "BGE Base",
    "sentence-transformers/all-MiniLM-L6-v2": "MiniLM",
    "cohere-embed-v3": "Cohere V3"
}

selected_model = st.selectbox(
    "임베딩 모델 선택",
    options=list(model_options.keys()),
    format_func=lambda x: model_options[x],
    help="다양한 임베딩 모델을 선택하여 검색 성능을 비교할 수 있습니다."
)

# 질문 입력
question = st.text_area(
    "질문을 입력하세요",
    placeholder="예: 이 문서의 주요 내용은 무엇인가요?",
    height=100,
    help="업로드된 문서에 대한 질문을 자유롭게 입력하세요."
)

# 질문 제출
if st.button("🔍 질문하기", type="primary", disabled=not question.strip()):
    if question.strip():
        with st.spinner("질문을 처리하고 답변을 생성하는 중..."):
            result = ask_question(question, selected_model)
            
            if result and result.get("success"):
                data = result["data"]
                
                # 답변 표시
                st.success("✅ 답변 생성 완료!")
                
                # 답변 내용
                st.subheader("🤖 AI 답변")
                st.write(data["answer"])
                
                # 관련 문서 정보
                if data.get("relevant_documents"):
                    st.subheader("📄 관련 문서")
                    for i, doc in enumerate(data["relevant_documents"], 1):
                        with st.expander(f"문서 {i}: {doc['filename']} (유사도: {doc['similarity']:.3f})"):
                            st.write(doc["content_preview"])
                
                # 피드백 버튼
                st.subheader("💬 답변 평가")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("👍 좋아요", key="positive"):
                        if update_feedback(data["answer_id"], True):
                            st.success("피드백이 저장되었습니다!")
                
                with col2:
                    if st.button("👎 개선 필요", key="negative"):
                        if update_feedback(data["answer_id"], False):
                            st.success("피드백이 저장되었습니다!")
                
                # 세션에 최근 답변 저장
                if "recent_answers" not in st.session_state:
                    st.session_state.recent_answers = []
                
                st.session_state.recent_answers.insert(0, {
                    "question": data["question"],
                    "answer": data["answer"],
                    "model": selected_model,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # 최근 5개만 유지
                st.session_state.recent_answers = st.session_state.recent_answers[:5]
            else:
                st.error("❌ 질문 처리 실패")

# 최근 답변 표시
if "recent_answers" in st.session_state and st.session_state.recent_answers:
    st.header("🕒 최근 답변")
    
    for i, qa in enumerate(st.session_state.recent_answers):
        with st.expander(f"Q: {qa['question'][:50]}... ({qa['timestamp']})"):
            st.write(f"**질문:** {qa['question']}")
            st.write(f"**모델:** {model_options.get(qa['model'], qa['model'])}")
            st.write(f"**답변:** {qa['answer']}")

# 질의응답 히스토리
st.header("📚 질의응답 히스토리")

# 새로고침 버튼
if st.button("🔄 히스토리 새로고침"):
    st.rerun()

# 히스토리 조회
history = get_qa_history()

if history:
    # 데이터프레임으로 표시
    df = pd.DataFrame(history)
    df["생성 날짜"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    df["피드백"] = df["is_positive"].apply(lambda x: "👍" if x else "👎" if x is False else "❓")
    
    # 표시할 컬럼만 선택
    display_df = df[["question", "answer", "피드백", "생성 날짜"]].copy()
    display_df.columns = ["질문", "답변", "피드백", "생성 날짜"]
    
    # 질문과 답변 길이 제한
    display_df["질문"] = display_df["질문"].apply(lambda x: x[:50] + "..." if len(x) > 50 else x)
    display_df["답변"] = display_df["답변"].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 통계 정보
    st.subheader("📊 히스토리 통계")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 질문 수", len(history))
    with col2:
        positive_count = len([h for h in history if h["is_positive"] is True])
        st.metric("긍정 피드백", positive_count)
    with col3:
        negative_count = len([h for h in history if h["is_positive"] is False])
        st.metric("부정 피드백", negative_count)
    with col4:
        feedback_rate = (positive_count + negative_count) / len(history) * 100 if history else 0
        st.metric("피드백 비율", f"{feedback_rate:.1f}%")
        
else:
    st.info("📝 아직 질의응답 기록이 없습니다. 위에서 질문해보세요!")

# 사이드바에 도움말
with st.sidebar:
    st.header("💡 도움말")
    st.markdown("""
    **질문 팁:**
    - 구체적이고 명확한 질문을 하세요
    - 문서의 특정 내용에 대해 질문하세요
    - "이 문서에서 ~에 대해 설명해주세요" 형식으로 질문하세요
    
    **임베딩 모델:**
    - **OpenAI Ada**: 빠르고 안정적 (기본)
    - **BGE Base**: 높은 정확도
    - **MiniLM**: 빠른 속도
    - **Cohere V3**: 균형잡힌 성능
    
    **피드백:**
    - 답변 품질에 대한 피드백을 제공해주세요
    - 피드백은 시스템 개선에 도움이 됩니다
    """)
    
    # 모델 정보
    st.header("🔧 모델 정보")
    model_info = {
        "text-embedding-ada-002": "차원: 1536, 속도: 빠름, 정확도: 중상",
        "BAAI/bge-base-en-v1.5": "차원: 768, 속도: 중간, 정확도: 높음",
        "sentence-transformers/all-MiniLM-L6-v2": "차원: 384, 속도: 빠름, 정확도: 낮음",
        "cohere-embed-v3": "차원: 1024, 속도: 빠름, 정확도: 중상"
    }
    
    for model, info in model_info.items():
        if model in model_options:
            st.caption(f"**{model_options[model]}**")
            st.caption(info) 