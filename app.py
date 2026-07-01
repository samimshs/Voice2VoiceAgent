"""
Phase 7 — Streamlit UI
Voice-to-Voice AI Product Assistant
"""
import os, sys, tempfile
import streamlit as st

sys.path.insert(0, ".")

from speech.asr import transcribe
from speech.tts import speak
from agents.router import router_node
from agents.planner import planner_node
from agents.retriever import retriever_node
from agents.answerer import answerer_node

st.set_page_config(
    page_title="Voice AI Product Assistant",
    page_icon="🎙",
    layout="wide",
    initial_sidebar_state="collapsed",
)
os.makedirs("temp", exist_ok=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "transcript":      "",
    "result":          None,
    "tts_path":        None,
    "last_audio_hash": None,
    "status":          "idle",   # idle | recorded | running | done
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.stDeployButton  { display: none; }

.stApp { background: #f1f5f9 !important; }

/* Header */
.app-header {
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
}
.app-header h1 {
    font-size: 2rem; font-weight: 700; margin: 0 0 0.4rem;
    background: linear-gradient(90deg, #6366f1, #0284c7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.app-header p { color: #64748b; font-size: 0.95rem; margin: 0; }

/* Mic panel */
.mic-panel {
    text-align: center;
    background: #ffffff;
    border: 1px solid #c7d2fe;
    border-radius: 16px;
    padding: 1.5rem 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(99,102,241,0.08);
}
.mic-instruction {
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem;
}

/* Audio input — slightly bigger controls, no layout shift (zoom affects flow; scale does not) */
div[data-testid="stAudioInput"] {
    zoom: 1.18;
}

/* Status pill */
.status-pill {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.3rem 0.9rem; border-radius: 20px;
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
}
.pill-idle     { background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; }
.pill-recorded { background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; }
.pill-running  { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
.pill-done     { background: #dcfce7; color: #16a34a; border: 1px solid #86efac; }

/* Transcript */
.transcript-box {
    background: #eff6ff;
    border-left: 3px solid #6366f1;
    border-radius: 0 10px 10px 0;
    padding: 0.75rem 1rem;
    color: #1e293b; font-size: 0.95rem;
    line-height: 1.6; font-style: italic; margin: 1rem 0;
}

/* Answer */
.answer-box {
    background: linear-gradient(135deg, #eef2ff, #eff6ff);
    border: 1px solid #c7d2fe;
    border-radius: 14px; padding: 1.2rem 1.4rem;
    color: #1e293b; font-size: 1rem; line-height: 1.75; margin-bottom: 1rem;
}

/* Section heading */
.sec-heading {
    color: #94a3b8; font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.12em; margin: 1.4rem 0 0.6rem;
}

/* Product cards */
.product-card {
    background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.product-card:hover { border-color: #a5b4fc; }
.product-title  { font-weight: 600; color: #0f172a; font-size: 0.92rem; margin-bottom: 0.45rem; }
.product-badges { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
.b { padding: 0.18rem 0.55rem; border-radius: 6px; font-size: 0.72rem; font-weight: 600; }
.b-cat    { background: #eef2ff; color: #4f46e5; }
.b-price  { background: #dcfce7; color: #16a34a; }
.b-rating { background: #fef9c3; color: #a16207; }
.b-match  { background: #f1f5f9; color: #64748b; }
.b-avail  { background: #e0f2fe; color: #0284c7; }

/* Agent timeline */
.timeline { position: relative; padding-left: 1.5rem; }
.timeline::before {
    content: ''; position: absolute; left: 10px; top: 0; bottom: 0;
    width: 1px; background: linear-gradient(to bottom, #6366f1, rgba(99,102,241,0));
}
.tl-item { position: relative; margin-bottom: 1rem; }
.tl-dot  {
    position: absolute; left: -1.5rem; top: 4px;
    width: 10px; height: 10px; border-radius: 50%;
    background: #6366f1; border: 2px solid #f1f5f9;
}
.tl-label { font-size: 0.8rem; font-weight: 700; color: #4f46e5; margin-bottom: 0.2rem; }
.tl-value { font-size: 0.78rem; color: #64748b; line-height: 1.5; }

/* Citation */
.citation-item {
    display: flex; align-items: flex-start; gap: 0.5rem;
    padding: 0.4rem 0; border-bottom: 1px solid #f1f5f9;
    font-size: 0.82rem; color: #475569;
}
.citation-dot { color: #6366f1; flex-shrink: 0; margin-top: 2px; }

/* Placeholder */
.placeholder {
    text-align: center; padding: 3rem 2rem;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px; color: #94a3b8;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🎙 Voice AI Product Assistant</h1>
  <p>Speak a product query — the assistant searches the catalog and answers by voice</p>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
left, right = st.columns([2, 3], gap="large")

# ── LEFT: Mic + transcript ────────────────────────────────────────────────────
with left:
    pill_map = {
        "idle":     ("pill-idle",     "○  Waiting for voice input"),
        "recorded": ("pill-recorded", "◉  Voice captured"),
        "running":  ("pill-running",  "⟳  Processing..."),
        "done":     ("pill-done",     "✓  Done"),
    }
    pill_cls, pill_txt = pill_map[st.session_state.status]

    st.markdown(f"""
    <div class="mic-panel">
        <div class="mic-instruction">Click mic · Speak · Click to stop</div>
    </div>
    """, unsafe_allow_html=True)

    audio_input = st.audio_input(label="", label_visibility="collapsed")

    st.markdown(f"""
    <div style="text-align:center;margin-top:0.5rem;">
        <span class="status-pill {pill_cls}">{pill_txt}</span>
    </div>
    """, unsafe_allow_html=True)

    # Process new recording → transcribe → auto-trigger pipeline
    if audio_input is not None:
        audio_bytes = audio_input.read()
        if len(audio_bytes) > 2000:
            audio_hash = hash(audio_bytes)
            if audio_hash != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_hash
                st.session_state.result   = None
                st.session_state.tts_path = None

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir="temp") as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name

                with st.spinner("Transcribing..."):
                    st.session_state.transcript = transcribe(tmp_path)
                os.unlink(tmp_path)
                st.session_state.status = "recorded"
                st.rerun()

    # Show transcript when available
    if st.session_state.transcript:
        st.markdown(f"""
        <div class="sec-heading">Your query</div>
        <div class="transcript-box">"{st.session_state.transcript}"</div>
        """, unsafe_allow_html=True)

# ── RIGHT: Auto-run pipeline or show results ──────────────────────────────────
with right:

    # ── Auto-run when transcript is ready ─────────────────────────────────────
    if st.session_state.status == "recorded":
        state = {
            "user_query":   st.session_state.transcript,
            "intent":       {}, "plan":         {},
            "rag_results":  [], "web_results":  [],
            "final_answer": "", "citations":    [],
            "safety_flags": [],
        }

        with st.status("🤖 Assistant is working...", expanded=True) as status_ui:
            st.write("🎙️ Voice transcribed successfully")

            st.write("🧠 Classifying intent and constraints...")
            state.update(router_node(state))

            _unsafe     = bool(state.get("safety_flags"))
            _off_topic  = state.get("intent", {}).get("task_type") != "product_search"

            if _unsafe or _off_topic:
                if _unsafe:
                    st.write("🚫 Unsafe content detected — stopping.")
                    status_ui.update(label="⚠️ Unsafe request", state="error")
                    state["final_answer"] = (
                        "I'm sorry, I can't help with that — it looks like the request involves "
                        "unsafe or harmful content. I'm only able to help you find and compare products."
                    )
                else:
                    st.write("↩️ Off-topic query — this assistant only handles product search.")
                    status_ui.update(label="↩️ Off-topic", state="error")
                    state["final_answer"] = (
                        "I'm a product search assistant, so I can only help you find and compare products. "
                        "Try something like: \"find me wireless headphones under $50\" "
                        "or \"show me eco-friendly cleaning products\"."
                    )
            else:
                st.write("📋 Planning search strategy...")
                state.update(planner_node(state))

                tools = state.get("plan", {}).get("tools", [])
                st.write(f"🔍 Searching private catalog...")
                if "web.search" in tools:
                    st.write("🌐 Checking live web prices...")
                state.update(retriever_node(state))

                n_rag = len(state.get("rag_results", []))
                n_web = len(state.get("web_results", []))
                st.write(f"📦 Found {n_rag} catalog product(s)" + (f" + {n_web} web result(s)" if n_web else ""))

                st.write("✍️ Crafting recommendation...")
                state.update(answerer_node(state))

                st.write("🔊 Generating voice response...")
                st.session_state.tts_path = speak(state["final_answer"])

                status_ui.update(label="✅ Done! Scroll down to see results.", state="complete", expanded=False)

        st.session_state.result = state
        st.session_state.status = "done"
        st.rerun()

    # ── Show results ──────────────────────────────────────────────────────────
    elif st.session_state.status == "done" and st.session_state.result:
        result = st.session_state.result

        # Answer + audio
        st.markdown('<div class="sec-heading">Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="answer-box">{result["final_answer"]}</div>', unsafe_allow_html=True)
        if st.session_state.tts_path and os.path.exists(st.session_state.tts_path):
            with open(st.session_state.tts_path, "rb") as f:
                st.audio(f.read(), format="audio/mp3", autoplay=True)

        # Product cards
        rag = result.get("rag_results", [])
        if rag:
            st.markdown('<div class="sec-heading">Products found</div>', unsafe_allow_html=True)
            for p in rag[:5]:
                rating_str = f"⭐ {p['rating']}" if p.get("rating", -1) != -1 else ""
                match_pct  = int(p.get("match_score", 0) * 100)
                st.markdown(f"""
                <div class="product-card">
                    <div class="product-title">{p['title']}</div>
                    <div class="product-badges">
                        <span class="b b-cat">{p.get('category','')}</span>
                        <span class="b b-price">${p['price']}</span>
                        {"<span class='b b-rating'>"+rating_str+"</span>" if rating_str else ""}
                        {"<span class='b b-avail'>"+p.get('availability','')+"</span>" if p.get('availability') else ""}
                        <span class="b b-match">{match_pct}% match</span>
                    </div>
                </div>""", unsafe_allow_html=True)

        # Agent timeline
        intent = result.get("intent", {})
        plan   = result.get("plan",   {})
        st.markdown('<div class="sec-heading">Agent steps</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="timeline">
            <div class="tl-item"><div class="tl-dot"></div>
                <div class="tl-label">Router — Intent</div>
                <div class="tl-value">Budget: {"$"+str(intent.get('budget')) if intent.get('budget') else 'any'} &nbsp;·&nbsp; Category: {intent.get('category') or 'any'} &nbsp;·&nbsp; Flags: {intent.get('safety_flags') or 'none'}</div>
            </div>
            <div class="tl-item"><div class="tl-dot"></div>
                <div class="tl-label">Planner — Decision</div>
                <div class="tl-value">Tools: {" + ".join(plan.get('tools', []))} &nbsp;·&nbsp; {plan.get('reason','')}</div>
            </div>
            <div class="tl-item"><div class="tl-dot"></div>
                <div class="tl-label">Retriever — Results</div>
                <div class="tl-value">Private: {len(rag)} products &nbsp;·&nbsp; Web: {len(result.get('web_results', []))} results</div>
            </div>
            <div class="tl-item"><div class="tl-dot"></div>
                <div class="tl-label">Answerer — Grounded response + critic check</div>
                <div class="tl-value">{len(result.get('citations', []))} citation(s)</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Citations
        citations = result.get("citations", [])
        web       = [w for w in result.get("web_results", []) if w.get("url") and "error" not in w]
        if citations or web:
            st.markdown('<div class="sec-heading">Citations</div>', unsafe_allow_html=True)
            for c in citations:
                st.markdown(f'<div class="citation-item"><span class="citation-dot">◆</span><span><b>{c.get("title","")}</b> — ${c.get("price","")} <span style="color:#475569;font-size:0.75rem;">private catalog</span></span></div>', unsafe_allow_html=True)
            for w in web:
                st.markdown(f'<div class="citation-item"><span class="citation-dot">◇</span><a href="{w["url"]}" target="_blank" style="color:#38bdf8;text-decoration:none;">{w.get("title",w["url"])}</a> <span style="color:#475569;font-size:0.75rem;">web</span></div>', unsafe_allow_html=True)

    # ── Placeholder ───────────────────────────────────────────────────────────
    else:
        st.markdown("""
        <div class="placeholder">
            <div style="font-size:3rem;margin-bottom:1rem;">🛍️</div>
            <div style="font-size:0.95rem;">Record a query on the left<br>to see product recommendations here</div>
        </div>""", unsafe_allow_html=True)
