"""
Music Curator — Streamlit web app implementing the design prototype.
Dark glassmorphism aesthetic: Space Grotesk + DM Sans, teal/violet accents,
animated particle canvas, glass cards, mood-coloured badges.
"""

import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

from src.recommender import load_songs, recommend_songs

CATALOG   = "data/songs.csv"
SONGS_RAW = load_songs(CATALOG)
GENRES    = sorted({s["genre"] for s in SONGS_RAW})
MOODS     = sorted({s["mood"]  for s in SONGS_RAW})

MOOD_COLORS = {
    "happy": "#4ade80", "chill": "#38bdf8", "intense": "#f87171",
    "relaxed": "#a78bfa", "moody": "#818cf8", "focused": "#34d399",
    "energetic": "#fb923c", "sad": "#60a5fa", "nostalgic": "#f9a8d4",
    "euphoric": "#e879f9", "melancholic": "#94a3b8", "upbeat": "#facc15",
    "romantic": "#f472b6", "angry": "#ef4444",
}
GENRE_ICONS = {
    "pop": "✦", "lofi": "◎", "rock": "⚡", "ambient": "〜", "jazz": "♩",
    "synthwave": "▲", "indie pop": "◈", "hip-hop": "◉", "r&b": "♡",
    "classical": "♪", "electronic": "◆", "folk": "◇", "metal": "✸",
    "country": "◌", "blues": "◐",
}
VIBE_PRESETS = [
    "late-night drive in the rain",
    "focused morning study session",
    "rooftop party at sunset",
    "melancholic Sunday afternoon",
]

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Music Curator",
    page_icon="♫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS + fonts + particle canvas — injected via JS bridge into parent document ──

