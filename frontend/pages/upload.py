import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="문서 업로드",
    page_icon="📄",
    layout="wide"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8000"

def upload_file(file):
    """파일 업로드 API 호출"""
    try:
        files = {"file": file}
        response = requests.post(f"{API_BASE_URL}/upload/", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"업로드 실패: {response.text}")
            return None
    except Exception as e:
        st.error(f"업로드 중 오류 발생: {str(e)}")
        return None

def get_uploaded_files():
    """업로드된 파일 목록 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/upload/")
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"파일 목록 조회 실패: {response.text}")
            return []
    except Exception as e:
        st.error(f"파일 목록 조회 중 오류 발생: {str(e)}")
        return []

def delete_file(file_id):
    """파일 삭제"""
    try:
        response = requests.delete(f"{API_BASE_URL}/upload/{file_id}")
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"삭제 실패: {response.text}")
            return False
    except Exception as e:
        st.error(f"삭제 중 오류 발생: {str(e)}")
        return False

# 메인 UI
st.title("📄 문서 업로드")
st.markdown("PDF 또는 DOCX 파일을 업로드하여 AI 질의 시스템에 추가하세요.")

# 파일 업로드 섹션
st.header("파일 업로드")
uploaded_file = st.file_uploader(
    "파일을 선택하세요",
    type=["pdf", "docx"],
    help="PDF 또는 DOCX 파일만 업로드 가능합니다. (최대 10MB)"
)

if uploaded_file is not None:
    # 파일 정보 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("파일명", uploaded_file.name)
    with col2:
        st.metric("파일 크기", f"{uploaded_file.size / 1024:.1f} KB")
    with col3:
        st.metric("파일 타입", uploaded_file.type or "알 수 없음")
    
    # 업로드 버튼
    if st.button("📤 파일 업로드", type="primary"):
        with st.spinner("파일을 업로드하고 임베딩을 생성하는 중..."):
            result = upload_file(uploaded_file)
            
            if result and result.get("success"):
                st.success("✅ 파일 업로드 완료!")
                st.json(result["data"])
            else:
                st.error("❌ 파일 업로드 실패")

# 업로드된 파일 목록
st.header("📋 업로드된 파일 목록")

# 새로고침 버튼
if st.button("🔄 목록 새로고침"):
    st.rerun()

# 파일 목록 조회
files = get_uploaded_files()

if files:
    # 데이터프레임으로 표시
    df = pd.DataFrame(files)
    df["업로드 날짜"] = pd.to_datetime(df["uploaded_at"]).dt.strftime("%Y-%m-%d %H:%M")
    df["파일 크기"] = df["content_length"].apply(lambda x: f"{x:,} 문자")
    
    # 표시할 컬럼만 선택
    display_df = df[["filename", "filetype", "파일 크기", "업로드 날짜"]].copy()
    display_df.columns = ["파일명", "타입", "크기", "업로드 날짜"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # 파일 삭제 기능
    st.subheader("🗑️ 파일 삭제")
    file_to_delete = st.selectbox(
        "삭제할 파일을 선택하세요",
        options=[(f["id"], f["filename"]) for f in files],
        format_func=lambda x: x[1]
    )
    
    if st.button("삭제", type="secondary"):
        if file_to_delete:
            file_id = file_to_delete[0]
            if delete_file(file_id):
                st.success("✅ 파일 삭제 완료!")
                st.rerun()
    
    # 통계 정보
    st.subheader("📊 업로드 통계")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 파일 수", len(files))
    with col2:
        pdf_count = len([f for f in files if f["filetype"] == ".pdf"])
        st.metric("PDF 파일", pdf_count)
    with col3:
        docx_count = len([f for f in files if f["filetype"] == ".docx"])
        st.metric("DOCX 파일", docx_count)
    with col4:
        total_chars = sum(f["content_length"] for f in files)
        st.metric("총 문자 수", f"{total_chars:,}")
        
else:
    st.info("📝 아직 업로드된 파일이 없습니다. 위에서 파일을 업로드해보세요!")

# 사이드바에 도움말
with st.sidebar:
    st.header("💡 도움말")
    st.markdown("""
    **지원 파일 형식:**
    - PDF (.pdf)
    - Word (.docx)
    
    **파일 크기 제한:**
    - 최대 10MB
    
    **처리 과정:**
    1. 파일 업로드
    2. 텍스트 추출
    3. 임베딩 생성
    4. 데이터베이스 저장
    
    **주의사항:**
    - 이미지가 포함된 PDF는 텍스트만 추출됩니다
    - 파일 업로드 후 질의응답 페이지에서 사용할 수 있습니다
    """) 