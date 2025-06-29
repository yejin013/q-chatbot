import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="임베딩 테스트",
    page_icon="🧪",
    layout="wide"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

def test_embedding_with_file(file, question, model_names):
    """파일로 임베딩 테스트"""
    try:
        files = {"file": file}
        data = {
            "question": question,
            "model_names": model_names
        }
        response = requests.post(
            f"{API_BASE_URL}/embedding-test/test-with-file",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"테스트 실패: {response.text}")
            return None
    except Exception as e:
        st.error(f"테스트 중 오류 발생: {str(e)}")
        return None

def test_embedding_with_text(question, model_names):
    """텍스트로 임베딩 테스트"""
    try:
        data = {
            "question": question,
            "model_names": model_names
        }
        response = requests.post(f"{API_BASE_URL}/embedding-test/test-with-text", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"테스트 실패: {response.text}")
            return None
    except Exception as e:
        st.error(f"테스트 중 오류 발생: {str(e)}")
        return None

def get_available_models():
    """사용 가능한 모델 목록 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/embedding-test/available-models")
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"모델 목록 조회 실패: {response.text}")
            return {}
    except Exception as e:
        st.error(f"모델 목록 조회 중 오류 발생: {str(e)}")
        return {}

def get_test_history():
    """테스트 히스토리 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/embedding-test/history")
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"히스토리 조회 실패: {response.text}")
            return []
    except Exception as e:
        st.error(f"히스토리 조회 중 오류 발생: {str(e)}")
        return []

# 메인 UI
st.title("🧪 임베딩 모델 성능 테스트")
st.markdown("다양한 임베딩 모델의 성능을 비교하고 테스트해보세요.")

# 사용 가능한 모델 정보
st.header("📋 사용 가능한 모델")
models_info = get_available_models()

if models_info:
    # 모델 정보를 데이터프레임으로 표시
    model_data = []
    for model_name, info in models_info.items():
        model_data.append({
            "모델명": model_name,
            "차원": info.get("dimension", "N/A"),
            "사용 가능": "✅" if info.get("available", False) else "❌"
        })
    
    df_models = pd.DataFrame(model_data)
    st.dataframe(df_models, use_container_width=True, hide_index=True)
else:
    st.warning("모델 정보를 불러올 수 없습니다.")

# 테스트 섹션
st.header("🔬 임베딩 테스트")

# 테스트 방법 선택
test_method = st.radio(
    "테스트 방법 선택",
    ["파일 업로드", "샘플 텍스트"],
    help="파일을 업로드하거나 미리 정의된 샘플 텍스트로 테스트할 수 있습니다."
)

# 모델 선택
available_models = [name for name, info in models_info.items() if info.get("available", False)]
if available_models:
    selected_models = st.multiselect(
        "테스트할 모델 선택",
        options=available_models,
        default=available_models[:3] if len(available_models) >= 3 else available_models,
        help="비교할 임베딩 모델들을 선택하세요."
    )
else:
    st.error("사용 가능한 모델이 없습니다.")
    selected_models = []

# 질문 입력
question = st.text_area(
    "테스트 질문 입력",
    value="이 문서의 주요 내용은 무엇인가요?",
    height=80,
    help="임베딩 모델들이 찾을 질문을 입력하세요."
)

# 테스트 실행
if test_method == "파일 업로드":
    uploaded_file = st.file_uploader(
        "테스트용 파일 업로드",
        type=["pdf", "docx"],
        help="PDF 또는 DOCX 파일을 업로드하여 테스트하세요."
    )
    
    if uploaded_file and selected_models and st.button("🧪 테스트 실행", type="primary"):
        with st.spinner("임베딩 모델들을 테스트하는 중..."):
            result = test_embedding_with_file(uploaded_file, question, selected_models)
            
            if result and result.get("success"):
                display_test_results(result["data"])
            else:
                st.error("❌ 테스트 실패")

else:  # 샘플 텍스트
    if selected_models and st.button("🧪 테스트 실행", type="primary"):
        with st.spinner("임베딩 모델들을 테스트하는 중..."):
            result = test_embedding_with_text(question, selected_models)
            
            if result and result.get("success"):
                display_test_results(result["data"])
            else:
                st.error("❌ 테스트 실패")

