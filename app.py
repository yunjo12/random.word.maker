import streamlit as st
import pandas as pd
import random
import re
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator

st.set_page_config(page_title="맞춤형 영어 단어 시험지 제작기", layout="wide")

# 자동 번역 함수
@st.cache_data(show_spinner=False)
def translate_word(word):
    try:
        translated = GoogleTranslator(source='en', target='ko').translate(word)
        return translated
    except Exception:
        return ""

# 인쇄용 A4 2열 HTML 생성 함수
def build_print_html(df, title, is_answer=False):
    half = (len(df) + 1) // 2
    col1_df = df.iloc[:half]
    col2_df = df.iloc[half:]

    def make_table_rows(data):
        rows_html = ""
        for idx, row in data.iterrows():
            q_num = idx
            if is_answer:
                ans = row.get("정답", "")
                rows_html += f"<tr><td class='num-col'>{q_num}</td><td>{ans}</td></tr>"
            else:
                eng = row.get("영어 단어", "")
                kor = row.get("한국어 뜻", "") if "한국어 뜻" in row else row.get("뜻", "")
                rows_html += f"<tr><td class='num-col'>{q_num}</td><td>{eng}</td><td>{kor}</td></tr>"
        return rows_html

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Malgun Gothic', sans-serif;
                margin: 0;
                padding: 10px;
                color: #000000;
                background-color: #ffffff;
            }}
            .header {{
                text-align: center;
                margin-bottom: 10px;
            }}
            .header h2 {{
                margin: 0 0 5px 0;
            }}
            .info {{
                text-align: right;
                font-size: 12px;
                border-bottom: 2px solid #000;
                padding-bottom: 5px;
                margin-bottom: 15px;
            }}
            .grid-container {{
                display: flex;
                gap: 20px;
            }}
            .grid-col {{
                flex: 1;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #333;
                padding: 6px 8px;
                font-size: 13px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                text-align: center;
            }}
            .num-col {{
                width: 12%;
                text-align: center;
            }}
            .print-btn {{
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin-bottom: 15px;
            }}
            @media print {{
                .print-btn {{
                    display: none !important;
                }}
            }}
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ 인쇄하기 (Ctrl+P)</button>
        <div class="header">
            <h2>{title}</h2>
        </div>
        <div class="info">
            범위: 전 범위 | 문제 수: {len(df)}문제 | 점수: ____ / 100
        </div>
        <div class="grid-container">
            <div class="grid-col">
                <table>
                    <thead>
                        <tr>
                            <th class="num-col">번호</th>
                            {"<th>정답</th>" if is_answer else "<th>영어 단어</th><th>한국어 뜻</th>"}
                        </tr>
                    </thead>
                    <tbody>
                        {make_table_rows(col1_df)}
                    </tbody>
                </table>
            </div>
            <div class="grid-col">
                {"<table><thead><tr><th class='num-col'>번호</th>" + ("<th>정답</th>" if is_answer else "<th>영어 단어</th><th>한국어 뜻</th>") + "</tr></thead><tbody>" + make_table_rows(col2_df) + "</tbody></table>" if not col2_df.empty else ""}
            </div>
        </div>
    </body>
    </html>
    """
    return html_code

# 세션 초기화
if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])
if "current_words_df" not in st.session_state:
    st.session_state.current_words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. 단어 데이터 입력")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력 (목록/뜻)", "문장/글귀 통째로 입력", "엑셀 파일 업로드"])
    
    if input_type == "직접 입력 (목록/뜻)":
        raw_text = st.text_area("단어를 입력하세요 (예: apple - 사과)", height=200, value="")
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
                
                combined = pd.concat([st.session_state.words_df, new_df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"], keep="last").reset_index(drop=True)
                st.success(f"{len(new_data)}개 단어가 반영되었습니다!")

    elif input_type == "문장/글귀 통째로 입력":
        raw_passage = st.text_area("영어 문장이나 긴 글을 붙여넣으세요", height=200, value="")
        if st.button("✂️ 문장 분해하여 단어장에 추가"):
            if raw_passage.strip():
                # 영문 알파벳과 하이픈만 추출하여 단어 분해 (소문자 변환)
                extracted_words = re.findall(r'\b[a-zA-A-Za-z-]+\b', raw_passage)
                # 알파벳 2자 이상만 필터링 및 중복 제거
                unique_words = sorted(list(set([w.lower() for w in extracted_words if len(w) > 1])))
                
                new_data = []
                with st.spinner(f"총 {len(unique_words)}개 단어를 분해하고 뜻을 찾는 중..."):
                    for w in unique_words:
                        kor = translate_word(w)
                        new_data.append({"영어 단어": w, "한국어 뜻": kor})
                
                if new_data:
                    new_df = pd.DataFrame(new_data)
                    st.session_state.current_words_df = new_df
                    
                    combined = pd.concat([st.session_state.words_df, new_df], ignore_index=True)
                    st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"], keep="last").reset_index(drop=True)
                    st.success(f"문장에서 총 {len(new_data)}개의 단어를 추출하여 저장했습니다!")
            else:
                st.warning("문장을 입력해 주세요.")

    elif input_type == "엑셀 파일 업로드":
        uploaded_file = st.file_uploader("엑셀 (.xlsx, .csv) 파일 업로드", type=["xlsx", "csv"])
        if uploaded_file is not None and st.button("📥 엑셀 단어 반영"):
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                if "한국어 뜻" not in df.columns:
                    df["한국어 뜻"] = ""
                    
                with st.spinner("뜻 자동 채우는 중..."):
                    for idx, row in df.iterrows():
                        if not str(row["한국어 뜻"]).strip():
                            df.at[idx, "한국어 뜻"] = translate_word(str(row["영어 단어"]))
                            
                st.session_state.current_words_df = df
                combined = pd.concat([st.session_state.words_df, df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"], keep="last").reset_index(drop=True)
                st.success("엑셀 단어가 반영되었습니다!")
            except Exception:
                st.error("파일을 읽는 중 오류가 발생했습니다.")

    st.markdown("---")
    st.header("2. 시험지 출제 옵션")
    test_target = st.radio("출제할 단어 범위:", ["방금 입력한 단어만", "누적 전체 단어장"])
    test_direction = st.selectbox("시험 방향 선택:", ["영어 → 한국어 (기본)", "한국어 → 영어", "혼합형"])
    
    target_df = st.session_state.current_words_df if test_target == "방금 입력한 단어만" else st.session_state.words_df
    word_count = len(target_df)
    max_q = st.number_input("출제 문제 수 설정", min_value=1, max_value=word_count, value=word_count) if word_count > 0 else 0

# --- MAIN TAB ---
tab1, tab2 = st.tabs(["📄 시험지 생성 및 인쇄", "📚 전체 단어장 정리/관리"])

with tab2:
    st.subheader(f"📚 누적된 단어 목록 (총 {len(st.session_state.words_df)}개)")
    if not st.session_state.words_df.empty:
        edited_df = st.data_editor(st.session_state.words_df, num_rows="dynamic", use_container_width=True, key="word_editor")
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
        st.warning("선택한 범위에 단어가 없습니다. 사이드바에서 단어를 먼저 입력해 주세요.")
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
            st.subheader("📝 영어 단어 시험지 (2열 배치)")
            
            quiz_html = build_print_html(st.session_state.quiz_df, "영어 단어 시험지", is_answer=False)
            components.html(quiz_html, height=600, scrolling=True)
            
            st.markdown("---")
            with st.expander("🔑 정답지 보기 및 인쇄"):
                st.subheader("🔑 정답지 (2열 배치)")
                ans_html = build_print_html(st.session_state.answer_df, "영어 단어 시험지 정답지", is_answer=True)
                components.html(ans_html, height=500, scrolling=True)
