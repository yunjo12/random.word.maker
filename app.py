import streamlit as st
import pandas as pd
import random
import re
from deep_translator import GoogleTranslator

st.set_page_config(page_title="영어 단어 시험지 제작기", layout="wide")

# --- A4 인쇄 전용 CSS (인쇄 시 배경 흰색 고정 및 불필요한 UI 숨김) ---
st.markdown("""
    <style>
    @media print {
        body, .stApp, div {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        [data-testid="stSidebar"], 
        header, 
        footer, 
        .stButton, 
        .stTabs,
        [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
        }
        table, th, td {
            color: #000000 !important;
            border-color: #cccccc !important;
            background-color: #ffffff !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 자동 번역 함수
@st.cache_data(show_spinner=False)
def translate_word(word):
    try:
        translated = GoogleTranslator(source='en', target='ko').translate(word)
        return translated
    except Exception:
        return ""

if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")

# --- SIDEBAR: 입력 및 설정 ---
with st.sidebar:
    st.header("1. 단어 데이터 입력")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력", "엑셀 파일 업로드"])
    
    if input_type == "직접 입력":
        raw_text = st.text_area(
            "단어를 입력하세요 (단어만 적어도 뜻이 자동 생성됩니다)",
            height=250,
            value=""
        )
        if st.button("단어 목록에 반영"):
            lines = raw_text.strip().split("\n")
            data = []
            
            with st.spinner("단어 뜻을 자동으로 검색 중입니다..."):
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # '1. provide 21. aim' 형태 자동 분리
                    items = re.split(r'\s+(?=\d+\.)', line)
                    
                    for item in items:
                        item = item.strip()
                        clean_item = re.sub(r'^\d+\.\s*', '', item)
                        
                        if not clean_item:
                            continue
                            
                        if "-" in clean_item:
                            eng, kor = clean_item.split("-", 1)
                            eng, kor = eng.strip(), kor.strip()
                        elif ":" in clean_item:
                            eng, kor = clean_item.split(":", 1)
                            eng, kor = eng.strip(), kor.strip()
                        else:
                            eng = clean_item.strip()
                            # 뜻이 직접 작성되지 않은 경우 자동 번역
                            kor = translate_word(eng)
                            
                        data.append({"영어 단어": eng, "한국어 뜻": kor})
                
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
                    
                # 엑셀 파일 내 빈 뜻 자동 채우기
                with st.spinner("빈 뜻을 자동으로 채우는 중입니다..."):
                    for idx, row in df.iterrows():
                        if not str(row["한국어 뜻"]).strip():
                            df.at[idx, "한국어 뜻"] = translate_word(str(row["영어 단어"]))
                            
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
    st.subheader("현재 입력된 단어 목록 (자동 완성된 뜻 포함)")
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
                q_num = idx + 1
                eng = row.get("영어 단어", "")
                kor = row.get("한국어 뜻", "")
                
                direction = test_direction
                if direction == "혼합형":
                    direction = random.choice(["영어 → 한국어 (기본)", "한국어 → 영어"])
                    
                if "영어 → 한국어" in direction:
                    quiz_data.append({"번호": q_num, "영어 단어": eng, "뜻": ""})
                else:
                    quiz_data.append({"번호": q_num, "한국어 뜻": kor if kor else "뜻 없음", "영어 단어": ""})
                    
                answer_data.append({"번호": q_num, "정답": f"{eng} - {kor}" if kor else eng})
                    
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
            # 정답지 섹션 (번호 + 영어/뜻 포함)
            with st.expander("🔑 정답지 보기 / 숨기기"):
                st.subheader("🔑 정답지")
                st.table(st.session_state.answer_df)
