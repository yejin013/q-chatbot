import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="히스토리",
    page_icon="📚",
    layout="wide"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

def get_document_history(limit=50, offset=0, filetype=None, date_from=None, date_to=None):
    """문서 히스토리 조회"""
    try:
        params = {
            "limit": limit,
            "offset": offset
        }
        if filetype:
            params["filetype"] = filetype
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
            
        response = requests.get(f"{API_BASE_URL}/history/documents", params=params)
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"문서 히스토리 조회 실패: {response.text}")
            return {"documents": [], "pagination": {}}
    except Exception as e:
        st.error(f"문서 히스토리 조회 중 오류 발생: {str(e)}")
        return {"documents": [], "pagination": {}}

def get_qa_history(limit=50, offset=0, feedback=None, date_from=None, date_to=None):
    """질의응답 히스토리 조회"""
    try:
        params = {
            "limit": limit,
            "offset": offset
        }
        if feedback is not None:
            params["feedback"] = feedback
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
            
        response = requests.get(f"{API_BASE_URL}/history/qa", params=params)
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"질의응답 히스토리 조회 실패: {response.text}")
            return {"qa_history": [], "pagination": {}}
    except Exception as e:
        st.error(f"질의응답 히스토리 조회 중 오류 발생: {str(e)}")
        return {"qa_history": [], "pagination": {}}

