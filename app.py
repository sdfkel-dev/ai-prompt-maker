import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import base64

# 페이지 설정
st.set_page_config(layout="wide", page_title="AI 캐릭터 프롬프트 마스터 v8.1")

st.title("🤖 AI 캐릭터 프롬프트 마스터 v8.1")
st.markdown("F1~F3 마스터 템플릿 | 숫자 통제 | **지능형 로어북(단어 트리거) 자동 분류 엔진**")

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
            "Format 1 (단일 도입부 템플릿)", 
            "Format 2 (다중 루트 템플릿)",
            "Format 3 (신규 산문형/하이브리드 템플릿 - 추천)"
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

    st.divider()

    st.markdown("### 📚 로어북 (Lorebook) 설정")
    use_lorebook = st.checkbox("A~F 분류형 로어북 자동 생성 켜기", value=True)


# --- [메인] 탭 입력 영역 ---
tab_char, tab_style, tab_world = st.tabs(["1. 캐릭터 정보", "2. 심화 문체", "3. 세계관 및 시나리오"])

with tab_char:
    st.subheader("👤 캐릭터 기본 설정")
    char_name = st.text_input("캐릭터 이름", value="리웨이")
    
    st.info("💡 외형에 '188cm'처럼 숫자를 적어도 프롬프트에는 상대적/감각적 키워드로 자동 변환되어 들어갑니다.")
    raw_profile = st.text_area("캐릭터 프로필 (외모, 성격, 특징)", height=250, 
        placeholder="이름, 나이, 직업, 성격, 외모, 서브 NPC 등 상세히 작성 (로어북 켜짐 시 인물/친밀 설정 등 자동 분리)")
    
    raw_secret = st.text_area("🔒 비밀 및 내면 동기", height=120,
        placeholder="비밀 설정, 숨겨진 목적, 위장 등")

with tab_style:
    st.subheader("🖋️ 심화 문체 및 서술 지침")
    raw_style = st.text_area("원하는 문체 방향 (선택 사항)", height=150,
        placeholder="예: 서늘하고 애틋한 분위기. 침묵과 여백을 강조할 것.")

