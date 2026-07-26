import streamlit as st
import pandas as pd
import random
import re

st.set_page_config(page_title="영어 단어 시험지 제작기", layout="wide")

# --- A4 인쇄용 스타일 적용 (인쇄 시 사이드바 및 버튼 숨김) ---
st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], 
        header, 
        footer, 
        .stButton, 
        [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")

# --- SIDEBAR: 입력 및 설정 ---
with st.sidebar:
    st.header("1. 단어 데이터 입력")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력", "엑셀 파일 업로드"])
    
    if input_type == "직접 입력":
        raw_text = st.text_area(
            "단어를 입력하세요 (줄바꿈/한 줄 여러 개 모두 가능)",
            height=250,
            value=""
        )
        if st.button("단어 목록에 반영"):
            lines = raw_text.strip().split("\n")
            data = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # '1. provide 21. aim' 형태 자동 분리
                items = re.split(r'\s+(?=\d+\.)', line)
                
                for item in items:
                    item = item.strip()
                    # 앞에 붙은 번호 제거
                    clean_item = re.sub(r'^\d+\.\s*', '', item)
                    
                    if not clean_item:
                        continue
                        
                    if "-" in clean_item:
                        eng, kor = clean_item.split("-", 1)
                    elif ":" in clean_item:
                        eng, kor = clean_item.split(":", 1)
                    else:
                        eng = clean_item
                        kor = ""
                        
                    data.append({"영어 단어": eng.strip(), "한국어 뜻": kor.strip()})
                
            st.session_state.words_df = pd.DataFrame(data)
            st.success(f"{len(data)}개 단어 반영 완료!")

    elif input_type == "엑셀 파일 업로드":
        uploaded_file = st.file_uploader("엑셀 (.xlsx, .csv) 파일을 업로드하세요", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                if "한국어 뜻" not in df.columns:
                    df["한국어 뜻"] = ""
                    
                st.session_state.words_df = df
                st.success("파일 업로드 성공!")
            except Exception as e:
                st.error("파일을 읽는 중 오류가 발생했습니다.")

    st.markdown("---")
    st.header("2. 시험지 옵션 설정")
    test_direction = st.selectbox(
        "시험 방향 선택:",
        ["영어 → 한국어 (기본)", "한국어 → 영어", "혼합형"]
    )
    
    word_count = len(st.session_state.words_df)
    if word_count > 0:
        max_q = st.number_input("문제 수 설정", min_value=1, max_value=word_count, value=word_count)
    else:
        max_q = 0

tab1, tab2 = st.tabs(["📄 시험지 생성", "📚 단어장 확인"])

with tab2:
    st.subheader("현재 입력된 단어 목록")
    # 1번부터 표시
    df_display = st.session_state.words_df.copy()
    df_display.index = range(1, len(df_display) + 1)
    st.dataframe(df_display, use_container_width=True)

with tab1:
    if st.session_state.words_df.empty:
        st.warning("왼쪽 사이드바에서 먼저 단어 데이터를 입력해주세요.")
    else:
        if st.button("🎲 새로운 시험지 만들기 (랜덤 섞기)", type="primary"):
            sample_df = st.session_state.words_df.sample(n=max_q).reset_index(drop=True)
            
            quiz_data = []
            answer_data = []
            
            for idx, row in sample_df.iterrows():
                q_num = idx + 1  # 1번부터 시작되도록 고정
                eng = row.get("영어 단어", "")
                kor = row.get("한국어 뜻", "")
                
                direction = test_direction
                if direction == "혼합형":
                    direction = random.choice(["영어 → 한국어 (기본)", "한국어 → 영어"])
                    
                if "영어 → 한국어" in direction:
                    quiz_data.append({"번호": q_num, "영어 단어": eng, "뜻": ""})
                    answer_data.append({"번호": q_num, "정답": f"{eng} - {kor}" if kor else eng})
                else:
                    quiz_data.append({"번호": q_num, "한국어 뜻": kor, "영어 단어": ""})
                    answer_data.append({"번호": q_num, "정답": f"{kor} - {eng}" if kor else eng})
                    
            # 표의 인덱스도 1번부터 표시되도록 설정
            q_df = pd.DataFrame(quiz_data).set_index("번호")
            a_df = pd.DataFrame(answer_data).set_index("번호")
            
            st.session_state.quiz_df = q_df
            st.session_state.answer_df = a_df

        if "quiz_df" in st.session_state:
            st.markdown("---")
            st.subheader("📝 영어 단어 시험지")
            st.text(f"범위: 전 범위 | 문제 수: {len(st.session_state.quiz_df)}문제 | 점수: ____ / 100")
            
            # 시험지 출력
            st.table(st.session_state.quiz_df)
            
            st.markdown("---")
            with st.expander("🔑 정답지 보기 / 숨기기"):
                st.subheader("정답지")
                st.table(st.session_state.answer_df)