components.html("""
<script>
(function () {
  const pd = window.parent.document;

  // Fonts
  if (!pd.getElementById('mc-fonts')) {
    const lk = pd.createElement('link');
    lk.id   = 'mc-fonts';
    lk.rel  = 'stylesheet';
    lk.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600&display=swap';
    pd.head.appendChild(lk);
  }

  // CSS
  if (!pd.getElementById('mc-styles')) {
    const st = pd.createElement('style');
    st.id = 'mc-styles';
    st.textContent = `
      #MainMenu, footer { visibility: hidden !important; }
      .stDeployButton { display: none !important; }
      /* header: transparent shell only — individual bad elements hidden via JS below */
      [data-testid="stHeader"] {
        background: transparent !important; box-shadow: none !important;
        border: none !important;
      }
      /* canvas stays behind everything and never blocks clicks */
      canvas { pointer-events: none !important; z-index: 0 !important; }
      /* sidebar always above canvas */
      [data-testid="stSidebar"] { z-index: 99 !important; }
      /* hide sidebar collapse arrow — JS also targets this, belt+suspenders */
      [data-testid="stSidebarCollapseButton"],
      button[aria-label="Collapse sidebar"],
      button[aria-label="collapse sidebar"] { display: none !important; }

      :root {
        --bg: #080c18; --border: rgba(255,255,255,0.08);
        --text: rgba(255,255,255,0.88); --muted: rgba(255,255,255,0.38);
        --a1: #38bdf8; --a2: #a78bfa;
      }

      /* Dark base on body — canvas punches through transparent containers */
      html, body { background: var(--bg) !important; }
      .stApp,
      [data-testid="stAppViewContainer"],
      [data-testid="stMain"] {
        background: transparent !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
      }

      [data-testid="stMain"] .block-container {
        padding: 48px 52px !important;
        max-width: 860px !important;
      }

      /* sidebar background set via JS MutationObserver — no position overrides here */
      section[data-testid="stSidebar"] > div:first-child { padding-top: 28px !important; }

      .stRadio > label { display: none !important; }
      div[data-baseweb="radio"] { flex-direction: column !important; gap: 4px !important; }
      div[data-baseweb="radio"] > label {
        width: 100% !important; padding: 11px 14px !important; border-radius: 12px !important;
        background: transparent !important; border: none !important; cursor: pointer !important;
        transition: background 0.2s !important;
      }
      div[data-baseweb="radio"] > label:hover { background: rgba(255,255,255,0.06) !important; }
      div[data-baseweb="radio"] > label[data-checked="true"] {
        background: rgba(56,189,248,0.1) !important;
        border: 1px solid rgba(56,189,248,0.25) !important;
      }
      div[data-baseweb="radio"] > label span:last-child {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 13px !important; font-weight: 700 !important;
      }

      /* Textarea — solid dark bg so white text is visible */
      textarea,
      .stTextArea textarea,
      div[data-baseweb="textarea"] textarea {
        background: #0f1629 !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important; color: #e2e8f0 !important;
        font-family: 'DM Sans', sans-serif !important; font-size: 14px !important;
        caret-color: #38bdf8 !important;
      }
      textarea:focus,
      .stTextArea textarea:focus {
        border-color: rgba(56,189,248,0.5) !important;
        box-shadow: 0 0 0 2px rgba(56,189,248,0.15) !important;
        outline: none !important;
      }
      textarea::placeholder,
      .stTextArea textarea::placeholder { color: rgba(255,255,255,0.25) !important; }
      .stTextArea > label { display: none !important; }

      .stSelectbox > label {
        font-size: 11px !important; font-weight: 700 !important;
        letter-spacing: 0.08em !important; color: rgba(255,255,255,0.3) !important;
        font-family: 'DM Sans', sans-serif !important; text-transform: uppercase !important;
      }
      .stSelectbox [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important; color: rgba(255,255,255,0.82) !important;
      }
      [data-baseweb="popover"], [data-baseweb="menu"] {
        background: #0f1629 !important; border: 1px solid rgba(255,255,255,0.1) !important;
      }
      [data-baseweb="option"] { background: #0f1629 !important; color: rgba(255,255,255,0.82) !important; }
      [data-baseweb="option"]:hover { background: rgba(56,189,248,0.1) !important; }

      .stSlider > label {
        font-size: 11px !important; font-weight: 700 !important;
        letter-spacing: 0.08em !important; color: rgba(255,255,255,0.3) !important;
        font-family: 'DM Sans', sans-serif !important; text-transform: uppercase !important;
      }
      .stSlider [data-testid="stSliderTrack"] { background: rgba(255,255,255,0.1) !important; }
      .stSlider p { color: rgba(255,255,255,0.6) !important; font-family: 'DM Sans', sans-serif !important; }

      .stButton > button {
        border-radius: 12px !important; font-family: 'Space Grotesk', sans-serif !important;
        font-size: 14px !important; font-weight: 700 !important; letter-spacing: 0.03em !important;
        transition: opacity 0.2s, transform 0.15s !important;
      }
      .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #38bdf8, #a78bfa) !important;
        border: none !important; color: #fff !important;
        box-shadow: 0 4px 24px rgba(56,189,248,0.25) !important;
      }
      .stButton > button[kind="primary"]:hover { opacity: 0.9 !important; transform: translateY(-1px) !important; }
      .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 99px !important; color: rgba(255,255,255,0.5) !important;
        font-size: 12px !important; padding: 5px 14px !important;
      }
      .stButton > button[kind="secondary"]:hover {
        background: rgba(56,189,248,0.1) !important;
        border-color: rgba(56,189,248,0.3) !important; color: #38bdf8 !important;
      }

      .stSpinner > div > div { border-top-color: var(--a1) !important; }

      ::-webkit-scrollbar { width: 4px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 99px; }

      .glass-card {
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.09);
        border-radius: 18px; padding: 24px; margin-bottom: 16px; backdrop-filter: blur(12px);
      }
      .song-card {
        background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px; padding: 20px; margin-bottom: 12px; backdrop-filter: blur(12px);
        transition: border-color 0.25s;
      }
      .song-card:hover { border-color: rgba(56,189,248,0.25); }
      .badge {
        display: inline-block; padding: 2px 10px; border-radius: 99px;
        font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
        margin-right: 6px;
      }
      .page-eyebrow { font-size: 10px; font-weight: 700; letter-spacing: 0.15em; color: var(--a1); margin-bottom: 8px; }
      .page-title {
        font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 800; line-height: 1.1;
        background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.55));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: inline-block; margin-bottom: 10px;
      }
      .page-subtitle { font-size: 14px; color: rgba(255,255,255,0.38); line-height: 1.6; margin-bottom: 32px; }
      .metric-mini { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 6px 10px; border: 1px solid rgba(255,255,255,0.06); }
      .metric-mini .mlabel { font-size: 9px; color: rgba(255,255,255,0.3); font-weight: 700; letter-spacing: 0.06em; }
      .metric-mini .mval   { font-size: 13px; color: rgba(255,255,255,0.75); font-weight: 600; margin-top: 2px; }
      details summary { font-size: 11px; color: rgba(255,255,255,0.3); cursor: pointer; list-style: none; margin-top: 12px; user-select: none; }
      details summary::-webkit-details-marker { display: none; }
      details[open] summary { color: rgba(255,255,255,0.5); }
    `;
    pd.head.appendChild(st);
  }

  // Particle canvas
  if (!pd.getElementById('mc-particles')) {
    const cv = pd.createElement('canvas');
    cv.id = 'mc-particles';
    Object.assign(cv.style, { position:'fixed', inset:'0', zIndex:'0', pointerEvents:'none', width:'100vw', height:'100vh' });
    pd.body.insertBefore(cv, pd.body.firstChild);
    const ctx = cv.getContext('2d');
    let W, H, ps;
    function rsz() { W = cv.width = window.parent.innerWidth; H = cv.height = window.parent.innerHeight; }
    function mkP() { return { x:Math.random()*W, y:Math.random()*H, vx:(Math.random()-.5)*.25, vy:(Math.random()-.5)*.25, r:Math.random()*1.5+.5 }; }
    function init() { rsz(); ps = Array.from({length:80}, mkP); }
    function draw() {
      ctx.clearRect(0,0,W,H);
      for (const p of ps) { p.x+=p.vx; p.y+=p.vy; if(p.x<0)p.x=W; if(p.x>W)p.x=0; if(p.y<0)p.y=H; if(p.y>H)p.y=0; }
      for (let i=0;i<ps.length;i++) for (let j=i+1;j<ps.length;j++) {
        const dx=ps[i].x-ps[j].x, dy=ps[i].y-ps[j].y, d=Math.sqrt(dx*dx+dy*dy);
        if (d<120) { ctx.beginPath(); ctx.strokeStyle=`rgba(56,189,248,${.12*(1-d/120)})`; ctx.lineWidth=.6; ctx.moveTo(ps[i].x,ps[i].y); ctx.lineTo(ps[j].x,ps[j].y); ctx.stroke(); }
      }
      for (const p of ps) { ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fillStyle='rgba(167,139,250,0.55)'; ctx.fill(); }
      requestAnimationFrame(draw);
    }
    window.parent.addEventListener('resize', rsz);
    init(); draw();
  }

  // Surgical DOM cleanup — hide bad header chrome, lock sidebar permanently open.
  const HIDE_IDS = ['stToolbar', 'stDecoration', 'stStatusWidget'];
  function cleanDOM() {
    // Sidebar background
    const sb = pd.querySelector('[data-testid="stSidebar"]');
    if (sb) {
      sb.style.setProperty('background', '#0e1e38', 'important');
      sb.style.setProperty('border-right', '1px solid rgba(56,189,248,0.35)', 'important');
    }
    // Hide specific header chrome without touching the container
    HIDE_IDS.forEach(id => {
      const el = pd.querySelector('[data-testid="' + id + '"]');
      if (el) el.style.setProperty('display', 'none', 'important');
    });
    // Hide the sidebar's own collapse arrow (belt+suspenders: CSS + JS)
    // so the sidebar can never be accidentally closed.
    const COLLAPSE_SELECTORS = [
      '[data-testid="stSidebarCollapseButton"]',
      'button[aria-label="Collapse sidebar"]',
      'button[aria-label="collapse sidebar"]',
      '[data-testid="stSidebar"] > div:first-child > div:first-child > button',
    ];
    COLLAPSE_SELECTORS.forEach(sel => {
      pd.querySelectorAll(sel).forEach(el => el.style.setProperty('display', 'none', 'important'));
    });
  }

  cleanDOM();
  new MutationObserver(cleanDOM).observe(pd.body, { childList: true, subtree: true });

})();
</script>
""", height=0)

