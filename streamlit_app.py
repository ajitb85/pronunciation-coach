import sys
import audioop
sys.modules["pyaudioop"] = audioop

import streamlit as st
import tempfile
import os
from audiorecorder import audiorecorder
from openai import OpenAI
from dotenv import load_dotenv
import json


# ---------------------------
# CONFIG & BRANDING
# ---------------------------
load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    raise Exception("OPENAI_API_KEY not set!")

client = OpenAI(api_key=api_key)

st.set_page_config(page_title="MASTER COMMUNICATOR | Pronunciation Coach", page_icon="🎤", layout="centered")

st.markdown("""
    <style>
    body {
        background-color: #ffffff;
        font-family: 'Poppins', sans-serif;
        color: #333333;
    }
    .stButton button {
        background-color: #1a73e8;
        color: white;
        font-size: 16px;
        border-radius: 8px;
        padding: 10px 20px;
        border: none;
        transition: 0.3s;
    }
    .stButton button:hover {
        background-color: #0b5ed7;
        transform: scale(1.05);
    }
    .title {
        color: #1a73e8;
        text-align: center;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 30px;
        color: #444;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'> MASTER COMMUNICATOR Pronunciation AI Coach</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Sharpen your English speaking skills with instant, AI-powered feedback</div>", unsafe_allow_html=True)

# ---------------------------
# HELPER: Analyze Pronunciation
# ---------------------------
def analyze_pronunciation(audio_path):
    # Step 1: Transcribe with Whisper
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    text = transcript.text

    # Step 2: Score with GPT
    scoring_prompt = f"""
    You are a pronunciation coach. Evaluate the following speech transcript:

    "{text}"

    Score the speaker on a scale of 1–10 for:
    - Clarity
    - Pace
    - Pronunciation Accuracy
    - Fluency
    - Energy & Confidence

    Provide results in JSON format only, like this:
    {{
        "Clarity": 8,
        "Pace": 7,
        "Pronunciation Accuracy": 9,
        "Fluency": 8,
        "Energy & Confidence": 7
    }}
    """

    eval_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": scoring_prompt}]
    )

    try:
        scores = json.loads(eval_response.choices[0].message.content)
    except:
        scores = {}

    return text, scores

def show_scores(scores):
    if not scores:
        st.warning("⚠️ Could not generate scores.")
        return
    for metric, value in scores.items():
        st.write(f"**{metric}:** {value}/10")
        st.progress(value / 10)

# ---------------------------
# MODE SELECTION
# ---------------------------
mode = st.radio("Choose how you want to test your pronunciation:", ["Upload Audio", "Record Audio"])

# ---------------------------
# UPLOAD MODE
# ---------------------------
if mode == "Upload Audio":
    uploaded_file = st.file_uploader("Upload your `.wav`, `.mp3`, or `.m4a` file", type=["wav", "mp3", "m4a"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        st.audio(tmp_path)
        if st.button("🔍 Analyze Uploaded File"):
            with st.spinner("🔵 Analyzing..."):
                transcript, feedback = analyze_pronunciation(tmp_path)
            st.success("✅ Analysis complete!")    
            st.write("**Transcript:**", transcript)
            show_scores(feedback)

# ---------------------------
# RECORD MODE
# ---------------------------
elif mode == "Record Audio":
    st.markdown("Click **Start Recording** to practice live. Stop anytime, then analyze your performance instantly.")

    audio = audiorecorder("🎙️ Start Recording", "⏹ Stop Recording")

    if len(audio) > 0:
        st.audio(audio.export().read(), format="audio/wav")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            audio.export(tmpfile.name, format="wav")
            tmpfile_path = tmpfile.name

        if st.button("🔍 Analyze Recorded Audio"):
            with st.spinner("🔵 Analyzing..."):
                transcript, feedback = analyze_pronunciation(tmpfile_path)
            st.success("✅ Analysis complete!")
            st.write("**Transcript:**", transcript)
            show_scores(feedback)

# ---------------------------
# Closing Note
# ---------------------------
st.markdown("---")
#st.markdown("💡 *Tip: Use this tool before and after your learning module to track your improvement in pronunciation, fluency, and confidence!*")
