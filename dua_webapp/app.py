import streamlit as st
from dua_core import parse_duas, build_pptx_bytes
from pathlib import Path

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dua Slide Generator — duas.org",
    page_icon="🕌",
    layout="centered",
)

# ── styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lateef:wght@400;700&family=Nunito:wght@300;400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f7f9fc;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #e8f4fd 0%, #f7f9fc 50%, #eef6ee 100%);
}

.main-title {
    font-family: 'Nunito', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #003380;
    text-align: center;
    margin-bottom: 0;
    letter-spacing: -0.5px;
}

.sub-title {
    font-family: 'Nunito', sans-serif;
    font-size: 1rem;
    font-weight: 400;
    color: #5a7a9a;
    text-align: center;
    margin-top: 4px;
    margin-bottom: 2rem;
}

.arabic-preview {
    font-family: 'Lateef', serif;
    font-size: 2rem;
    direction: rtl;
    text-align: center;
    color: #003380;
    line-height: 1.8;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    box-shadow: 0 2px 16px rgba(0,51,128,0.07);
    margin-bottom: 1.2rem;
}

.step-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #0066cc;
    margin-bottom: 0.4rem;
}

.preview-row {
    display: flex;
    justify-content: space-between;
    font-family: 'Nunito', sans-serif;
    font-size: 0.85rem;
    color: #666;
    padding: 0.3rem 0;
    border-bottom: 1px solid #f0f0f0;
}

.preview-row:last-child { border-bottom: none; }

.badge {
    background: #e8f0fe;
    color: #003380;
    font-family: 'Nunito', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-right: 6px;
}

.count-box {
    background: linear-gradient(135deg, #003380, #0066cc);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    font-family: 'Nunito', sans-serif;
}

.count-num {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}

.count-label {
    font-size: 0.85rem;
    opacity: 0.85;
    margin-top: 4px;
}

/* Override Streamlit button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #003380, #0066cc) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.6rem 2rem !important;
    width: 100%;
    transition: opacity 0.2s;
}

.stDownloadButton > button:hover { opacity: 0.88 !important; }

.stFileUploader label, .stTextArea label {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 600 !important;
    color: #333 !important;
}

footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🕌 Dua Slide Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">duas.org · Upload your text file, download a ready-to-present PPTX</div>', unsafe_allow_html=True)

# ── load bundled template ─────────────────────────────────────────────────────
TEMPLATE_PATH = Path(__file__).parent / "template.pptx"
if not TEMPLATE_PATH.exists():
    st.error("⚠️ `template.pptx` not found next to `app.py`. Please add it to the repo.")
    st.stop()

template_bytes = TEMPLATE_PATH.read_bytes()

# ── format guide ──────────────────────────────────────────────────────────────
with st.expander("📋 Text file format", expanded=False):
    st.markdown("""
Each **dua** is 4 lines followed by a blank line:

```
Arabic text
Transliteration
English translation
Urdu translation

Arabic text
Transliteration
English translation
Urdu translation
```

Save the file as plain `.txt` with **UTF-8** encoding.
""")

# ── upload ────────────────────────────────────────────────────────────────────
st.markdown('<div class="step-label">Step 1 — Upload your duas text file</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("", type=["txt"], label_visibility="collapsed")

if uploaded:
    raw_text = uploaded.read().decode("utf-8")
    duas = parse_duas(raw_text)

    if not duas:
        st.error("No valid dua sets found. Make sure each set has 4 lines separated by a blank line.")
        st.stop()

    # ── stats ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"""
        <div class="count-box">
            <div class="count-num">{len(duas)}</div>
            <div class="count-label">duas found</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="count-box" style="background: linear-gradient(135deg, #1a7a3c, #2ecc71); height: 100%;">
            <div class="count-num">{len(duas)}</div>
            <div class="count-label">slides will be generated</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── preview ───────────────────────────────────────────────────────────────
    st.markdown('<div class="step-label">Preview — first 3 duas</div>', unsafe_allow_html=True)
    for dua in duas[:3]:
        with st.container():
            st.markdown(f"""
            <div class="card">
                <div class="arabic-preview">{dua['arabic']}</div>
                <div style="margin-top:0.8rem">
                    <div class="preview-row">
                        <span><span class="badge">EN</span>{dua['english']}</span>
                    </div>
                    <div class="preview-row">
                        <span><span class="badge">UR</span>{dua['urdu']}</span>
                    </div>
                    <div class="preview-row">
                        <span><span class="badge">TR</span><em>{dua['transliteration']}</em></span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── generate ──────────────────────────────────────────────────────────────
    st.markdown('<div class="step-label">Step 2 — Generate & Download</div>', unsafe_allow_html=True)

    with st.spinner("Building your presentation…"):
        pptx_bytes = build_pptx_bytes(template_bytes, duas)

    st.success(f"✅ Done! {len(duas)} slide{'s' if len(duas) != 1 else ''} generated.")

    st.download_button(
        label="⬇️  Download duas.pptx",
        data=pptx_bytes,
        file_name="duas.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

else:
    st.markdown("""
    <div class="card" style="text-align:center; color:#aaa; padding: 2.5rem;">
        <div style="font-size:2.5rem">📄</div>
        <div style="font-family:'Nunito',sans-serif; margin-top:0.5rem">
            Upload a <strong>.txt</strong> file to get started
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; font-family:'Nunito',sans-serif;
            font-size:0.78rem; color:#aaa; margin-top:3rem;">
    Built for duas.org · Template layout preserved automatically
</div>
""", unsafe_allow_html=True)