def display_test_results(data):
    """테스트 결과 표시"""
    st.success("✅ 테스트 완료!")
    
    # 결과 요약
    st.subheader("📊 테스트 결과 요약")
    
    results = data["results"]
    successful_models = [name for name, result in results.items() if result.get("status") == "success"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("테스트 모델 수", len(selected_models))
    with col2:
        st.metric("성공한 모델 수", len(successful_models))
    with col3:
        success_rate = len(successful_models) / len(selected_models) * 100 if selected_models else 0
        st.metric("성공률", f"{success_rate:.1f}%")
    
    # 각 모델별 결과
    st.subheader("🔍 모델별 상세 결과")
    
    for model_name, result in results.items():
        with st.expander(f"📈 {model_name}"):
            if result.get("status") == "success":
                model_results = result.get("results", [])
                
                if model_results:
                    # 유사도 점수 차트
                    similarities = [r["similarity"] for r in model_results]
                    indices = [r["index"] for r in model_results]
                    
                    # 차트 생성
                    fig = go.Figure(data=[
                        go.Bar(
                            x=[f"결과 {i+1}" for i in range(len(similarities))],
                            y=similarities,
                            text=[f"{s:.3f}" for s in similarities],
                            textposition='auto',
                            name="유사도 점수"
                        )
                    ])
                    
                    fig.update_layout(
                        title=f"{model_name} - 유사도 점수 비교",
                        xaxis_title="검색 결과",
                        yaxis_title="유사도 점수",
                        yaxis_range=[0, 1]
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 상세 결과 표시
                    st.write("**상세 결과:**")
                    for i, r in enumerate(model_results):
                        st.write(f"**결과 {i+1}** (유사도: {r['similarity']:.3f})")
                        st.write(f"내용: {r['content'][:200]}...")
                        st.divider()
                else:
                    st.warning("검색 결과가 없습니다.")
            else:
                st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
    
    # 모델 비교 차트
    if len(successful_models) > 1:
        st.subheader("📊 모델 성능 비교")
        
        # 평균 유사도 점수 계산
        model_avg_similarities = {}
        for model_name in successful_models:
            model_results = results[model_name].get("results", [])
            if model_results:
                avg_similarity = sum(r["similarity"] for r in model_results) / len(model_results)
                model_avg_similarities[model_name] = avg_similarity
        
        if model_avg_similarities:
            # 평균 유사도 비교 차트
            fig_comparison = px.bar(
                x=list(model_avg_similarities.keys()),
                y=list(model_avg_similarities.values()),
                title="모델별 평균 유사도 점수 비교",
                labels={"x": "모델", "y": "평균 유사도 점수"}
            )
            
            fig_comparison.update_layout(yaxis_range=[0, 1])
            st.plotly_chart(fig_comparison, use_container_width=True)

# 테스트 히스토리
st.header("📚 테스트 히스토리")

# 새로고침 버튼
if st.button("🔄 히스토리 새로고침"):
    st.rerun()

# 히스토리 조회
history = get_test_history()

if history:
    # 데이터프레임으로 표시
    df_history = pd.DataFrame(history)
    df_history["생성 날짜"] = pd.to_datetime(df_history["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    
    # 표시할 컬럼만 선택
    display_df = df_history[["question", "model_name", "생성 날짜"]].copy()
    display_df.columns = ["질문", "모델", "생성 날짜"]
    
    # 질문 길이 제한
    display_df["질문"] = display_df["질문"].apply(lambda x: x[:50] + "..." if len(x) > 50 else x)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 통계 정보
    st.subheader("📊 히스토리 통계")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 테스트 수", len(history))
    with col2:
        recent_tests = len([h for h in history if "2024" in h["created_at"]])  # 간단한 최근 필터
        st.metric("최근 테스트", recent_tests)
    with col3:
        unique_models = len(set(h["model_name"] for h in history))
        st.metric("사용된 모델", unique_models)
        
else:
    st.info("📝 아직 테스트 기록이 없습니다. 위에서 테스트를 실행해보세요!")

# 사이드바에 도움말
with st.sidebar:
    st.header("💡 도움말")
    st.markdown("""
    **임베딩 테스트란?**
    - 다양한 임베딩 모델의 성능을 비교하는 기능입니다
    - 동일한 질문에 대해 각 모델이 찾는 결과를 비교할 수 있습니다
    
    **테스트 방법:**
    1. 파일 업로드: 실제 문서로 테스트
    2. 샘플 텍스트: 미리 정의된 텍스트로 테스트
    
    **결과 해석:**
    - 유사도 점수가 높을수록 더 관련성 높은 결과
    - 모델별로 다른 결과를 보일 수 있음
    - 용도에 맞는 모델 선택이 중요
    
    **모델 특성:**
    - **OpenAI Ada**: 빠르고 안정적
    - **BGE**: 높은 정확도
    - **MiniLM**: 빠른 속도
    - **Cohere**: 균형잡힌 성능
    """)
    
    # 샘플 질문들
    st.header("💭 샘플 질문")
    sample_questions = [
        "이 문서의 주요 내용은 무엇인가요?",
        "핵심 개념을 설명해주세요",
        "주요 결론은 무엇인가요?",
        "이 문서에서 다루는 문제점은?",
        "해결 방안은 무엇인가요?"
    ]
    
    for i, q in enumerate(sample_questions):
        if st.button(q, key=f"sample_{i}"):
            st.session_state.sample_question = q
            st.rerun() 