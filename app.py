import streamlit as st
import pandas as pd
import random
import re
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

# 인쇄용 HTML 문서 생성 함수
def generate_print_html(df, title, is_answer=False):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; padding: 20px; color: #000; }}
            h2 {{ text-align: center; margin-bottom: 5px; }}
            .sub-info {{ text-align: right; font-size: 13px; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #333; padding: 10px 12px; text-align: left; font-size: 14px; }}
            th {{ background-color: #f2f2f2; font-weight: bold; text-align: center; }}
            .num-col {{ width: 10%; text-align: center; }}
            @media print {{
                body {{ padding: 0; }}
                @page {{ size: A4; margin: 15mm; }}
            }}
        </style>
    </head>
    <body>
        <h2>{title}</h2>
        <div class="sub-info">
            범위: 전 범위 | 문제 수: {len(df)}문제 | 점수: ____ / 100
        </div>
        <table>
            <thead>
                <tr>
                    <th class="num-col">번호</th>
                    {"<th>정답</th>" if is_answer else "<th>영어 단어</th><th>한국어 뜻 (작성)</th>"}
                </tr>
            </thead>
            <tbody>
    """
    for idx, row in df.iterrows():
        q_num = idx
        if is_answer:
            ans = row.get("정답", "")
            html_content += f"<tr><td class='num-col'>{q_num}</td><td>{ans}</td></tr>"
        else:
            eng = row.get("영어 단어", "")
            kor = row.get("뜻", "")
            html_content += f"<tr><td class='num-col'>{q_num}</td><td>{eng}</td><td>{kor}</td></tr>"
            
    html_content += """
            </tbody>
        </table>
        <script>
            window.onload = function() { window.print(); }
        </script>
    </body>
    </html>
    """
    return html_content

# 세션 상태 초기화 (누적 단어 데이터프레임)
if "words_df" not in st.session_state:
    st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])

st.title("📝 맞춤형 영어 단어 시험지 제작기")

# --- SIDEBAR: 입력 및 설정 ---
with st.sidebar:
    st.header("1. 단어 데이터 추가")
    input_type = st.radio("입력 방식을 선택하세요:", ["직접 입력", "엑셀 파일 업로드"])
    
    if input_type == "직접 입력":
        raw_text = st.text_area(
            "단어를 입력하세요 (한 줄에 하나 또는 '1. apple 21. aim' 형태 가능)",
            height=200,
            value=""
        )
        if st.button("➕ 누적 단어장에 추가"):
            lines = raw_text.strip().split("\n")
            new_data = []
            
            with st.spinner("단어 뜻을 자동으로 검색하여 수집 중..."):
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
                # 기존 누적 데이터와 합치기 (중복 제거)
                combined = pd.concat([st.session_state.words_df, new_df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"]).reset_index(drop=True)
                st.success(f"{len(new_data)}개 단어가 단어장에 추가되었습니다!")

    elif input_type == "엑셀 파일 업로드":
        uploaded_file = st.file_uploader("엑셀 (.xlsx, .csv) 파일을 업로드하세요", type=["xlsx", "csv"])
        if uploaded_file is not None and st.button("📥 엑셀 단어 추가"):
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
                            
                combined = pd.concat([st.session_state.words_df, df], ignore_index=True)
                st.session_state.words_df = combined.drop_duplicates(subset=["영어 단어"]).reset_index(drop=True)
                st.success("엑셀 단어가 누적 단어장에 추가되었습니다!")
            except Exception as e:
                st.error("파일을 읽는 중 오류가 발생했습니다.")

    st.markdown("---")
    st.header("2. 시험지 출제 옵션")
    test_direction = st.selectbox(
        "시험 방향 선택:",
        ["영어 → 한국어 (기본)", "한국어 → 영어", "혼합형"]
    )
    
    word_count = len(st.session_state.words_df)
    if word_count > 0:
        max_q = st.number_input("출제 문제 수 설정", min_value=1, max_value=word_count, value=word_count)
    else:
        max_q = 0

# --- MAIN TAB ---
tab1, tab2 = st.tabs(["📄 시험지 생성 및 인쇄", "📚 전체 단어장 정리/관리"])

# --- TAB 2: 단어장 정리 및 관리 ---
with tab2:
    st.subheader(f"📚 지금까지 입력한 단어 목록 (총 {len(st.session_state.words_df)}개)")
    
    if not st.session_state.words_df.empty:
        # 단어장 편집 기능 (데이터프레임 수정 가능)
        edited_df = st.data_editor(
            st.session_state.words_df,
            num_rows="dynamic",
            use_container_width=True,
            key="word_editor"
        )
        st.session_state.words_df = edited_df
        
        col1, col2 = st.columns(2)
        with col1:
            # 엑셀 다운로드
            csv = st.session_state.words_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 단어장 전체 CSV로 저장하기",
                data=csv,
                file_name="my_wordlist.csv",
                mime="text/csv"
            )
        with col2:
            if st.button("🗑️ 단어장 전체 비우기 (초기화)"):
                st.session_state.words_df = pd.DataFrame(columns=["영어 단어", "한국어 뜻"])
                st.experimental_rerun()
    else:
        st.info("아직 입력된 단어가 없습니다. 왼쪽 사이드바에서 단어를 추가해 보세요.")

# --- TAB 1: 시험지 생성 및 인쇄 ---
with tab1:
    if st.session_state.words_df.empty:
        st.warning("먼저 단어를 입력하여 단어장을 채워주세요.")
    else:
        if st.button("🎲 단어 랜덤 섞기 & 시험지 생성", type="primary"):
            sample_df = st.session_state.words_df.sample(n=max_q).reset_index(drop=True)
            
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
                    
            q_df = pd.DataFrame(quiz_data).set_index("번호")
            a_df = pd.DataFrame(answer_data).set_index("번호")
            
            st.session_state.quiz_df = q_df
            st.session_state.answer_df = a_df

        if "quiz_df" in st.session_state:
            st.markdown("---")
            st.subheader("📝 영어 단어 시험지 미리보기")
            st.text(f"범위: 전 범위 | 문제 수: {len(st.session_state.quiz_df)}문제")
            
            st.table(st.session_state.quiz_df)
            
            # 인쇄 전용 다운로드 버튼 (A4 출력)
            st.markdown("### 🖨️ 깔끔한 A4 시험지 인쇄하기")
            print_html_quiz = generate_print_html(st.session_state.quiz_df, "영어 단어 시험지", is_answer=False)
            st.download_button(
                label="🖨️ [시험지] 클릭하여 깔끔하게 인쇄하기 (HTML)",
                data=print_html_quiz,
                file_name="word_test_sheet.html",
                mime="text/html"
            )
            
            st.markdown("---")
            with st.expander("🔑 정답지 보기 / 인쇄하기"):
                st.subheader("🔑 정답지 미리보기")
                st.table(st.session_state.answer_df)
                
                print_html_ans = generate_print_html(st.session_state.answer_df, "영어 단어 시험지 정답지", is_answer=True)
                st.download_button(
                    label="🖨️ [정답지] 클릭하여 깔끔하게 인쇄하기 (HTML)",
                    data=print_html_ans,
                    file_name="word_test_answer.html",
                    mime="text/html"
                )