# ── Helpers ───────────────────────────────────────────────────────────────────

def badge(label, color):
    return (f'<span class="badge" style="background:{color}18;color:{color};'
            f'border:1px solid {color}40">{label}</span>')

def energy_bar(value):
    pct   = round(value * 100)
    color = "#38bdf8" if value < 0.35 else "#a78bfa" if value < 0.65 else "#fb923c" if value < 0.85 else "#f87171"
    return (
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<div style="flex:1;height:4px;background:rgba(255,255,255,0.08);border-radius:9px">'
        f'<div style="width:{pct}%;height:100%;border-radius:9px;background:{color}"></div>'
        f'</div>'
        f'<span style="font-size:11px;color:rgba(255,255,255,0.45);width:28px;text-align:right">{pct}%</span>'
        f'</div>'
    )

def song_card(rank, song, score, explanation):
    mood_color  = MOOD_COLORS.get(song["mood"], "#94a3b8")
    genre_icon  = GENRE_ICONS.get(song["genre"], "•")
    score_color = "#4ade80" if score >= 3.5 else "#a78bfa" if score >= 2.5 else "#38bdf8"
    st.markdown(f"""
<div class="song-card">
  <div style="display:flex;align-items:flex-start;gap:16px">
    <div style="min-width:36px;height:36px;border-radius:10px;display:flex;align-items:center;
      justify-content:center;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);
      font-size:13px;font-weight:700;color:rgba(255,255,255,0.4);flex-shrink:0">{rank}</div>
    <div style="flex:1;min-width:0">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
        <div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;
            color:rgba(255,255,255,0.92);line-height:1.3">{song["title"]}</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.4);margin-top:2px">{song["artist"]}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
          <div style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;
            color:{score_color}">{score:.2f}</div>
          <div style="font-size:10px;color:rgba(255,255,255,0.3);line-height:1.2">match<br/>score</div>
        </div>
      </div>
      <div style="margin-top:10px">
        {badge(f"{genre_icon} {song['genre']}", "#7dd3fc")}
        {badge(song["mood"], mood_color)}
      </div>
      <div style="margin-top:10px">
        <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-bottom:4px">ENERGY</div>
        {energy_bar(song["energy"])}
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px">
        <div class="metric-mini">
          <div class="mlabel">TEMPO</div>
          <div class="mval">{song["tempo_bpm"]:.0f} bpm</div>
        </div>
        <div class="metric-mini">
          <div class="mlabel">VALENCE</div>
          <div class="mval">{round(song["valence"]*100)}%</div>
        </div>
        <div class="metric-mini">
          <div class="mlabel">DANCE</div>
          <div class="mval">{round(song["danceability"]*100)}%</div>
        </div>
      </div>
      <details>
        <summary>▼ Why this song?</summary>
        <div style="margin-top:8px;padding:10px 14px;border-radius:10px;
          background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
          font-size:12px;color:rgba(255,255,255,0.5);line-height:1.7">{explanation}</div>
      </details>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:36px;padding:0 4px">
  <div style="width:38px;height:38px;border-radius:11px;display:flex;align-items:center;
    justify-content:center;font-size:18px;
    background:linear-gradient(135deg,#38bdf8,#a78bfa);
    box-shadow:0 4px 20px rgba(56,189,248,0.35)">♫</div>
  <div>
    <div style="font-family:'Space Grotesk',sans-serif;font-weight:800;font-size:15px;
      color:rgba(255,255,255,0.92);line-height:1">Music</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-weight:800;font-size:15px;
      background:linear-gradient(90deg,#38bdf8,#a78bfa);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2">Curator</div>
  </div>
</div>
<div style="font-size:10px;font-weight:700;letter-spacing:0.1em;
  color:rgba(255,255,255,0.25);margin-bottom:10px;padding-left:4px">MODE</div>
""", unsafe_allow_html=True)

    mode = st.radio("Mode", ["✦  Playlist Curator", "◈  Direct Search"],
                    label_visibility="collapsed")

    st.markdown("""
<div style="margin-top:32px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06)">
  <div style="font-size:11px;color:rgba(255,255,255,0.2);line-height:2.2">
    <div>🎵 20 songs in catalog</div>
    <div>🤖 Gemini 2.5 Flash</div>
    <div>⚡ Scoring: genre · mood · energy</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Agent mode ────────────────────────────────────────────────────────────────

def agent_mode():
    st.markdown("""
<div class="page-eyebrow">AI-POWERED</div>
<div class="page-title">Playlist Curator</div>
<p class="page-subtitle">Describe a mood, moment, or scenario — the AI will build your perfect soundtrack.</p>
""", unsafe_allow_html=True)

    if "vibe_text" not in st.session_state:
        st.session_state.vibe_text = ""

    st.markdown('<div style="font-size:11px;font-weight:700;letter-spacing:0.08em;'
                'color:rgba(255,255,255,0.3);margin-bottom:8px">YOUR VIBE</div>',
                unsafe_allow_html=True)

    vibe = st.text_area(
        "vibe", value=st.session_state.vibe_text, height=100,
        placeholder="e.g. something moody for a late-night drive in the rain…",
        label_visibility="collapsed",
    )
    st.session_state.vibe_text = vibe

    st.markdown('<div style="font-size:11px;color:rgba(255,255,255,0.25);margin:8px 0 4px">'
                'QUICK PICKS</div>', unsafe_allow_html=True)
    chip_cols = st.columns(4)
    for i, preset in enumerate(VIBE_PRESETS):
        if chip_cols[i].button(preset, key=f"chip_{i}", type="secondary"):
            st.session_state.vibe_text = preset
            st.rerun()

    curate = st.button("✦  Curate Playlist", type="primary",
                       disabled=not st.session_state.vibe_text.strip())

    if curate:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.markdown('<div class="glass-card" style="border-color:rgba(248,113,113,0.3)">'
                        '<span style="color:#f87171;font-weight:600">⚠ GEMINI_API_KEY not set.'
                        '</span></div>', unsafe_allow_html=True)
        else:
            with st.spinner("Interpreting vibe · Scoring catalog · Writing narrative…"):
                try:
                    from src.agent import PlaylistAgent
                    agent = PlaylistAgent(catalog_path=CATALOG, api_key=api_key)
                    profile   = agent._extract_profile(st.session_state.vibe_text)
                    results   = agent._get_songs(profile, k=5)
                    narrative = agent._write_narrative(st.session_state.vibe_text, results)
                    st.session_state.agent_cache = dict(
                        vibe=st.session_state.vibe_text,
                        profile=profile, results=results, narrative=narrative,
                    )
                except Exception as exc:
                    st.markdown(
                        f'<div class="glass-card" style="border-color:rgba(248,113,113,0.3)">'
                        f'<span style="color:#f87171;font-weight:600">⚠ {exc}</span></div>',
                        unsafe_allow_html=True,
                    )

    cache = st.session_state.get("agent_cache")
    if cache:
        profile   = cache["profile"]
        results   = cache["results"]
        narrative = cache["narrative"]
        mood_color = MOOD_COLORS.get(profile["mood"], "#94a3b8")

        st.markdown(f"""
<div class="glass-card" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
  <div style="font-size:12px;color:rgba(255,255,255,0.4);margin-right:4px">INTERPRETED AS</div>
  {badge(f'♩ {profile["genre"]}', "#7dd3fc")}
  {badge(profile["mood"], mood_color)}
  {badge(f'⚡ energy {round(profile["energy"]*100)}%', "#a78bfa")}
</div>

<div class="glass-card" style="border-left:3px solid #38bdf8">
  <div style="font-size:10px;font-weight:700;letter-spacing:0.1em;
    color:rgba(255,255,255,0.25);margin-bottom:12px">CURATOR'S NARRATIVE</div>
  <p style="font-size:14px;line-height:1.85;color:rgba(255,255,255,0.72);margin:0">{narrative}</p>
</div>

<div style="font-size:11px;font-weight:700;letter-spacing:0.08em;
  color:rgba(255,255,255,0.25);margin-bottom:12px;margin-top:8px">
  TOP {len(results)} MATCHES
</div>""", unsafe_allow_html=True)

        for i, (s, score, explanation) in enumerate(results):
            song_card(i + 1, s, score, explanation)

# ── Direct mode ───────────────────────────────────────────────────────────────

def direct_mode():
    st.markdown("""
<div class="page-eyebrow">PRECISION MATCHING</div>
<div class="page-title">Direct Search</div>
<p class="page-subtitle">Set your exact preferences and see how every song scores against them.</p>
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        genre = st.selectbox("Genre", GENRES)
    with col2:
        mood = st.selectbox("Mood", MOODS)

    energy_pct = st.slider("Energy Level", 0, 100, 50, step=5, format="%d%%",
                            help="0 = very calm / ambient  →  100 = very intense / loud")
    energy = energy_pct / 100.0

    k = st.slider("Results", 1, 10, 5)

    if st.button("◈  Get Recommendations", type="primary"):
        prefs   = {"genre": genre, "mood": mood, "energy": energy}
        results = recommend_songs(prefs, SONGS_RAW, k=k)
        st.session_state.direct_cache = dict(prefs=prefs, results=results)

    cache = st.session_state.get("direct_cache")
    if cache:
        prefs      = cache["prefs"]
        results    = cache["results"]
        mood_color = MOOD_COLORS.get(prefs["mood"], "#94a3b8")

        st.markdown(f"""
<div class="glass-card" style="padding:12px 20px;display:flex;gap:10px;flex-wrap:wrap;align-items:center">
  <div style="font-size:12px;color:rgba(255,255,255,0.4)">PROFILE</div>
  {badge(prefs["genre"], "#7dd3fc")}
  {badge(prefs["mood"], mood_color)}
  {badge(f'energy {round(prefs["energy"]*100)}%', "#a78bfa")}
</div>
<div style="font-size:11px;font-weight:700;letter-spacing:0.08em;
  color:rgba(255,255,255,0.25);margin-bottom:12px">TOP {len(results)} MATCHES</div>
""", unsafe_allow_html=True)

        for i, (s, score, explanation) in enumerate(results):
            song_card(i + 1, s, score, explanation)

# ── Route ─────────────────────────────────────────────────────────────────────

if "✦" in mode:
    agent_mode()
else:
    direct_mode()
