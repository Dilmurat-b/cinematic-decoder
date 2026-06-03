"""
Cinematic Decoder — AI Movie Companion
A Streamlit app that surfaces vocabulary, idioms, and cultural context
from classic movie scenes — with zero spoilers.
"""

import streamlit as st
import json
import google.generativeai as genai

# ── Page configuration (must be first Streamlit call) ──────────────────────────
st.set_page_config(
    page_title="Cinematic Decoder · AI Movie Companion",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inline CSS — dark-mode polish & card styles ────────────────────────────────
st.markdown(
    """
    <style>
    /* ---------- Global ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,700;1,600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d0d0f;
        color: #e8e8f0;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12121a 0%, #0d0d0f 100%);
        border-right: 1px solid #1e1e2e;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: #a0a0c0 !important;
        font-size: 0.8rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    /* ---------- Main area ---------- */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 960px;
    }

    /* ---------- Hero header ---------- */
    .cd-hero {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.25rem;
    }
    .cd-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #e8c97e 0%, #f5a623 50%, #e05c5c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
        margin: 0;
    }
    .cd-subtitle {
        color: #6b6b8a;
        font-size: 0.95rem;
        font-weight: 400;
        letter-spacing: 0.04em;
        margin-bottom: 2rem;
    }

    /* ---------- Scene badge ---------- */
    .scene-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(240, 166, 35, 0.12);
        border: 1px solid rgba(240, 166, 35, 0.3);
        color: #f0a623;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
    }

    /* ---------- Section heading ---------- */
    .vocab-section-heading {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #55556a;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .vocab-section-heading::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #1e1e2e, transparent);
    }

    /* ---------- Idiom card ---------- */
    .idiom-card {
        background: linear-gradient(135deg, #14141e 0%, #1a1a28 100%);
        border: 1px solid #22223a;
        border-radius: 16px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.1rem;
        position: relative;
        overflow: hidden;
        transition: border-color 0.25s ease, transform 0.2s ease;
    }
    .idiom-card:hover {
        border-color: rgba(240, 166, 35, 0.35);
        transform: translateY(-2px);
    }
    .idiom-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px; height: 100%;
        background: linear-gradient(180deg, #f0a623, #e05c5c);
        border-radius: 4px 0 0 4px;
    }
    .card-index {
        position: absolute;
        top: 1.2rem; right: 1.5rem;
        font-size: 2.2rem;
        font-weight: 700;
        color: rgba(255,255,255,0.04);
        font-family: 'Playfair Display', serif;
        line-height: 1;
        user-select: none;
    }
    .phrase {
        font-size: 1.2rem;
        font-weight: 600;
        color: #f0e6c8;
        margin-bottom: 0.5rem;
        letter-spacing: 0.01em;
    }
    .translation {
        font-size: 0.9rem;
        font-weight: 500;
        color: #f0a623;
        margin-bottom: 0.75rem;
        font-style: italic;
    }
    .context-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #44445a;
        margin-bottom: 0.3rem;
    }
    .context {
        font-size: 0.88rem;
        color: #8888aa;
        line-height: 1.6;
    }
    .no-spoiler-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(46, 213, 115, 0.1);
        border: 1px solid rgba(46, 213, 115, 0.2);
        color: #2ed573;
        border-radius: 999px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 0.15rem 0.6rem;
        margin-top: 0.8rem;
    }

    /* ---------- Footer ---------- */
    .cd-footer {
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #1e1e2e;
        color: #33334a;
        font-size: 0.78rem;
        text-align: center;
        letter-spacing: 0.05em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Data Loading & Helpers ─────────────────────────────────────────────────────
@st.cache_data
def load_data() -> dict[str, list[dict]]:
    with open("movies_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def parse_srt(srt_content: str) -> list[dict]:
    import re
    blocks = re.split(r'\n\s*\n', srt_content.strip())
    parsed = []
    for block in blocks:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) >= 3:
            # First line is index, second is timestamp, rest is text
            timestamp = lines[1]
            text = " ".join(lines[2:])
            parsed.append({"timestamp": timestamp, "text": text})
    return parsed

# Configure Gemini API
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, FileNotFoundError):
    pass  # Allow app to load, error will happen when button is clicked

def extract_vocabulary_with_ai(subtitle_text: str) -> list[dict]:
    prompt = f"""You are an English language tutor.
Task: Identify top 5-7 idioms, phrases, or slang terms from the provided subtitle text.
CRITICAL: 
    1. 'phrase' must be the original English text.
    2. 'translation' MUST be a natural translation into RUSSIAN.
    3. 'context' must be the original English context provided below.
Return the result strictly in valid JSON format: [{{"phrase": "...", "translation": "...", "context": "..."}}].
Do not include any markdown formatting like ```json or ```, just return the raw JSON array.

Subtitle text:
{subtitle_text}
"""
    model = genai.GenerativeModel("gemini-3.1-flash-lite")
    response = model.generate_content(prompt)
    
    try:
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"Failed to parse AI response. Error: {str(e)}")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='margin-bottom:1.5rem;'>"
        "<span style='font-size:1.8rem;'>🎬</span>"
        "<span style='font-family:Playfair Display,serif; font-size:1.15rem; "
        "font-weight:700; color:#e8c97e; margin-left:0.5rem;'>Cinematic<br>"
        "<span style='color:#f5a623;'>Decoder</span></span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='color:#55556a; font-size:0.8rem; line-height:1.6; "
        "margin-bottom:1.5rem;'>"
        "Explore classic movie scenes or upload your own subtitles for custom analysis."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#1e1e2e; margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#33334a; font-size:0.72rem; text-align:center;'>"
        "Powered by mock data · AI integration coming soon"
        "</p>",
        unsafe_allow_html=True,
    )

# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='cd-hero'>"
    "<div class='cd-title'>Cinematic Decoder</div>"
    "</div>"
    "<div class='cd-subtitle'>Your AI-powered guide to film language · Zero spoilers guaranteed</div>",
    unsafe_allow_html=True,
)

tab_library, tab_custom = st.tabs(["🎬 Library", "📁 Custom Analysis"])

with tab_library:
    SCENE_DATA = load_data()
    SCENE_KEYS = list(SCENE_DATA.keys())
    
    selected_scene = st.selectbox(
        "SCENE SELECTION",
        options=SCENE_KEYS,
        index=0,
        help="Choose a scene to view its vocabulary cards.",
    )

    # Scene badge
    if selected_scene:
        scene_short = selected_scene.split("—")[0].strip()
        st.markdown(
            f"<div class='scene-badge'>🎞 Now viewing &nbsp;·&nbsp; {scene_short}</div>",
            unsafe_allow_html=True,
        )

        # Section heading
        st.markdown(
            "<div class='vocab-section-heading'>📖 &nbsp;Vocabulary & Idioms</div>",
            unsafe_allow_html=True,
        )

        # Cards
        idioms = SCENE_DATA[selected_scene]
        for item in idioms:
            st.markdown(
                f"""
                <div class='idiom-card'>
                    <div class='card-index'>{item['id']}</div>
                    <div class='phrase'>"{item['phrase']}"</div>
                    <div class='translation'>↳ {item['translation']}</div>
                    <div class='context-label'>Context</div>
                    <div class='context'>{item['context']}</div>
                    <div class='no-spoiler-tag'>✓ &nbsp;No spoilers</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with tab_custom:
    st.markdown("<div class='vocab-section-heading'>📄 &nbsp;Subtitle Upload</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Subtitle File", type=["srt"], help="Upload a .srt file to extract text")
    
    if uploaded_file is not None:
        srt_content = uploaded_file.read().decode("utf-8")
        parsed_chunks = parse_srt(srt_content)
        
        st.markdown("<div class='vocab-section-heading'>💬 &nbsp;Parsed Dialogue</div>", unsafe_allow_html=True)
        with st.container(height=400):
            for chunk in parsed_chunks:
                st.markdown(
                    f"<div style='color:#8888aa; font-size:0.75rem; margin-bottom:0.2rem;'>{chunk['timestamp']}</div>"
                    f"<div style='color:#e8e8f0; font-size:0.95rem; margin-bottom:1rem;'>{chunk['text']}</div>",
                    unsafe_allow_html=True
                )
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Extract Vocabulary", use_container_width=True):
            with st.spinner("Analyzing with Gemini..."):
                try:
                    full_text = " ".join([chunk["text"] for chunk in parsed_chunks])
                    results = extract_vocabulary_with_ai(full_text)
                    
                    st.markdown("<div class='vocab-section-heading'>✨ &nbsp;AI Extraction Results</div>", unsafe_allow_html=True)
                    for i, item in enumerate(results, 1):
                        st.markdown(
                            f"""
                            <div class='idiom-card'>
                                <div class='card-index'>{str(i).zfill(2)}</div>
                                <div class='phrase'>"{item.get('phrase', '')}"</div>
                                <div class='translation'>↳ {item.get('translation', '')}</div>
                                <div class='context-label'>Context</div>
                                <div class='context'>{item.get('context', '')}</div>
                                <div class='no-spoiler-tag'>✓ &nbsp;AI Generated</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                except Exception as e:
                    st.error(f"Error during analysis: {e}")

# Footer
st.markdown(
    "<div class='cd-footer'>Cinematic Decoder &nbsp;·&nbsp; AI Movie Companion &nbsp;·&nbsp; "
    "All context is carefully curated to be 100% spoiler-free</div>",
    unsafe_allow_html=True,
)
