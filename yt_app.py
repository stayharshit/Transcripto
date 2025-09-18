import os
import re
import streamlit as st
import base64
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import openai
from openai import OpenAI

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

def summarize_with_openai(transcript: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or gpt-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes transcripts."},
                {"role": "user", "content": transcript},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception as e:
        # Fallback: return None instead of crashing
        print(f"OpenAI error: {e}")
        st.warning("⚠️ Unable to generate AI summary due to technical issues. Please try again later.")
        return None
# --- Load external CSS ---
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Load external HTML and inject variables ---
def load_html(file_path, replacements=None):
    with open(file_path) as f:
        html = f.read()
    if replacements:
        for key, value in replacements.items():
            html = html.replace(f"{{{{{key}}}}}", value)  # replace {{key}} with value
    st.markdown(html, unsafe_allow_html=True)

# --- Convert image to Base64 ---
def load_logo_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_adsense():
    adsense_code = """
    <iframe src="https://your-ad-url.com" style="width:100%; height:90px; border:none;"></iframe>
    """
    st.markdown(adsense_code, unsafe_allow_html=True)

# --- Extract video ID from YouTube URL ---
def get_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be\/|\/v\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# --- Fetch transcript text ---
def fetch_transcript_text(video_id: str):
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en"])
        texts = [s["text"] if isinstance(s, dict) else getattr(s, "text", "") for s in fetched]
        return " ".join(texts)
    except NoTranscriptFound:
        raise NoTranscriptFound("No transcript found for this video.")
    except TranscriptsDisabled:
        raise TranscriptsDisabled("Transcripts are disabled for this video.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

# --- Streamlit config ---
st.set_page_config(page_title="Transcripto", page_icon="🎬", layout="centered")

# --- Inject CSS ---
load_css("assets/styles.css")

# --- Load Logo and Inject Header ---
logo_base64 = load_logo_base64("assets/image.png")
load_html("assets/header.html", {"logo_base64": logo_base64})

# --- Main content ---
st.markdown("<h1>🎬 YouTube AI Summarizer</h1>", unsafe_allow_html=True)
st.markdown("<h3>Paste any YouTube link and get an instant AI-powered summary & transcript</h3>", unsafe_allow_html=True)

url = st.text_input("👉 Paste YouTube link here")

if st.button("Summarize Video") and url:
    video_id = get_video_id(url)

    if not video_id:
        st.error("❌ Invalid YouTube URL.")
    else:
        with st.spinner("Fetching transcript... ⏳"):
            try:
                transcript_text = fetch_transcript_text(video_id)
                st.session_state["transcript"] = transcript_text
            except (NoTranscriptFound, TranscriptsDisabled):
                st.error("❌ No transcript found (captions disabled or missing).")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

if "transcript" in st.session_state:
    st.success("✅ Transcript fetched successfully!")

    with st.spinner("Summarizing with OpenAI... ✨"):
        summary = summarize_with_openai(st.session_state["transcript"])
        if summary:
            st.session_state["summary"] = summary

# --- Show Results ---
if "transcript" in st.session_state:
    tab1, tab2 = st.tabs(["📌 AI Summary", "📜 Transcript"])

    with tab1:
        st.subheader("✨ AI Summary")
        if "summary" in st.session_state and st.session_state["summary"]:
            st.write(st.session_state["summary"])
            st.download_button(
                "⬇️ Download Summary",
                st.session_state["summary"],
                "summary.txt",
                key="download_summary_tab"
            )
        else:
            st.info("⚠️ AI summary couldn't be generated due to a technical issue.")

    with tab2:
        st.subheader("📜 Full Transcript")
        st.text_area("Transcript", st.session_state["transcript"], height=400)
        st.download_button(
            "⬇️ Download Transcript",
            st.session_state["transcript"],
            "transcript.txt",
            key="download_transcript_tab"
        )

# --- Inject Footer ---
load_html("assets/footer.html")
