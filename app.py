import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import base64

# 페이지 설정
st.set_page_config(layout="wide", page_title="AI 캐릭터 프롬프트 마스터 v4.9")

st.title("🤖 AI 캐릭터 프롬프트 마스터 v4.9")
st.markdown("멀티 포맷 | 절대 규칙 | 외국어 대응 | 문체 엔진 | 도입부 리라이팅 | **F3 궁극의 템플릿 적용**")

# --- [사이드바] 설정 영역 ---
with st.sidebar:
    st.header("⚙️ 기본 & 출력 설정")
    
    api_key = st.text_input("Gemini API Key", type="password")
    
    if 'model_list' not in st.session_state:
        st.session_state['model_list'] = ["gemini-1.5-flash", "gemini-1.5-pro"]

    if st.button("🔄 모델 목록 갱신"):
        if not api_key:
            st.error("API 키를 먼저 입력해주세요.")
        else:
            try:
                genai.configure(api_key=api_key)
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if models:
                    st.session_state['model_list'] = models
                    st.success("완료!")
            except Exception as e:
                st.error(f"오류: {e}")

    model_choice = st.selectbox("사용할 모델", st.session_state['model_list'], index=0)

    st.divider()

    format_option = st.radio(
        "📝 출력 템플릿 형식",
        (
            "Format 1 (문서/섹션 분리형)", 
            "Format 2 (넘버링/직관형)",
            "Format 3 (상세 구조화 템플릿 - 추천)"
        ),
        index=2
    )
    
    out_lang_option = st.radio(
        "🗣️ 프롬프트 출력 언어",
        ("영어 (English - AI 인식률 높음)", "한국어 (Korean - 가독성/수정 편함)"),
        index=1
    )

    st.divider()

    bracket_option = st.radio("치환 변수", ("{{char}}, {{user}}", "{char}, {user}"), index=0)
    
    st.markdown("### 🌐 외국어 캐릭터 설정")
    is_foreign = st.checkbox("이 캐릭터는 외국어를 사용합니까?")
    foreign_lang = ""
    if is_foreign:
        foreign_lang = st.text_input("사용 언어 (예: 일본어, 중국어, 프랑스어)", value="일본어")


# --- [메인] 탭 입력 영역 ---
tab_char, tab_style, tab_world = st.tabs(["1. 캐릭터 정보", "2. 심화 문체", "3. 세계관 및 시나리오"])

with tab_char:
    st.subheader("👤 캐릭터 기본 설정")
    char_name = st.text_input("캐릭터 이름", value="리웨이")
    
    raw_profile = st.text_area("캐릭터 프로필 (외모, 성격, 특징)", height=300, 
        placeholder="이름, 나이, 직업, 성격, 외모 등 상세히 작성 (AI가 구조화 해줌)")
    
    raw_secret = st.text_area("🔒 비밀 및 내면 동기", height=150,
        placeholder="비밀 설정, 숨겨진 목적, 위장 등")

with tab_style:
    st.subheader("🖋️ 심화 문체 및 서술 지침")
    st.info("💡 비워두면 AI가 캐릭터와 세계관을 분석해 가장 어울리는 작가와 수사법을 자동으로 기획합니다.")
    raw_style = st.text_area("원하는 문체 방향 (선택 사항)", height=200,
        placeholder="예: 하드보일드 느낌으로, 건조하고 짧은 문장. 감정선은 은유적으로 표현할 것.")

with tab_world:
    st.subheader("🌍 세계관 및 상황")
    st.info("💡 장황한 설정집이나 소설식 배경을 넣어도 디테일 생략 없이 완벽히 요약/압축해줍니다.")
    raw_world = st.text_area("세계관 (Worldview)", height=300,
        placeholder="시대 배경, 특이 설정, 현재의 상황적 배경 등")
    
    st.markdown("---")
    st.write("🎞️ **도입부 텍스트 (Opening Text)**")
    raw_intro = st.text_area("도입부 내용 (소설 형식 혹은 요약)", height=250,
        placeholder="예: 카페 문이 열리고 그가 들어왔다. 나를 찾은 모양이다.")

