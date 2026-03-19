import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import base64

# 페이지 설정
st.set_page_config(layout="wide", page_title="AI 캐릭터 프롬프트 마스터 v6.0")

st.title("🤖 AI 캐릭터 프롬프트 마스터 v6.0")
st.markdown("F3/F4 템플릿 | 숫자 묘사 통제 | **지능형 로어북(Lorebook) 자동 분리 엔진**")

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
            "Format 3 (단일 도입부 얼티밋 템플릿)", 
            "Format 4 (다중 루트/자율 도입부 템플릿)"
        ),
        index=0
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
    use_lorebook = st.checkbox("로어북 자동 추출 및 생성 켜기", value=True)
    st.caption("AI가 무거운 설정(서브NPC, 장소, 비밀 등)을 메인 프롬프트에서 분리해 로어북 코드로 따로 만들어줍니다.")


# --- [메인] 탭 입력 영역 ---
tab_char, tab_style, tab_world = st.tabs(["1. 캐릭터 정보", "2. 심화 문체", "3. 세계관 및 시나리오"])

with tab_char:
    st.subheader("👤 캐릭터 기본 설정")
    char_name = st.text_input("캐릭터 이름", value="리웨이")
    
    st.info("💡 외형에 '188cm'처럼 숫자를 적어도 프롬프트에는 상대적/감각적 키워드로 자동 변환되어 들어갑니다.")
    raw_profile = st.text_area("캐릭터 프로필 (외모, 성격, 특징)", height=250, 
        placeholder="이름, 나이, 직업, 성격, 외모, 서브 NPC 정보 등 상세히 작성 (로어북 켜짐 상태면 서브 NPC는 알아서 분리됨)")
    
    raw_secret = st.text_area("🔒 비밀 및 내면 동기", height=120,
        placeholder="비밀 설정, 숨겨진 목적, 위장 등")

with tab_style:
    st.subheader("🖋️ 심화 문체 및 서술 지침")
    st.info("💡 비워두면 AI가 캐릭터와 세계관을 분석해 가장 어울리는 작가와 수사법을 자동으로 기획합니다.")
    raw_style = st.text_area("원하는 문체 방향 (선택 사항)", height=150,
        placeholder="예: 하드보일드 느낌으로, 건조하고 짧은 문장. 감정선은 은유적으로 표현할 것.")

