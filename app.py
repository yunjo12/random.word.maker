import streamlit as st
import pandas as pd
import random
import google.generativeai as genai
from PIL import Image
import json

st.set_page_config(page_title="영어 단어 시험지 제작기", layout="wide")

# 세션 상태 초기화
if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")
st.caption("단어 직접 입력, 엑셀 업로드, 사진 업로드로 쉽게 시험지를 만들어보세요.")

# --- SIDEBAR: 입력 및 설정 ---
with st.sidebar:
    st.header("1. 단어 데이터 입력")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력", "사진 업로드 📸", "엑셀 파일 업로드"])
    
    # 1) 직접 입력
    if input_type == "직접 입력":
        raw_text = st.text_area(
            "단어와 뜻을 입력하세요 (예: apple - 사과)",
            height=200,
            value="apple - 사과\ndifficult - 어려운\nbanana - 바나나\nelegantly - 우아하게"
        )
        if st.button("단어 목록에 반영"):
            lines = raw_text.strip().split("\n")
            data = []
            for line in lines:
                if "-" in line:
                    eng, kor = line.split("-", 1)
                    data.append({"영어 단어": eng.strip(), "한국어 뜻": kor.strip()})
            st.session_state.words_df = pd.DataFrame(data)
            st.success(f"{len(data)}개 단어 반영 완료!")

    # 2) 사진 업로드 (Gemini AI 활용)
    elif input_type == "사진 업로드 📸":
        api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
        uploaded_image = st.file_uploader("단어장/교재 사진을 올리세요", type=["jpg", "jpeg", "png"])
        
        if uploaded_image and api_key:
            if st.button("사진에서 단어 추출하기"):
                with st.spinner("AI가 사진 속 단어를 분석 중입니다..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        image = Image.open(uploaded_image)
                        
                        prompt = """
                        이 이미지에서 영어 단어와 한국어 뜻을 추출해줘.
                        반드시 아래와 같은 JSON 배열 형식으로만 응답해줘. 다른 설명은 제외해.
                        [
                          {"영어 단어": "apple", "한국어 뜻": "사과"},
                          {"영어 단어": "banana", "한국어 뜻": "바나나"}
                        ]
                        """
                        response = model.generate_content([image, prompt])
                        clean_res = response.text.replace("```json", "").replace("```", "").strip()
                        word_list = json.loads(clean_res)
                        
                        st.session_state.words_df = pd.DataFrame(word_list)
                        st.success(f"{len(word_list)}개 단어를 사진에서 추출했습니다!")
                    except Exception as e:
                        st.error(f"단어 추출 실패: {e}")
        elif uploaded_image and not api_key:
            st.info("사진 분석을 위해 Google Gemini API Key가 필요합니다.")

    # 3) 엑셀 업로드
    elif input_type == "엑셀 파일 업로드":
        uploaded_file = st.file_uploader("엑셀 (.xlsx, .csv) 파일을 업로드하세요", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
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

# --- MAIN CONTENT ---
tab1, tab2 = st.tabs(["📄 시험지 생성", "📚 단어장 확인"])

with tab2:
    st.subheader("현재 입력된 단어 목록")
    st.dataframe(st.session_state.words_df, use_container_width=True)

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
                eng = row["영어 단어"]
                kor = row["한국어 뜻"]
                
                direction = test_direction
                if direction == "혼합형":
                    direction = random.choice(["영어 → 한국어 (기본)", "한국어 → 영어"])
                    
                if "영어 → 한국어" in direction:
                    quiz_data.append({"번호": q_num, "영어 단어": eng, "뜻": ""})
                    answer_data.append({"번호": q_num, "정답": f"{eng} - {kor}"})
                else:
                    quiz_data.append({"번호": q_num, "한국어 뜻": kor, "영어 단어": ""})
                    answer_data.append({"번호": q_num, "정답": f"{kor} - {eng}"})
                    
            st.session_state.quiz_df = pd.DataFrame(quiz_data)
            st.session_state.answer_df = pd.DataFrame(answer_data)

        if "quiz_df" in st.session_state:
            st.markdown("---")
            st.subheader("📝 영어 단어 시험지")
            st.text(f"범위: 전 범위 | 문제 수: {len(st.session_state.quiz_df)}문제 | 점수: ____ / 100")
            
            st.table(st.session_state.quiz_df)
            
            st.markdown("---")
            with st.expander("🔑 정답지 보기 / 숨기기"):
                st.subheader("정답지")
                st.table(st.session_state.answer_df)
