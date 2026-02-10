import streamlit as st
import pandas as pd
import math

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------
st.set_page_config(page_title="AI Tool Atlas", page_icon="🧭", layout="wide")

# 스타일 커스터마이징 (버튼과 이미지 정렬)
st.markdown("""
<style>
    div.stButton > button {
        width: 100%;
        height: 80px; /* 버튼 높이 키움 */
        border-radius: 12px;
        text-align: left;
        padding-left: 20px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = 'AI_Tool_Atlas_4files_통합_표준화.xlsx' # 파일명 확인
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except:
        try:
            df = pd.read_csv(file_path + " - Sheet1.csv")
        except:
            return pd.DataFrame()

    df.fillna('정보 없음', inplace=True)
    
    # 문자열 컬럼 정리
    cols = ['분야', '서비스명', '핵심 정체성', '강점', '약점', '가격 정책', '요금제 특징']
    for col in cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    return df

df = load_data()

# ---------------------------------------------------------
# 3. 로고 및 URL 처리 로직 (핵심)
# ---------------------------------------------------------
def get_domain_and_logo(tool_row):
    """
    서비스명을 기반으로 도메인과 로고 URL을 추정하는 함수
    엑셀에 'URL' 컬럼이 있다면 그것을 최우선으로 사용합니다.
    """
    service_name = tool_row['서비스명']
    
    # 1. 엑셀에 진짜 URL 정보가 있는 경우 (가장 정확)
    if 'URL' in tool_row and str(tool_row['URL']).startswith('http'):
        target_url = tool_row['URL']
        # 도메인 추출 (예: https://www.vrew.ai/ -> vrew.ai)
        domain = target_url.replace("https://", "").replace("http://", "").split('/')[0]
        logo_url = f"https://logo.clearbit.com/{domain}"
        
    # 2. URL 정보가 없는 경우 (이름으로 추정)
    else:
        # 공백 제거 및 소문자 변환 (예: AI Studio -> aistudio)
        clean_name = service_name.lower().replace(" ", "")
        
        # 임시 URL (URL 컬럼이 없으므로 구글 검색으로 대체하거나 추정 도메인 사용)
        target_url = f"https://www.google.com/search?q={service_name}"
        
        # 로고 추정 (대부분의 AI 서비스는 .ai 또는 .com을 사용)
        # Clearbit API는 도메인을 주면 로고를 줍니다.
        logo_url = f"https://logo.clearbit.com/{clean_name}.com"
    
    return target_url, logo_url

# ---------------------------------------------------------
# 4. 팝업창 (Dialog) 함수 - Streamlit 1.34+ 필요
# ---------------------------------------------------------
@st.dialog("상세 정보")
def show_tool_details(tool):
    st.header(f"🚀 {tool['서비스명']}")
    st.caption(f"분야: {tool['분야']}")
    
    target_url, logo_url = get_domain_and_logo(tool)
    
    # 상단: 로고와 바로가기 버튼
    c1, c2 = st.columns([1, 2])
    with c1:
        # 로고 표시 (에러시 대체 텍스트)
        st.image(logo_url, width=80) 
    with c2:
        st.write("") # 줄맞춤용 공백
        st.link_button("🌐 사이트 바로가기", target_url, type="primary", use_container_width=True)
        if "google" in target_url:
            st.caption("⚠️ 데이터에 URL이 없어 검색 결과로 이동합니다.")

    st.divider()
    
    # 상세 내용
    st.subheader("💡 핵심 정체성")
    st.info(tool.get('핵심 정체성', '내용 없음'))
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("👍 **강점**")
        st.success(tool.get('강점', '-'))
    with col_b:
        st.write("👎 **약점**")
        st.error(tool.get('약점', '-'))
        
    st.write("💰 **가격 정책**")
    st.markdown(f"- 정책: {tool.get('가격 정책', '-')}")
    st.markdown(f"- 특징: {tool.get('요금제 특징', '-')}")


# ---------------------------------------------------------
# 5. 메인 화면 구성
# ---------------------------------------------------------
st.title("🧭 AI Tool Explorer")

if df.empty:
    st.error("데이터 파일을 찾을 수 없습니다.")
    st.stop()

# (1) 상단: 분야 선택 버튼
categories = sorted(df['분야'].unique())
st.markdown("### 1️⃣ 분야를 선택하세요")

# 세션 상태 관리
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = categories[0]

# 카테고리 버튼 나열
cols = st.columns(len(categories))
for idx, cat in enumerate(categories):
    # 버튼이 너무 많으면 줄바꿈 처리가 필요할 수 있음 (여기선 자동 줄바꿈)
    if cols[idx % len(categories)].button(
        cat, 
        key=f"cat_{idx}", 
        type="primary" if st.session_state.selected_category == cat else "secondary"
    ):
        st.session_state.selected_category = cat
        st.rerun()

st.divider()

# (2) 하단: 선택된 분야의 도구 목록
selected_cat = st.session_state.selected_category
st.markdown(f"### 2️⃣ **{selected_cat}** 도구 목록")

tools_in_cat = df[df['분야'] == selected_cat]

# 그리드 레이아웃 (4열)
row_cols = 4
rows = math.ceil(len(tools_in_cat) / row_cols)
tools_list = tools_in_cat.to_dict('records')

for r in range(rows):
    cols = st.columns(row_cols)
    for c in range(row_cols):
        idx = r * row_cols + c
        if idx < len(tools_list):
            tool = tools_list[idx]
            
            # 로고 URL 미리 계산 (버튼 옆에 표시하기 위함)
            _, logo_url = get_domain_and_logo(tool)
            
            with cols[c]:
                # Streamlit 버튼은 내부에 이미지를 넣는 옵션이 제한적입니다.
                # 따라서 이모지나 텍스트로 표현하거나, 커스텀 컴포넌트를 써야 하지만,
                # 여기서는 버튼을 누르면 팝업이 뜨는 구조로 심플하게 갑니다.
                
                # 버튼 레이블에 아이콘 추가 (로고 이미지를 버튼 안에 직접 넣으려면 복잡한 HTML/CSS 필요)
                # 대신, 버튼을 클릭하면 상세 팝업을 띄웁니다.
                
                # 팁: 로고 이미지를 버튼 위에 보여주고 싶다면 st.image 사용
                st.image(logo_url, width=40)
                if st.button(f"{tool['서비스명']}\n(상세보기)", key=f"btn_{idx}"):
                    show_tool_details(tool)

st.markdown("---")
st.caption("데이터에 'URL' 컬럼을 추가하면 더 정확한 로고와 링크 이동이 가능합니다.")