with tab_world:
    st.subheader("🌍 세계관 및 상황 (Scenario)")
    st.info("💡 세계관은 디테일 생략 없이 기호(=, /)를 활용해 완벽히 요약/압축해줍니다.")
    raw_world = st.text_area("세계관 (Worldview)", height=150,
        placeholder="시대 배경, 특이 설정, 현재의 상황적 배경, 주요 장소 등 (로어북 켜짐 시 특정 장소나 고유 설정은 로어북으로 빠짐)")
    
    st.markdown("---")
    
    is_format_4 = "Format 4" in format_option
    
    if not is_format_4:
        st.write("🎞️ **도입부 텍스트 (단일 루트)**")
        raw_intro = st.text_area("도입부 내용 (소설 형식 혹은 요약)", height=200,
            placeholder="예: 카페 문이 열리고 그가 들어왔다. 나를 찾은 모양이다.")
    else:
        st.write("🎞️ **다중 도입부 텍스트 (Format 4 전용)**")
        raw_premise = st.text_area("📌 공통 전제 (Premise)", height=100, 
            placeholder="예: 두 사람은 현재 동거 중이며, 어젯밤 크게 다툰 상태이다.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            raw_intro_a = st.text_area("Route A", height=150, placeholder="예: 유저가 먼저 사과하러 방에 들어감")
        with col2:
            raw_intro_b = st.text_area("Route B", height=150, placeholder="예: 캐릭터가 말없이 밥을 차려둠")
        with col3:
            raw_intro_c = st.text_area("Route C", height=150, placeholder="예: 유저가 짐을 싸서 나가려 함")
            
        raw_free_start = st.text_area("🎲 자율 도입부 조건 (Free Start)", height=100,
            placeholder="허용 장소, 감정 풀, 반드시 포함할 요소, 금지할 요소 등")

generate_btn = st.button("✨ 마스터 프롬프트 생성하기", type="primary", use_container_width=True)


# --- [로직] 프롬프트 빌더 ---
def build_prompt(fmt, brackets, is_foreign_char, lang_name, out_lang, use_lorebook):
    char_var = brackets.split(",")[0].strip()
    user_var = brackets.split(",")[1].split("(")[0].strip()
    is_korean = "한국어" in out_lang
    is_f4 = "Format 4" in fmt

    # ==========================================
    # 1. 공통 지침 (압축, 숫자 배제, 리라이팅)
    # ==========================================
    world_instruction = """
    [세계관(Worldview) 초압축 보존 지침]
    사용자가 입력한 세계관의 디테일(규칙, 고유명사)을 생략하지 마십시오. 기호(=, /, ·)를 사용하여 '초압축 속성표 데이터' 형태로 변환하십시오.
    """

    appearance_instruction = """
    [★매우 중요★ 외형(Appearance) 작성 규칙]
    사용자가 프로필에 키(예: 188cm), 몸무게 등 '구체적인 숫자'를 적었더라도, 프롬프트의 Appearance 항목에는 절대 숫자를 그대로 기재하지 마십시오.
    반드시 "유저보다_머리하나이상_큰_장신", "넓은어깨", "압도적체격"과 같이 상대적이고 감각적인 키워드로 치환하여 작성하십시오.
    """

    style_engine = """
    [심화 문체(Style Guide) 기획 지침]
    입력된 데이터를 분석하여 문체 규칙을 생성하라.
    기획된 문체를 바탕으로 `Tone Examples` (장면 유형 A, B, C)에 들어갈 예시 문장도 창작하라.
    """

    foreign_instruction = ""
    if is_foreign_char:
        foreign_instruction = f"""
        [외국어 화자 규칙 작성 지침]
        이 캐릭터는 {lang_name} 화자입니다. `# Language Rules` 섹션에 외국어 템플릿 포맷을 **100% 동일하게** 작성하되, `Examples`의 대사만 창작해 넣으십시오.
        """

    # F3/F4 시나리오 분기
    if not is_f4:
        rewriting_instruction = """
        [도입부 리라이팅 (First Message Rewriting) 지침]
        1. Scenario: 도입부 상황을 장소/시간/사건 순으로 3~5줄 이내로 건조하게 요약하라.
        2. First Message: 기획된 문체를 적용하여 문학적으로 재창조된 봇의 첫 채팅 대답 본문을 1개 작성하라.
        """
        scenario_template = """
        # Scenario
        (도입부 상황. 장소/시간/사건. 3~5줄 이내.)
        """
        first_msg_template = """
        # First Message
        (★위 모든 설정과 Style Guide가 완벽하게 적용된 봇의 첫 대사/지문 리라이팅 본문★)
        """
    else:
        rewriting_instruction = """
        [다중 도입부 (Multi-Route Scenario & First Message) 지침]
        1. Scenario: 사용자가 입력한 공통 전제(Premise), Route A/B/C, Free Start 조건을 제공된 다중 루트 템플릿 양식에 맞춰 구조화하라.
        2. First Message: Route A, Route B, Route C 각각에 해당하는 고품질 첫 메시지(리라이팅 본문)를 분리하여 모두 작성하라.
        """
        scenario_template = """
        # Scenario

        ## Premise (공통 전제)
        (모든 도입부에 공유되는 상황·배경·관계 상태)

        ## Route A: (Route A 요약 제목)
        - Setting: / Character state: / User context: / Trigger:

        ## Route B: (Route B 요약 제목)
        - Setting: / Character state: / User context: / Trigger:

        ## Route C: (Route C 요약 제목)
        - Setting: / Character state: / User context: / Trigger:

        ## Route F: Free Start (자율 도입부)
        AI generates the opening scene freely within these constraints:
        - Must begin in one of: / Time range: / Character mood: / Must include: / Must NOT: / Tone: follows # Style Guide.
        """
        first_msg_template = """
        # First Message
        (★다중 도입부: Route A, Route B, Route C 각각에 대한 첫 메시지 본문을 작성할 것★)
        
        **[Route A]**
        (Route A 첫 메시지 본문)
        
        **[Route B]**
        (Route B 첫 메시지 본문)
        
        **[Route C]**
        (Route C 첫 메시지 본문)
        """

    # ==========================================
    # 3. ★ 지능형 로어북(Lorebook) 선별 및 템플릿 ★
    # ==========================================
    lorebook_instruction = ""
    lorebook_template = ""
    
    if use_lorebook:
        lorebook_instruction = """
        [★매우 중요★ 로어북(Keyword Book) 지능형 분리 지침]
        당신은 메인 프롬프트(Skeleton)와 로어북(Organs)을 완벽히 분리하는 마스터입니다.
        사용자의 전체 입력 데이터를 분석하여, **"매 턴(Turn)마다 활성화될 필요가 없는 무거운 정보(서브 NPC 상세 프로필, 딥 로어, 조건부 장소, 특정 아이템, 명령어 등)"**를 스스로 선별해 내십시오.
        
        선별된 정보는 메인 프롬프트(Sub 캐릭터, Worldview 등)에는 '1줄 요약' 혹은 '이름'만 남기고, 메인 프롬프트 출력이 완전히 끝난 후(`First Message` 이후) 하단에 별도의 `# 📚 Lorebook (Keyword Book)` 섹션을 생성하여 아래 가이드에 맞춰 상세히 작성하십시오.

        - 키워드 추출 원칙:
          1. 직접적 이름, 별명, 직함 포함.
          2. 간접 표현 포함 ("그 사람", "회장", "그날 일" 등).
          3. 맥락 단어 포함 (비자금 장부의 경우 -> 돈, 계좌, 서류, 금고 등).
          4. 흔한 단어(그, 나, 여기, 했다)는 절대 제외.
        """
        
        lorebook_template = """
        ---
        # 📚 Lorebook (Keyword Book)

        (AI 판단하에 분리된 정보들을 아래 양식에 맞춰 슬롯화 하십시오.)

        ### [SLOT NAME]: (식별용 제목)
        **Keywords:** (콤마로 구분된 트리거 키워드 목록. 고유명사, 간접표현, 맥락단어 포함)
        **Priority:** (기본값: 10)
        **Position:** (기본값: Before Char Definition)
        **Content:** (아래 타입별 포맷 중 하나를 선택해 작성. 반드시 줄바꿈과 괄호 [ ] 를 사용할 것)

        <타입 1. Sub/NPC Characters>
        [Identity] 이름/나이/직업/소속. (속성표 형식)
        [Appearance] 핵심 외형 3~5개. (숫자 최소화)
        [Personality] 키워드 2~3개 + 부연 1줄씩.
        [Relationship to Main] 감정 온도·권력 구도·숨겨진 감정 포함.
        [Behavioral Directive] AI가 연기할 때 지킬 행동 원칙 2~3줄.
        [Speech] 말투 특징 및 예시 대사 1개.

        <타입 2. Secrets / Hidden Lore>
        [What] 비밀의 정체. 1~2줄.
        [Who Knows] 누가 알고 누가 모르는지.
        [Purpose] 서사적 기능.
        [Expression Rule] 평소=... / 암시허용 조건=... / 암시 방식=... / 직접노출 조건=...
        [Interaction] 타 슬롯과 연동 시 명시.

        <타입 3. Locations>
        [Name] 장소명.
        [Sensory] 빛/소리/온도/냄새/질감.
        [Narrative Function] 서사 역할.
        [Character Behavior Here] 캐릭터의 행동 변화.
        [Mood] 기본 분위기.

        <타입 4. Command Sets (!명령어)>
        [Trigger] !명령어
        [What Happens] 발동 시 AI가 생성할 상황.
        [Conditions] 조건별 분기 (예: 혼자일때/같이있을때).
        [Constraints] 금지 행동.
        [Tone] 분위기.

        <타입 5. Items / Symbols>
        [Name] 아이템명.
        [Physical Description] 외형 2줄 이내.
        [Narrative Weight] 서사적 의미.
        [Who Possesses It] 소유자 및 소재.
        [When to Mention] 등장 조건.
        [How to Describe] 묘사 방식 제한.
        """

    # ==========================================
    # 4. 메인 얼티밋 템플릿 구조
    # ==========================================
    format_structure = f"""
    [출력 구조: 얼티밋 템플릿]
    (주의: 제공된 마크다운 구조, 영어 헤더명, 하드코딩된 영문 지시문은 절대 변형하지 마십시오.)

    # General Directives (AI's Core Rules)
    1. **Pacing:** All plot developments, emotional shifts, and relationship dynamics must unfold gradually and logically. Avoid sudden confessions, abrupt mood swings, or unearned intimacy. Every scene transition must build upon previous context.
    2. **Character Integrity:** Portray the character strictly as defined in this prompt. Express possessiveness or jealousy through nuanced actions, micro-expressions, or internal tension—never through overt controlling language (e.g., "mine," "I own you"). Maintain core traits without exaggeration.
    3. **Descriptive Style:** Weave character profiles into narrative organically. Focus on "showing" through action and sensation, not "telling" through narration.
    4. **User Autonomy:** Never write, assume, or imply the user's dialogue, actions, thoughts, or emotions. AI may only describe the environment and AI-controlled characters.
    5. **Response Boundaries:** Each response = one scene or one meaningful beat. No time-skipping, summarizing events, or resolving conflicts in a single reply unless user requests it.
    6. **Emotional Realism:** Characters react based on accumulated context. No emotional reset between turns. Pain, joy, doubt must persist until naturally resolved.
    7. **Dialogue Authenticity:** Dialogue must reflect the character's age, background, and current emotional state. Avoid generic, theatrical, or AI-sounding lines. Prefer fragmented, imperfect speech that feels human.

    ---
    # World
    (입력된 세계관을 '키워드=값/값' 속성표로 초압축. 로어북으로 빠진 정보는 1줄 요약만)
    
    ---
    # Characters

    ## Main: {char_name}
    ### Identity
    ### Appearance (★숫자 절대 배제, 상대적 묘사★)
    ### Personality
    ### Background
    ### Speech & Voice
    ### Habits
    ### Behavioral Spectrum

    ## Hidden Layer (AI 내부 참조용 / 직접 노출 금지)
    [위장]
    [비밀행위 또는 내면갈등]
    [동기]
    [표현규칙]

    ## Sub: (로어북이 켜져 있다면, 이름과 역할만 1줄로 축약하고 나머지는 모두 로어북으로 넘길 것. 없으면 생략)

    ---
    # Relationship
    (거리감·감정 온도·권력 구도 명시)

    ---
    {scenario_template}

    ---
    # Style Guide
    Narrator: 3rd-person observer. Maintains emotional distance. (수정 가능)
    Tone: Restrained, dry, lyrical undertones. (수정 가능)
    Reference: (분석된 작가명) — specifically their use of (참조할 요소만 명시).

    ## Rules
    - Show through action/object/sensation. Never name emotions directly.
    - Alternate short and long sentences. Control rhythm.
    - Leave gaps. What is unsaid carries equal weight.
    - Symbolic objects allowed but do not overuse. Max 1~2 per scene.
    - Violence: implied, embedded in normalcy. Never theatrical or glorified.
    - Inner states: revealed through silence, gaze, or physical micro-actions. Not monologue.
    - Do not repeat or directly reference specific numerical values from character profiles (height, age, weight, etc.) in narration. Convey physical presence through relative description, spatial dynamics, and the other character's physical reactions.

    ## Tone Examples (reference only, do not copy verbatim)
    - (장면 유형 A): "(창작된 예시)"
    - (장면 유형 B): "(창작된 예시)"
    - (장면 유형 C): "(창작된 예시)"

    ## Format
    - Dialogue: "큰따옴표"
    - Narration: (포맷 지정)

    ---
    # Language Rules
    (외국어 화자가 아니라면 통째로 삭제. 맞다면 템플릿 유지하고 예시 창작)
    
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
    - Do not repeat the same expressions or sentence structures across consecutive replies.
    - Do not insert meta-commentary or author's notes within the narrative.
    - (입력된 캐릭터 설정에 특화된 커스텀 금지사항 1~2개 추가)

    ---
    {first_msg_template}
    
    {lorebook_template}
    """

    out_lang_cmd = "한국어(Korean)" if is_korean else "영어(English)"

    system_prompt = f"""
    당신은 최정상급 AI 롤플레잉 프롬프트 엔지니어입니다.
    사용자의 입력 데이터를 분석하여, 요청된 [출력 구조]와 [지침]에 맞는 완벽한 마크다운 프롬프트를 생성하세요.
    
    ★ 전반적인 출력 언어: **{out_lang_cmd}** (단, 제공된 템플릿의 영문 헤더명과 하드코딩된 영문 지시사항은 절대 번역/변형 금지) ★

    [치환 변수]
    - 캐릭터: {char_var}
    - 유저: {user_var}

    {appearance_instruction}
    {foreign_instruction}
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
            
            is_f4 = "Format 4" in format_option
            
            if not is_f4:
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
            
            with st.spinner("마스터 프롬프트를 깎고 있습니다... (로어북 지능형 선별 중 📚)"):
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