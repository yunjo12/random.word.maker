import streamlit as st
import pandas as pd
import random
import re
from deep_translator import GoogleTranslator

st.set_page_config(page_title="맞춤형 영어 단어 시험지 제작기", layout="wide")

# --- A4 2열(2줄) 인쇄 전용 CSS ---
st.markdown("""
    <style>
    @media print {
        body, .stApp, div, iframe {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        [data-testid="stSidebar"], 
        header, 
        footer, 
        .stButton, 
        .stTabs,
        .no-print,
        [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
        }
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin-bottom: 10px !important;
        }
        th, td {
            border: 1px solid #000000 !important;
            padding: 6px 8px !important;
            font-size: 13px !important;
            color: #000000 !important;
        }
        th {
            background-color: #f2f2f2 !important;
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

# 세션 상태 초기화
if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])
if "current_words_df" not in st.session_state:
    st.session_state.current_words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")

# --- SIDEBAR: 입력 및 설정 ---
with st.sidebar:
    st.header("1. 단어 데이터 입력")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력", "엑셀 파일 업로드"])
    
    if input_type == "직접 입력":
        raw_text = st.text_area(
            "단어를 입력하세요",
            height=200,
            value=""
        )
        if st.button("📥 단어 반영 (중복 시 덮어쓰기)"):
            lines = raw_text.strip().split("\n")
            new_data = []
            
            with st.spinner("단어 뜻을 자동으로 검색 중..."):
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
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
                            kor = translate_word(eng)
                            
                        new_data.append({"영어 단어": eng, "한국어 뜻": kor})
                
            if new_data:
                new_df = pd.DataFrame(new_data)
                st.session_state.current_words_df = new_df
                
                # 누적 데이터에 중복 덮어쓰기로 합치기
                combined = pd.concat([st.session_state.words_df, new_df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"], keep="last").reset_index(drop=True)
                st.success(f"{len(new_data)}개 단어가 반영되었습니다!")

    elif input_type == "엑셀 파일 업로드":
        uploaded_file = st.file_uploader("엑셀 (.xlsx, .csv) 파일을 업로드하세요", type=["xlsx", "csv"])
        if uploaded_file is not None and st.button("📥 엑셀 단어 반영"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                if "한국어 뜻" not in df.columns:
                    df["한국어 뜻"] = ""
                    
                with st.spinner("뜻이 없는 단어 자동 채우는 중..."):
                    for idx, row in df.iterrows():
                        if not str(row["한국어 뜻"]).strip():
                            df.at[idx, "한국어 뜻"] = translate_word(str(row["영어 단어"]))
                            
                st.session_state.current_words_df = df
                combined = pd.concat([st.session_state.words_df, df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"], keep="last").reset_index(drop=True)
                st.success("엑셀 단어가 반영되었습니다!")
            except Exception as e:
                st.error("파일을 읽는 중 오류가 발생했습니다.")

    st.markdown("---")
    st.header("2. 시험지 출제 옵션")
    
    test_target = st.radio(
        "출제할 단어 범위:",
        ["방금 입력한 단어만", "누적 전체 단어장"]
    )
    
    test_direction = st.selectbox(
        "시험 방향 선택:",
        ["영어 → 한국어 (기본)", "한국어 → 영어", "혼합형"]
    )
    
    target_df = st.session_state.current_words_df if test_target == "방금 입력한 단어만" else st.session_state.words_df
    
    word_count = len(target_df)
    if word_count > 0:
        max_q = st.number_input("출제 문제 수 설정", min_value=1, max_value=word_count, value=word_count)
    else:
        max_q = 0

# --- MAIN CONTENT ---
tab1, tab2 = st.tabs(["📄 시험지 생성 및 인쇄", "📚 전체 단어장 정리/관리"])

with tab2:
    st.subheader(f"📚 지금까지 누적된 단어 목록 (총 {len(st.session_state.words_df)}개)")
    if not st.session_state.words_df.empty:
        edited_df = st.data_editor(
            st.session_state.words_df,
            num_rows="dynamic",
            use_container_width=True,
            key="word_editor"
        )
        st.session_state.words_df = edited_df
        
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state.words_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 단어장 전체 CSV 다운로드", csv, "my_wordlist.csv", "text/csv")
        with col2:
            if st.button("🗑️ 단어장 전체 초기화"):
                st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])
                st.session_state.current_words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])
                st.rerun()

with tab1:
    target_df = st.session_state.current_words_df if test_target == "방금 입력한 단어만" else st.session_state.words_df
    
    if target_df.empty:
        st.warning("선택한 범위에 단어가 없습니다. 사이드바에서 단어를 입력해 주세요.")
    else:
        if st.button("🎲 단어 랜덤 섞기 & 시험지 생성", type="primary"):
            sample_df = target_df.sample(n=max_q).reset_index(drop=True)
            
            quiz_data = []
            answer_data = []
            
            for idx, row in sample_df.iterrows():
                q_num = idx + 1
                eng = str(row.get("영어 단어", ""))
                kor = str(row.get("한국어 뜻", ""))
                
                direction = test_direction
                if direction == "혼합형":
                    direction = random.choice(["영어 → 한국어 (기본)", "한국어 → 영어"])
                    
                if "영어 → 한국어" in direction:
                    quiz_data.append({"번호": q_num, "영어 단어": eng, "뜻": ""})
                else:
                    quiz_data.append({"번호": q_num, "한국어 뜻": kor if kor else "뜻 없음", "영어 단어": ""})
                    
                answer_data.append({"번호": q_num, "정답": f"{eng} - {kor}" if kor else eng})
                    
            st.session_state.quiz_df = pd.DataFrame(quiz_data).set_index("번호")
            st.session_state.answer_df = pd.DataFrame(answer_data).set_index("번호")

        if "quiz_df" in st.session_state:
            st.markdown("---")
            st.subheader("📝 영어 단어 시험지 미리보기")
            st.caption("💡 Ctrl + P를 누르시면 백지 없이 종이에 깔끔하게 2열(2줄)로 출력됩니다!")
            
            df_quiz = st.session_state.quiz_df
            half_len = (len(df_quiz) + 1) // 2
            
            col1_df = df_quiz.iloc[:half_len]
            col2_df = df_quiz.iloc[half_len:]
            
            st.text(f"범위: 전 범위 | 문제 수: {len(df_quiz)}문제 | 점수: ____ / 100")
            
            # 2열(2줄) 레이아웃
            col_left, col_right = st.columns(2)
            with col_left:
                st.table(col1_df)
            with col_right:
                if not col2_df.empty:
                    st.table(col2_df)
            
            st.markdown("---")
            with st.expander("🔑 정답지 보기"):
                st.subheader("🔑 정답지")
                df_ans = st.session_state.answer_df
                half_ans_len = (len(df_ans) + 1) // 2
                ans_col1 = df_ans.iloc[:half_ans_len]
                ans_col2 = df_ans.iloc[half_ans_len:]
                
                ans_left, ans_right = st.columns(2)
                with ans_left:
                    st.table(ans_col1)
                with ans_right:
                    if not ans_col2.empty:
                        st.table(ans_col2)