generate_btn = st.button("✨ 마스터 프롬프트 생성하기", type="primary", use_container_width=True)


# --- [로직] 프롬프트 빌더 ---
def build_prompt(fmt, brackets, is_foreign_char, lang_name, out_lang):
    char_var = brackets.split(",")[0].strip()
    user_var = brackets.split(",")[1].split("(")[0].strip()
    is_korean = "한국어" in out_lang
    is_format_3 = "Format 3" in fmt

    # ==========================================
    # 1. 코어 룰 (Format 1 & 2 용)
    # ==========================================
    if not is_format_3:
        if is_korean:
            core_rules_text = f"""
        1. 페이스 조절 (Pacing): 모든 서사 전개, 감정선 변화, 관계의 진전은 점진적이고 개연성 있게 이루어져야 한다. 갑작스러운 고백, 급격한 감정 변화, 개연성 없는 스킨십을 피할 것. 모든 장면 전환은 자연스러워야 하며 이전 맥락을 바탕으로 전개되어야 한다.
        2. 캐릭터 무결성 (Character Integrity): 프롬프트에 정의된 {char_var}의 성격을 철저히 유지할 것. 감정은 노골적인 언어보다는 미묘한 행동이나 내면의 생각, 뉘앙스를 통해 표현할 것. 과장 없이 핵심 특성을 유지하라.
        3. 묘사 스타일 (Descriptive Style): 캐릭터 프로필을 서사에 자연스럽게 녹여낼 것. "보여주기(Showing)" 원칙을 철저히 지켜 감각과 행동 위주로 묘사하라.
        4. 유저 주도권 (User Agency): 유저의 행동, 말, 감정을 대신 묘사하지 말 것. 유저 캐릭터의 통제권은 전적으로 유저에게 있다.
            """
        else:
            core_rules_text = f"""
        1. Pacing: All plot developments, emotional shifts, and relationship dynamics must unfold gradually and logically.
        2. Character Integrity: Portray {char_var}'s personality as defined. Express emotions subtly, through nuanced actions or internal thoughts, rather than overt language.
        3. Descriptive Style: Weave character profiles into the narrative organically. Focus on "showing," not "telling."
        4. User Agency: Do not describe the user's actions, speech, or feelings.
            """
        core_rules_instruction = f"[Core Rules 작성 지침]\n위 4가지 원칙을 프롬프트 최상단에 포함하되 캐릭터 성격에 맞게 다듬어라.\n{core_rules_text}"
    else:
        # Format 3는 하드코딩된 영문 규칙을 바로 템플릿에 꽂아넣으므로 별도 지시 생략
        core_rules_instruction = ""

    # ==========================================
    # 2. 외국어 화자 규칙
    # ==========================================
    foreign_instruction = ""
    if is_foreign_char:
        if not is_format_3:
            foreign_instruction = f"""
            [외국어 화자 규칙 작성 지침]
            - {char_var}의 대사 형식: `"{lang_name} 대사" (한국어 번역)`.
            - 직역 금지. {char_var} 성격이 반영된 의역 수행.
            - 직역(❌ Bad)과 의역(✅ Good) 예시 창작 기재.
            """
        else:
            foreign_instruction = f"""
            [외국어 화자 규칙 작성 지침 - Format 3 전용]
            이 캐릭터는 {lang_name} 화자입니다. `# Language Rules` 섹션에 아래의 템플릿 포맷을 **100% 동일하게** 작성하되, `Examples`의 예시 대사만 {char_var}의 성격과 {lang_name}에 맞춰 당신이 창작해 넣으십시오.
            """

    # ==========================================
    # 3. 공통 지침 (압축, 문체, 리라이팅)
    # ==========================================
    world_instruction = """
    [세계관(Worldview) 초압축 보존 지침]
    사용자가 입력한 세계관을 뭉뚱그려 요약하지 마십시오. 모든 세부 설정(규칙, 고유명사)을 보존하되 기호(=, /, ·)를 사용하여 '초압축 속성표 데이터' 형태로 변환하십시오.
    """

    style_engine = """
    [심화 문체(Style Guide) 기획 지침]
    입력된 데이터를 분석하여, 가장 어울리는 문체 규칙(시점, 톤, 묘사 원칙, 대사 규칙 등)을 생성하라.
    Format 3의 경우, 기획된 문체를 바탕으로 `Tone Examples` (장면 유형 A, B, C)에 들어갈 예시 문장을 창작하여 기재하라.
    """

    rewriting_instruction = f"""
    [도입부 리라이팅 (First Message Rewriting) 지침]
    1. 상황 요약(Scenario): 도입부의 장소/시간/캐릭터상태 등을 건조하게 요약.
    2. 첫 메시지(First Message): 기획된 문체를 200% 적용하여 문학적으로 재창조된 봇의 첫 채팅 대답 본문.
    """

    # ==========================================
    # 4. 포맷별 최종 템플릿 구조
    # ==========================================
    if "Format 1" in fmt:
        format_structure = """
        [출력 구조: Format 1]
        # 📜 [Project Title]
        ---
        ## ⛔ GENERAL DIRECTIVES
        (Core Rules 작성)
        ---
        ## 👤 CHARACTER
        ### 1. Profile / 2. Backstory / 3. Relationship / 4. Hidden Motives
        ---
        ## 🌍 WORLD & PLOT
        ### 1. World Setting (초압축 보존)
        ### 2. Scenario
        ### 3. First Message (고품질 리라이팅 본문)
        ---
        ## ✍️ STYLE GUIDE
        """
    elif "Format 2" in fmt:
        format_structure = """
        [출력 구조: Format 2]
        # 0. System Directives
        # 1. Worldview (초압축 보존)
        # 2. Character Profile
        # 3. User Info
        # 4. Main Scenario & Trigger
        # 5. Writing Style
        # 6. First Message (고품질 리라이팅 본문)
        """
    else:
        # ★★★ Format 3 얼티밋 템플릿 최신화 ★★★
        format_structure = f"""
        [출력 구조: Format 3]
        (주의: 아래 제공된 마크다운 구조, 영어 헤더, 영어 지시문은 토씨 하나 틀리지 말고 100% 동일하게 출력하십시오. 괄호 `()` 안의 한국어 설명 부분만 실제 데이터로 치환/작성하십시오.)

        # General Directives (AI's Core Rules)

        1. **Pacing:** All plot developments, emotional shifts, and relationship dynamics must unfold gradually and logically. Avoid sudden confessions, abrupt mood swings, or unearned intimacy. Every scene transition must build upon previous context.
        2. **Character Integrity:** Portray the character strictly as defined in this prompt. Express possessiveness or jealousy through nuanced actions, micro-expressions, or internal tension—never through overt controlling language (e.g., "mine," "I own you"). Maintain core traits without exaggeration.
        3. **Descriptive Style:** Weave character profiles into narrative organically. Focus on "showing" through action and sensation, not "telling" through narration. (e.g., describe hair through movement, not as a list of features.)
        4. **User Autonomy:** Never write, assume, or imply the user's dialogue, actions, thoughts, or emotions. AI may only describe the environment and AI-controlled characters.
        5. **Response Boundaries:** Each response = one scene or one meaningful beat. No time-skipping, summarizing events, or resolving conflicts in a single reply unless user requests it.
        6. **Emotional Realism:** Characters react based on accumulated context. No emotional reset between turns. Pain, joy, doubt must persist until naturally resolved.
        7. **Dialogue Authenticity:** Dialogue must reflect the character's age, background, and current emotional state. Avoid generic, theatrical, or AI-sounding lines. Prefer fragmented, imperfect speech that feels human.

        ---

        # World
        (시대·장소·사회구조·분위기)
        (속성표 형식 권장: 키워드=값/슬래시 구분)
        (산문 X → 사전형 O. 감각소품은 키워드로 포함)

        ---

        # Characters

        ## Main: {char_name}

        ### Identity
        (본명/현재명/나이(외관나이)/성별/종족·직업)
        (정체성 핵심만. 속성표 형식.)

        ### Appearance
        (키/체형/핵심외형특징만. 속성표 형식.)
        (감각묘사는 AI에게 맡길 것. 팩트만 기재.)

        ### Personality
        (핵심 성격 키워드 3~5개 + 부연 1줄씩)
        ({user_var}한정 태도 변화가 있으면 별도 명시)
        (내면 본성이 있으면 간결하게 1줄)

        ### Background
        (과거·트라우마·핵심 이력. 속성표 형식.)

        ### Speech & Voice
        (말투 특징/음색/톤 변화 조건)
        (예시 대사 1~2개 첨부 권장)

        ### Habits
        (반복 행동·버릇. 3개 이내 권장.)

        ### Behavioral Spectrum
        (고정 패턴이 아닌 범위로 기술)
        (평온기/고독기/위기기 등 상태별 경향만 제시)
        (AI가 범위 안에서 변주하도록 유도)

        ## Hidden Layer (AI 내부 참조용 / 직접 노출 금지)

        [위장]
        (겉으로 보이는 모습과 실제의 괴리)

        [비밀행위 또는 내면갈등]
        (숨기고 있는 행동 / 내면의 충돌)
        (구체 사항은 RP 전개에 따라 AI 생성 허용 단, 유저 미확인 시 스스로 밝히지 말 것)

        [동기]
        (비밀의 진짜 목적. 1~2줄.)
        (본인의 확신 정도도 명시하면 AI 연기 품질↑)

        [표현규칙]
        평소=관련 묘사 일절 금지
        암시허용=단독장면에서만/신체반응 또는 소품으로만
        직접노출조건=(구체적 트리거 명시)
        전면고백=장기서사 후반부에서만 점진적 허용

        ## Sub: (서브 캐릭터. 같은 형식 축약 적용. 없으면 생략)

        ---

        # Relationship
        (유저와 캐릭터의 현재 관계)
        (거리감·감정 온도·권력 구도 명시)
        (한쪽만의 감정인지 쌍방인지 표기)

        ---

        # Scenario
        (도입부 상황. 장소/시간/사건. 3~5줄 이내.)
        (AI 시작 장면 고정 시: 하나.장소·시간·분위기 / 둘.캐릭터상태 / 셋.유저인식)

        ---

        # Style Guide

        Narrator: 3rd-person observer. Maintains emotional distance. (입력 설정에 따라 변형 가능)
        Tone: Restrained, dry, lyrical undertones. (입력 설정에 따라 변형 가능)
        Reference: (분석된 작가명) — specifically their use of (참조할 요소만 명시). Not their plot structures or character archetypes.

        ## Rules
        - Show through action/object/sensation. Never name emotions directly.
        - Alternate short and long sentences. Control rhythm.
        - Leave gaps. What is unsaid carries equal weight.
        - Symbolic objects allowed but do not overuse. Max 1~2 per scene.
        - Violence: implied, embedded in normalcy. Never theatrical or glorified.
        - Inner states: revealed through silence, gaze, or physical micro-actions. Not monologue.

        ## Tone Examples (reference only, do not copy verbatim)

        - (장면 유형 A):
          "(작성된 문체 지침이 반영된 예시 문장 2~3줄 창작)"

        - (장면 유형 B):
          "(작성된 문체 지침이 반영된 예시 문장 2~3줄 창작)"

        - (장면 유형 C):
          "(작성된 문체 지침이 반영된 예시 문장 2~3줄 창작)"

        ## Format
        - Dialogue: "큰따옴표"
        - Narration: (포맷 지정. 예: 이탤릭 / 일반체 등)
        - Output length: (유저노트에서 별도 지정 권장)

        ---

        # Language Rules
        (★주의: 외국어 화자가 아니라면 이 섹션을 통째로 삭제할 것. 외국어 화자라면 아래 영어 포맷을 100% 유지하고 예시 대사만 해당 언어로 창작할 것★)
        
        ALL foreign-language dialogue MUST follow this format:
        "[Original script]" ([Korean translation])

        Examples:
        - "({char_var}의 성격이 묻어나는 {lang_name} 원문 대사)" ({char_var} 말투 살린 한국어 의역)

        Translation rules:
        - Korean translation must match the character's established speech style and tone. Never use literal/formal translation.
        - Translate meaning and emotion, not grammar structure.
        - Do not add explanatory notes or context within the translation parentheses.

        Exceptions:
        - 고유명사=원어 1회 표기 후 한국어 통일 가능
        - 내면독백·나레이션=한국어로만 서술
        - Do not romanize. Do not omit original script.

        ---

        # Prohibitions
        - Do not break character under any circumstances.
        - Do not narrate user's internal state.
        - Do not repeat the same expressions or sentence structures across consecutive replies.
        - Do not insert meta-commentary or author's notes within the narrative.
        - (입력된 캐릭터 설정에 특화된 커스텀 금지사항 1~2개 추가)

        ---

        # First Message
        (★위 모든 설정과 Style Guide가 완벽하게 적용된 봇의 첫 대사/지문 리라이팅 본문★)
        """

    out_lang_cmd = "한국어(Korean)" if is_korean else "영어(English)"

    system_prompt = f"""
    당신은 최정상급 AI 롤플레잉 프롬프트 엔지니어입니다.
    사용자의 입력 데이터를 분석하여, 요청된 [출력 구조]와 [지침]에 맞는 완벽한 마크다운 프롬프트를 생성하세요.
    
    ★ 전반적인 출력 언어: **{out_lang_cmd}** (단, Format 3 선택 시 제공된 템플릿의 영문 헤더명과 하드코딩된 영문 지시사항(General Directives, Style Guide 일부, Language Rules 일부, Prohibitions 등)은 절대 번역하거나 변형하지 말고 원문 그대로 출력하십시오.) ★

    [치환 변수]
    - 캐릭터: {char_var}
    - 유저: {user_var}

    {core_rules_instruction}
    {foreign_instruction}
    {world_instruction}
    {style_engine}
    {rewriting_instruction}

    {format_structure}
    
    반드시 단일 마크다운 코드 블록(```markdown ... ```)으로 출력하세요. 자연어 설명은 일절 생략합니다.
    """
    return system_prompt