def get_statistics():
    """통계 정보 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/history/statistics")
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"통계 정보 조회 실패: {response.text}")
            return {}
    except Exception as e:
        st.error(f"통계 정보 조회 중 오류 발생: {str(e)}")
        return {}

def delete_document(document_id):
    """문서 삭제"""
    try:
        response = requests.delete(f"{API_BASE_URL}/history/documents/{document_id}")
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"문서 삭제 실패: {response.text}")
            return False
    except Exception as e:
        st.error(f"문서 삭제 중 오류 발생: {str(e)}")
        return False

def delete_qa(question_id):
    """질의응답 삭제"""
    try:
        response = requests.delete(f"{API_BASE_URL}/history/qa/{question_id}")
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"질의응답 삭제 실패: {response.text}")
            return False
    except Exception as e:
        st.error(f"질의응답 삭제 중 오류 발생: {str(e)}")
        return False

# 메인 UI
st.title("📚 시스템 히스토리")
st.markdown("업로드된 문서와 질의응답 기록을 관리하고 통계를 확인하세요.")

# 탭 선택
tab1, tab2, tab3 = st.tabs(["📊 통계 대시보드", "📄 문서 히스토리", "❓ 질의응답 히스토리"])

# 통계 대시보드
with tab1:
    st.header("📊 시스템 통계")
    
    # 통계 정보 조회
    stats = get_statistics()
    
    if stats:
        # 전체 통계
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 문서 수", stats["documents"]["total"])
        with col2:
            st.metric("총 질문 수", stats["qa"]["total_queries"])
        with col3:
            st.metric("총 답변 수", stats["qa"]["total_answers"])
        with col4:
            feedback_rate = stats["qa"]["feedback_rate"] * 100
            st.metric("피드백 비율", f"{feedback_rate:.1f}%")
        
        # 문서 통계
        st.subheader("📄 문서 통계")
        doc_col1, doc_col2, doc_col3 = st.columns(3)
        
        with doc_col1:
            st.metric("PDF 파일", stats["documents"]["pdf"])
        with doc_col2:
            st.metric("DOCX 파일", stats["documents"]["docx"])
        with doc_col3:
            st.metric("최근 7일 업로드", stats["documents"]["recent_7_days"])
        
        # 파일 타입별 차트
        if stats["documents"]["by_filetype"]:
            fig_filetype = px.pie(
                values=list(stats["documents"]["by_filetype"].values()),
                names=list(stats["documents"]["by_filetype"].keys()),
                title="파일 타입별 분포"
            )
            st.plotly_chart(fig_filetype, use_container_width=True)
        
        # 질의응답 통계
        st.subheader("❓ 질의응답 통계")
        qa_col1, qa_col2, qa_col3 = st.columns(3)
        
        with qa_col1:
            st.metric("긍정 피드백", stats["qa"]["positive_feedback"])
        with qa_col2:
            st.metric("부정 피드백", stats["qa"]["negative_feedback"])
        with qa_col3:
            st.metric("최근 7일 질문", stats["qa"]["recent_7_days"])
        
        # 피드백 분포 차트
        if stats["qa"]["total_answers"] > 0:
            feedback_data = {
                "긍정": stats["qa"]["positive_feedback"],
                "부정": stats["qa"]["negative_feedback"],
                "미평가": stats["qa"]["total_answers"] - stats["qa"]["positive_feedback"] - stats["qa"]["negative_feedback"]
            }
            
            fig_feedback = px.bar(
                x=list(feedback_data.keys()),
                y=list(feedback_data.values()),
                title="피드백 분포",
                color=list(feedback_data.keys()),
                color_discrete_map={"긍정": "green", "부정": "red", "미평가": "gray"}
            )
            st.plotly_chart(fig_feedback, use_container_width=True)
    else:
        st.warning("통계 정보를 불러올 수 없습니다.")

# 문서 히스토리
with tab2:
    st.header("📄 문서 히스토리")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filetype_filter = st.selectbox(
            "파일 타입 필터",
            ["전체", ".pdf", ".docx"],
            help="특정 파일 타입만 조회할 수 있습니다."
        )
    
    with col2:
        date_from = st.date_input(
            "시작 날짜",
            value=datetime.now() - timedelta(days=30),
            help="조회할 시작 날짜를 선택하세요."
        )
    
    with col3:
        date_to = st.date_input(
            "종료 날짜",
            value=datetime.now(),
            help="조회할 종료 날짜를 선택하세요."
        )
    
    # 페이징
    col1, col2 = st.columns([3, 1])
    with col1:
        limit = st.slider("페이지당 항목 수", 10, 100, 20)
    with col2:
        page = st.number_input("페이지", min_value=1, value=1)
    
    offset = (page - 1) * limit
    
    # 문서 히스토리 조회
    doc_history = get_document_history(
        limit=limit,
        offset=offset,
        filetype=filetype_filter if filetype_filter != "전체" else None,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None
    )
    
    if doc_history["documents"]:
        # 데이터프레임으로 표시
        df_docs = pd.DataFrame(doc_history["documents"])
        df_docs["업로드 날짜"] = pd.to_datetime(df_docs["uploaded_at"]).dt.strftime("%Y-%m-%d %H:%M")
        df_docs["파일 크기"] = df_docs["content_length"].apply(lambda x: f"{x:,} 문자")
        
        # 표시할 컬럼만 선택
        display_df = df_docs[["filename", "filetype", "파일 크기", "업로드 날짜"]].copy()
        display_df.columns = ["파일명", "타입", "크기", "업로드 날짜"]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 페이징 정보
        pagination = doc_history["pagination"]
        if pagination:
            st.write(f"총 {pagination['total']}개 항목 중 {offset + 1}-{min(offset + limit, pagination['total'])}번째 표시")
            
            if pagination["has_more"]:
                if st.button("다음 페이지"):
                    st.session_state.page = page + 1
                    st.rerun()
            
            if page > 1:
                if st.button("이전 페이지"):
                    st.session_state.page = page - 1
                    st.rerun()
        
        # 문서 삭제 기능
        st.subheader("🗑️ 문서 삭제")
        doc_to_delete = st.selectbox(
            "삭제할 문서를 선택하세요",
            options=[(d["id"], d["filename"]) for d in doc_history["documents"]],
            format_func=lambda x: x[1]
        )
        
        if st.button("문서 삭제", type="secondary"):
            if doc_to_delete:
                doc_id = doc_to_delete[0]
                if delete_document(doc_id):
                    st.success("✅ 문서 삭제 완료!")
                    st.rerun()
    else:
        st.info("📝 해당 조건에 맞는 문서가 없습니다.")

# 질의응답 히스토리
with tab3:
    st.header("❓ 질의응답 히스토리")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        feedback_filter = st.selectbox(
            "피드백 필터",
            ["전체", "긍정", "부정", "미평가"],
            help="특정 피드백만 조회할 수 있습니다."
        )
    
    with col2:
        qa_date_from = st.date_input(
            "시작 날짜",
            value=datetime.now() - timedelta(days=30),
            key="qa_date_from",
            help="조회할 시작 날짜를 선택하세요."
        )
    
    with col3:
        qa_date_to = st.date_input(
            "종료 날짜",
            value=datetime.now(),
            key="qa_date_to",
            help="조회할 종료 날짜를 선택하세요."
        )
    
    # 페이징
    col1, col2 = st.columns([3, 1])
    with col1:
        qa_limit = st.slider("페이지당 항목 수", 10, 100, 20, key="qa_limit")
    with col2:
        qa_page = st.number_input("페이지", min_value=1, value=1, key="qa_page")
    
    qa_offset = (qa_page - 1) * qa_limit
    
    # 피드백 필터 변환
    feedback_map = {"긍정": True, "부정": False, "미평가": None, "전체": None}
    feedback_value = feedback_map[feedback_filter]
    
    # 질의응답 히스토리 조회
    qa_history = get_qa_history(
        limit=qa_limit,
        offset=qa_offset,
        feedback=feedback_value,
        date_from=qa_date_from.isoformat() if qa_date_from else None,
        date_to=qa_date_to.isoformat() if qa_date_to else None
    )
    
    if qa_history["qa_history"]:
        # 데이터프레임으로 표시
        df_qa = pd.DataFrame(qa_history["qa_history"])
        df_qa["생성 날짜"] = pd.to_datetime(df_qa["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
        df_qa["피드백"] = df_qa["is_positive"].apply(lambda x: "👍" if x else "👎" if x is False else "❓")
        
        # 표시할 컬럼만 선택
        display_df = df_qa[["question", "answer", "피드백", "생성 날짜"]].copy()
        display_df.columns = ["질문", "답변", "피드백", "생성 날짜"]
        
        # 질문과 답변 길이 제한
        display_df["질문"] = display_df["질문"].apply(lambda x: x[:50] + "..." if len(x) > 50 else x)
        display_df["답변"] = display_df["답변"].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 페이징 정보
        pagination = qa_history["pagination"]
        if pagination:
            st.write(f"총 {pagination['total']}개 항목 중 {qa_offset + 1}-{min(qa_offset + qa_limit, pagination['total'])}번째 표시")
            
            if pagination["has_more"]:
                if st.button("다음 페이지", key="qa_next"):
                    st.session_state.qa_page = qa_page + 1
                    st.rerun()
            
            if qa_page > 1:
                if st.button("이전 페이지", key="qa_prev"):
                    st.session_state.qa_page = qa_page - 1
                    st.rerun()
        
        # 질의응답 삭제 기능
        st.subheader("🗑️ 질의응답 삭제")
        qa_to_delete = st.selectbox(
            "삭제할 질의응답을 선택하세요",
            options=[(qa["question_id"], f"{qa['question'][:50]}...") for qa in qa_history["qa_history"]],
            format_func=lambda x: x[1]
        )
        
        if st.button("질의응답 삭제", type="secondary"):
            if qa_to_delete:
                qa_id = qa_to_delete[0]
                if delete_qa(qa_id):
                    st.success("✅ 질의응답 삭제 완료!")
                    st.rerun()
    else:
        st.info("📝 해당 조건에 맞는 질의응답이 없습니다.")

# 사이드바에 도움말
with st.sidebar:
    st.header("💡 도움말")
    st.markdown("""
    **히스토리 관리:**
    - 업로드된 문서와 질의응답 기록을 조회할 수 있습니다
    - 다양한 필터를 사용하여 원하는 데이터를 찾을 수 있습니다
    - 불필요한 데이터는 삭제할 수 있습니다
    
    **통계 정보:**
    - 시스템 사용 현황을 한눈에 확인할 수 있습니다
    - 파일 타입별 분포와 피드백 분포를 차트로 확인할 수 있습니다
    
    **필터 기능:**
    - 날짜 범위로 기간을 지정할 수 있습니다
    - 파일 타입이나 피드백으로 필터링할 수 있습니다
    - 페이징을 통해 대량의 데이터를 효율적으로 조회할 수 있습니다
    """)
    
    # 새로고침 버튼
    if st.button("🔄 전체 새로고침"):
        st.rerun() 