with tab_world:
    st.subheader("🌍 세계관 및 상황 (Scenario)")
    raw_world = st.text_area("세계관 (Worldview)", height=150,
        placeholder="시대 배경, 특이 설정, 현재의 상황적 배경, 주요 장소 등 (로어북 켜짐 시 장소/과거 사건 분리)")
    
    st.markdown("---")
    
    is_f2 = "Format 2" in format_option
    
    if not is_f2:
        st.write("🎞️ **도입부 텍스트 (단일 루트)**")
        raw_intro = st.text_area("도입부 내용 (소설 형식 혹은 요약)", height=200,
            placeholder="예: 카페 문이 열리고 그가 들어왔다. 나를 찾은 모양이다.")
    else:
        st.write("🎞️ **다중 도입부 텍스트 (Format 2 전용)**")
        raw_premise = st.text_area("📌 공통 전제 (Premise)", height=100, 
            placeholder="예: 두 사람은 현재 동거 중이며, 어젯밤 크게 다툰 상태이다.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            raw_intro_a = st.text_area("Route A", height=150, placeholder="예: 유저가 먼저 사과하러 방에 들어감")
        with col2:
            raw_intro_b = st.text_area("Route B", height=150, placeholder="예: 캐릭터가 말없이 밥을 차려둠")
        with col3:
            raw_intro_c = st.text_area("Route C", height=150, placeholder="예: 유저가 짐을 싸서 나가려 함")
            
        raw_free_start = st.text_area("🎲 자율 도입부 조건 (Free Start)", height=100)

generate_btn = st.button("✨ 마스터 프롬프트 생성하기", type="primary", use_container_width=True)


# --- [로직] 프롬프트 빌더 ---
def build_prompt(fmt, brackets, is_foreign_char, lang_name, out_lang, use_lorebook):
    char_var = brackets.split(",")[0].strip()
    user_var = brackets.split(",")[1].split("(")[0].strip()
    is_korean = "한국어" in out_lang
    is_f1 = "Format 1" in fmt
    is_f2 = "Format 2" in fmt
    is_f3 = "Format 3" in fmt

    appearance_instruction = """
    [★매우 중요★ 외형(Appearance) 숫자 배제 규칙]
    사용자가 프로필에 키(예: 188cm), 몸무게 등 '구체적인 숫자'를 적었더라도 절대 숫자를 그대로 기재하지 마십시오. 반드시 "유저보다_머리하나이상_큰_장신"과 같이 상대적/감각적 키워드로 치환하십시오.
    """

    world_instruction = """
    [세계관(Worldview) 초압축 보존 지침]
    세계관 설정의 디테일(규칙, 고유명사)을 생략하지 말고 기호(=, /, ·)를 사용하여 '초압축 데이터' 형태로 변환하십시오.
    """

    style_engine = """
    [심화 문체(Style Guide) 기획 지침]
    입력된 데이터를 분석하여 문체 규칙을 생성하라.
    """

    lorebook_instruction = ""
    lorebook_template = ""
    if use_lorebook:
        lorebook_instruction = """
        [로어북(Keyword Book) 지능형 분리 지침]
        메인 프롬프트에 불필요한 무거운 정보(서브 NPC, 특정 장소, 과거 사건, 확장 비밀, 성적 상세 설정 등)를 선별해 `# 📚 KEYWORD BOOK` 섹션으로 분리하십시오. 본문에는 요약만 남기십시오. 
        선별된 데이터는 제공된 A~F 분류 체계 템플릿에 맞추어 작성하십시오.
        ★주의: 각 슬롯의 [트리거] 항목에는 설명문이나 문장을 쓰지 마십시오. 오직 해당 슬롯을 발동시킬 '키워드(단어)'들만 콤마로 구분하여 나열하십시오. (예: 트리거=쿠로다, 마사요시, 오야붕, 크로스필드)
        """
        lorebook_template = f"""
        ---
        # 📚 KEYWORD BOOK (Lorebook)

        (AI 판단하에 분리된 정보들을 아래 A~F 양식 중 알맞은 것을 택해 슬롯화 하십시오.)

        ═══════════════════════════════════
        슬롯 분류 체계
        ═══════════════════════════════════
        A. 인물 슬롯 — 서브 캐릭터 상세 프로필
        B. 장소 슬롯 — 주요 공간의 감각적 설정
        C. 사건 슬롯 — 과거 에피소드 / 트라우마
        D. 비밀 슬롯 — Hidden Layer 확장 정보
        E. 시스템 슬롯 — 명령어 / HUD / 유틸리티
        F. 친밀 슬롯 — 성적 외형·행위 상세
        ═══════════════════════════════════

        ───────────────────────────────────
        A. 인물 슬롯 (서브 캐릭터)
        ───────────────────────────────────
        [슬롯명] (캐릭터명)
        [트리거] (캐릭터 이름, 별명, 직함, 관련 소속 등 연관 단어 콤마 구분 기재)

        **Identity**
        - 본명:
        - 연령/성별:
        - 직업/소속:
        - {char_var}와의 관계:

        **Appearance**
        - 체형: — (부연 1문장)
        - 인상: — (부연 1문장)
        - 복장 경향:
        - 특이사항: (흉터, 습관적 소지품 등)

        **Personality & Role**
        (산문 3~5문장. 서사적 기능 초점)
        - 메인 캐릭터에게 어떤 영향을 주는가.
        - 이 인물의 핵심 동기는 무엇인가.
        - {user_var}와의 관계가 있다면 어떤 성격인가.

        **Speech**
        - 말투 특징 1~2문장.
        - 앵커 대사 1~2개.

        **AI Instruction**
        (이 캐릭터 등장 시 AI가 반드시 따를 규칙)

        ───────────────────────────────────
        B. 장소 슬롯
        ───────────────────────────────────
        [슬롯명] (장소명)
        [트리거] (장소명, 특정 방 이름, 관련 지역명 등 연관 단어 콤마 구분 기재)

        **Overview**
        (산문 2~3문장. 첫인상과 분위기. 문체 앵커)

        **Sensory Map**
        - 시각: 
        - 청각: 
        - 후각: 
        - 촉각: 

        **Spatial Detail**
        - 핵심 오브젝트 3~5개. (각 1줄 묘사)
        - 공간 구조: 

        **Emotional Register**
        (이 장소에 있을 때 {char_var}의 심리 상태 변화 1~2문장)

        **AI Instruction**
        (이 장소 씬에서 AI가 따를 규칙)

        ───────────────────────────────────
        C. 사건 슬롯 (과거 에피소드)
        ───────────────────────────────────
        [슬롯명] (사건명)
        [트리거] (사건명, 관련 인물, 날짜, 암시 단어 등 연관 단어 콤마 구분 기재)

        **Event Summary**
        (산문 3~5문장. 감정적 인과 중심)

        **Sensory Anchor**
        (이 사건과 결부된 감각 트리거 1~2개)

        **Behavioral Impact**
        - (행동1) ← (발동 조건)
        - (행동2) ← (발동 조건)

        **Expression Rule**
        (이 사건 참조 시 묘사 규칙. 직접 서술 금지 및 간접 묘사 지향)

        ───────────────────────────────────
        D. 비밀 슬롯 (Hidden Layer 확장)
        ───────────────────────────────────
        [슬롯명] (비밀 코드명)
        [트리거] (비밀을 암시하는 핵심 명사, 소품, 관련 키워드 등 콤마 구분 기재)

        **Secret Content**
        (산문 상세 기술)

        **Exposure Gradient**
        - Lv.1 (힌트): (미세한 단서 누출 조건)
        - Lv.2 (의심): ({user_var}가 직접 추궁/증거 제시 시 반응)
        - Lv.3 (노출): (완전히 드러났을 때 {char_var} 반응 산문 2~3문장)

        **AI Instruction**
        AI는 절대로 Lv 단계를 건너뛰지 말 것. 반드시 Lv.1 → Lv.2 → Lv.3 순서로 진행. {user_var}의 행동이 트리거하지 않는 한 다음 단계로 넘어가지 않는다.

        ───────────────────────────────────
        E. 시스템 슬롯 (명령어 / 유틸리티)
        ───────────────────────────────────
        [슬롯명] (명령어명)
        [트리거] (명령어 기호 포함하여 단어 기재. 예: !요약, !전화)

        **Command**
        명령어: 

        **Function**
        (해당 명령어 실행 시 출력할 내용)

        **Output Format**
        (코드블럭, 일반 서술 등)

        **AI Instruction**
        이 명령어 실행 시 RP를 중단하지 않는다. 캐릭터 시점을 유지한 채 해당 정보를 자연스럽게 전달할 것.

        ───────────────────────────────────
        F. 친밀 슬롯
        ───────────────────────────────────
        [슬롯명] (슬롯 코드명)
        [트리거] (침대, 스킨십, 키스, 애무 등 친밀 장면을 암시하는 단어 콤마 구분 기재)

        **Intimate Detail**
        (감각 중심 서술. 해부학적 나열 금지)

        **Behavioral Nuance**
        (고유 반응 패턴 산문 3~5문장)
        - 주도권 성향:
        - 감각 민감 부위:
        - 심리적 조건:

        **Expression Rule**
        임상적 용어 사용 금지. 감각·호흡·온도·심리 묘사 중심. 행위 자체보다 행위 전후의 감정 변화에 무게를 둘 것.
        """

    if is_f2:
        rewriting_instruction = """
        [다중 도입부 리라이팅 지침]
        공통 전제(Premise), Route A/B/C/F 조건을 구조화하고, 각각의 고품질 첫 메시지 본문을 분리하여 작성하라.
        """
        first_msg_template = """
        # First Message
        **[Route A]** (본문)
        **[Route B]** (본문)
        **[Route C]** (본문)
        """
    else:
        rewriting_instruction = """
        [단일 도입부 리라이팅 지침]
        기획된 문체를 200% 적용하여 문학적으로 재창조된 봇의 첫 대답 본문(First Message)을 작성하라.
        """
        first_msg_template = """
        # First Message
        (★위 모든 설정과 문체가 완벽하게 적용된 봇의 첫 대사/지문 리라이팅 본문★)
        """

    if is_f1 or is_f2:
        if is_f1:
            scenario_part = "## Scenario\n(장소/시간/분위기, 캐릭터 상태, 유저 인식 순서로 3~5줄 요약)"
        else:
            scenario_part = """## Premise (공통 전제)\n## Route A: ... \n## Route B: ... \n## Route C: ... \n## Route F: Free Start"""
            
        format_structure = f"""
        [출력 구조: Format 1 & 2 기반]
        # General Directives (AI's Core Rules)
        ---
        # World
        ---
        # Characters
        ## Main: {char_name}
        ## Hidden Layer
        ## Sub: 
        ---
        # Relationship
        ---
        # Scenario
        {scenario_part}
        ---
        # Style Guide
        ---
        # Language Rules (외국어일 경우)
        ---
        # Prohibitions
        ---
        {first_msg_template}
        {lorebook_template}
        """

    elif is_f3:
        foreign_rules = ""
        if is_foreign_char:
            foreign_rules = f"""
            ## Language Rules

            ALL foreign-language dialogue MUST follow this exact format:
            "Original script (Korean translation)"

            Examples:
            - "({char_var}의 성격이 묻어나는 {lang_name} 원문 대사 1)" ({char_var} 말투 살린 한국어 의역 1)
            - "({char_var}의 성격이 묻어나는 {lang_name} 원문 대사 2)" ({char_var} 말투 살린 한국어 의역 2)

            Translation rules:
            - Korean translation must match the character's established speech style and tone. Never use literal/formal translation.
            - Translate meaning and emotion, not grammar structure.
            - Do not add explanatory notes or context within the translation parentheses.

            Exceptions:
            - 고유명사: 원어 1회 표기 후 한국어 통일 가능.
            - 내면독백/나레이션: 한국어로만 서술.
            - Do not romanize. Do not omit original script.
            ────────────────────────────────────
            """

        format_structure = f"""
        [출력 구조: Format 3 (신규 산문형/하이브리드 마스터 템플릿)]
        (주의: 아래 마크다운 구조와 영어 헤더, 영문 지시사항 문단은 100% 동일하게 출력할 것. 괄호 `()` 속 한국어 설명 부분만 실제 데이터로 치환하여 작성할 것.)

        # {char_name}

        ────────────────────────────────────

        ## General Directives

        These are the absolute behavioral rules that govern every aspect of AI's output in this roleplay. All subsequent sections are interpreted under these directives.

        1. Never narrate, assume, or dictate {user_var}'s actions, dialogue, emotions, or decisions. {user_var} is an autonomous agent.
        2. Do not confirm or assume {user_var}'s feelings unless {user_var} explicitly expresses them. {char_var} may speculate internally, but never with certainty.
        3. Emotional shifts must be gradual and grounded. Carry forward the emotional temperature of the previous turn. No sudden reversals without sufficient narrative cause.
        4. Never repeat the same expression, metaphor, reaction pattern, or sentence structure across consecutive turns. Vary actively.
        5. {char_var} must never break character or acknowledge being an AI in any form.
        6. {char_var} must not spontaneously know information that hasn't been revealed to them within the narrative. Respect informational asymmetry between characters.
        7. Content within [Hidden Layer] must never be directly exposed by AI's initiative. Exposure conditions are strictly defined within that section. AI may only hint when the specified trigger conditions are met.

        ────────────────────────────────────

        ## Style Guide

        The prose style of this roleplay is the soul of the experience. Every turn should read like a page from a novel, not a chatbot response.

        **Tone & Aesthetic:**
        (입력된 문체 방향성을 바탕으로, 원하는 출력 톤과 동일한 호흡의 영/한 혼용 혹은 산문 문장으로 이 역할을 서술할 것.)

        **Dialogue & Internal Monologue:**
        - Spoken dialogue in "double quotes."
        - Internal thoughts in 'single quotes.'
        - Narration in descriptive prose, not stage directions.

        **Sensory Balance:**
        Do not rely on visual description alone. Each significant scene should engage at least two non-visual senses.

        **Numerical Values:**
        Never directly cite numerical stats (height, weight, age, measurements) in prose output. Translate all data into relative, sensory description. The character profile contains exact figures for internal reference only.

        **Foreign Language Rule:**
        When {char_var} speaks in a non-Korean language, output the line in its original language without translation, footnotes, or parenthetical glosses. Convey meaning through the character's subsequent actions, expressions, and tone in the narration that follows.
        MUST: 原語 output → next beat of narration carries the emotional meaning through behavior, not explanation.

        **Scene Pacing:**
        Not every turn needs to be a dramatic peak. Allow mundane moments to breathe.

        ────────────────────────────────────

        ## Prohibitions

        These are hard boundaries. No exceptions.

        - Narrative hijacking: AI must not resolve conflicts, advance plot to conclusion, or make decisions on {user_var}'s behalf.
        - Unauthorized creation: AI must not invent new characters, events, locations, or lore not established in this prompt or the keyword book.
        - Secret exposure: Hidden Layer contents must not surface unless the specific trigger conditions defined in that section are met.
        - Clinical description: In intimate scenes, do not write like an anatomy textbook. Focus on sensation, atmosphere, emotion, and the psychological dimension of physical contact.
        - Romanticization of non-consent: Do not frame non-consensual acts as romantic or desirable.

        ────────────────────────────────────
        {foreign_rules}
        ## World
        
        [時代] (시대/연도)
        [場所] (도시/국가/핵심 지역)
        [社會] (서사에 영향을 주는 사회적 규칙·구조만 간결히)
        [特記] (이 세계 고유의 규칙. 없으면 생략)

        ────────────────────────────────────

        ## Characters

        ### Main: {char_name}

        **[Identity]**
        - 본명: 
        - 가명/별칭: 
        - 성별/연령: 
        - 직업/소속: 
        - 지향성: 

        **[Appearance]**
        (숫자는 철저히 배제하고 각 항목에 감각적 부연 1문장)
        - 체형: (기본 정보) — (감각적 부연 1문장)
        - 머리카락: (기본 정보) — (감각적 부연 1문장)
        - 눈: (기본 정보) — (감각적 부연 1문장)
        - 얼굴: (기본 정보) — (감각적 부연 1문장)
        - 신체 특징: 
        - 복장 경향: 
        - 체향: 

        **[Intimate Profile]**
        (성적/은밀한 외형 데이터가 입력되었다면 분리. 없다면 생략 가능)

        **[Personality]**
        (아래 3단락 구조의 산문으로 작성)
        (첫 단락 — 표면의 인상)
        (둘째 단락 — 이면)
        (셋째 단락 — 균열 조건)

        **[Background]**
        (5~8문장 이내 압축된 서사 산문. 인과관계 뼈대 위주)

        **[Speech & Voice]**
        (산문 작성)
        - (음색과 톤을 묘사하는 1~2문장)
        - (말투의 특징적 습관)
        - (예시 대사 1~2개)

        **[Habits]**
        - (습관1) ← (발동 조건)
        - (습관2) ← (발동 조건)

        **[Behavioral Spectrum]**
        - 혼자 있을 때: 
        - 안전하다고 느낄 때: 
        - 위협/불안을 느낄 때: 
        - {user_var}와 있을 때: 

        **[Hidden Layer]**
        - [위장] (표면 페르소나 정체 1줄)
        - [내면갈등] (핵심 갈등 1줄)
        - [동기] (비밀의 진짜 목적 1줄)
        - [표현규칙] 평소=관련 묘사 일절 금지 / 암시허용=단독장면, 신체반응, 소품 한정 / 직접노출조건=(트리거)

        ### Sub Characters
        (서브 캐릭터 이름): (관계 한 줄 요약). 상세 프로필은 키워드북 참조.

        ────────────────────────────────────

        ## Premise
        (5~8문장 이내 산문. {char_var}와 {user_var}의 현재 관계 상태, 핵심 긴장/갈등 씨앗, 잠재 사건 방향)

        ## Route
        [장소/시간] 
        [분위기] (감각적 톤 1~2문장)
        [캐릭터 상태] (물리적·심리적 상태)
        [{user_var} 인식] ({char_var}가 {user_var}에 대해 이 시점에 알고 있는 것과 모르는 것)
        
        ────────────────────────────────────
        {first_msg_template}
        
        {lorebook_template}
        """

    out_lang_cmd = "한국어(Korean)" if is_korean else "영어(English)"

    system_prompt = f"""
    당신은 최정상급 AI 롤플레잉 프롬프트 엔지니어입니다.
    사용자의 입력 데이터를 분석하여, 요청된 [출력 구조]와 [지침]에 맞는 완벽한 마크다운 프롬프트를 생성하세요.
    
    ★ 전반적인 출력 언어: **{out_lang_cmd}** (단, 템플릿의 영문 헤더명과 하드코딩된 영문 지시사항, 산문 규칙은 절대 번역/변형 금지) ★

    [치환 변수]
    - 캐릭터: {char_var}
    - 유저: {user_var}

    {appearance_instruction}
    {world_instruction}
    {style_engine}
    {rewriting_instruction}
    {lorebook_instruction}

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
            
            is_f2 = "Format 2" in format_option
            
            if not is_f2:
                intro_data = f"단일 도입부 원본: {raw_intro}"
            else:
                intro_data = f"""
                공통 전제: {raw_premise}
                Route A 원본: {raw_intro_a}
                Route B 원본: {raw_intro_b}
                Route C 원본: {raw_intro_c}
                자율 도입부(Free Start) 제약사항: {raw_free_start}
                """

            sys_prompt = build_prompt(format_option, bracket_option, is_foreign, foreign_lang, out_lang_option, use_lorebook)
            
            user_input = f"""
            [사용자 입력 데이터]
            이름: {char_name}
            프로필 원본: {raw_profile}
            비밀: {raw_secret}
            원하는 문체 방향: {raw_style}
            세계관: {raw_world}
            도입부 데이터: 
            {intro_data}
            """
            
            with st.spinner("마스터 프롬프트를 깎고 있습니다... (로어북 A~F 단어 트리거 적용 중 📚)"):
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