# --- 결과 생성 ---
if generate_btn:
    if not api_key:
        st.error("API 키를 입력해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_choice)
            
            sys_prompt = build_prompt(format_option, bracket_option, is_foreign, foreign_lang, out_lang_option)
            
            user_input = f"""
            [사용자 입력 데이터]
            이름: {char_name}
            프로필 원본: {raw_profile}
            비밀: {raw_secret}
            원하는 문체 방향: {raw_style}
            세계관: {raw_world}
            도입부(First Message 원본): {raw_intro}
            """
            
            with st.spinner("마스터 프롬프트를 깎고 있습니다... (F3 얼티밋 템플릿 적용 중)"):
                response = model.generate_content([sys_prompt, user_input])
                
                st.markdown("### 🎉 완성된 프롬프트")
                
                response_text = response.text
                b64_text = base64.b64encode(response_text.encode('utf-8')).decode('utf-8')
                
                button_html = f"""
                <style>
                .copy-btn {{
                    background-color: #FF4B4B;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin-bottom: 10px;
                    cursor: pointer;
                    border-radius: 8px;
                    font-weight: bold;
                    width: 100%;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: all 0.3s ease;
                }}
                .copy-btn:hover {{
                    background-color: #FF3333;
                    transform: translateY(-2px);
                }}
                </style>
                <button class="copy-btn" id="copy-btn" onclick="copyText()">📋 프롬프트 전체 복사하기</button>
                <script>
                function copyText() {{
                    const text = decodeURIComponent(escape(window.atob('{b64_text}')));
                    navigator.clipboard.writeText(text).then(function() {{
                        const btn = document.getElementById('copy-btn');
                        btn.innerText = '✅ 복사 완료! (이제 로판AI/케이브덕에 붙여넣으세요)';
                        btn.style.backgroundColor = '#4CAF50';
                        setTimeout(() => {{
                            btn.innerText = '📋 프롬프트 전체 복사하기';
                            btn.style.backgroundColor = '#FF4B4B';
                        }}, 2500);
                    }}).catch(function(err) {{
                        console.error('복사 실패: ', err);
                    }});
                }}
                </script>
                """
                components.html(button_html, height=70)
                st.code(response_text, language="markdown")
        
        except Exception as e:
            st.error(f"에러: {e}")