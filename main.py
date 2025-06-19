import tempfile

import streamlit as st
from audiorecorder import audiorecorder

from services.openai_service import OpenAIService
from services.speech_service import SpeechService


# -------------------------------
# Cached Service Initializers
# -------------------------------
@st.cache_resource
def get_speech_service():
    return SpeechService(play_audio=False)

@st.cache_resource
def get_openai_service():
    return OpenAIService()


# -------------------------------
# Tone Profiles
# -------------------------------
TONE_PROFILES = {
    "formal": "You are a professional and respectful AI assistant. Use a formal and informative tone. Avoid slang.",
    "friendly": "You are a cheerful and friendly AI assistant. Use an approachable and conversational tone. Feel free to use light humor.",
    "concise": "You are a precise and efficient assistant. Keep your responses short, to the point, and avoid unnecessary elaboration.",
    "empathetic": "You are a supportive and understanding assistant. Respond kindly and acknowledge the user's feelings.",
    "technical": "You are a highly knowledgeable technical assistant. Provide detailed, structured explanations, especially for developers."
}

# -------------------------------
# Streamlit App Logic
# -------------------------------
st.set_page_config(page_title="AI Voice Assistant", layout="centered")
st.title("🎙️ AI Suite Voice Assistant")
st.markdown(
    "Talk to an AI using your voice. Record, transcribe, choose tone, and get spoken responses!")

# -------------------------------
# Init Session State
# -------------------------------
for key in ["recorded_audio", "transcript", "response", "tone"]:
    if key not in st.session_state:
        st.session_state[key] = None

# -------------------------------
# Record Audio
# -------------------------------
with st.expander("🎤 Step 1: Record Audio", expanded=True):
    audio = audiorecorder("🎤 Start Recording", "⏹ Stop Recording")
    if len(audio) > 0:
        st.session_state.recorded_audio = audio
        st.audio(audio.export(format="wav").read(), format="audio/wav")
        st.write(f"⏱ Duration: `{audio.duration_seconds:.2f}` seconds")
        st.success("✅ Audio recorded. Proceed to transcription.")

# -------------------------------
# Transcribe Audio
# -------------------------------
if st.session_state.recorded_audio:
    with st.expander("📝 Step 2: Transcribe Audio", expanded=True):
        if st.button("📄 Transcribe"):
            with st.spinner("Transcribing..."):
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".wav") as f:
                    st.session_state.recorded_audio.export(f.name,
                                                           format="wav")
                    wav_path = f.name

                speech = get_speech_service()
                result = speech.speech_to_text(wav_path)

                st.session_state.transcript = result.get("text")
                st.success("🧠 Transcription Complete")
                st.write("Transcript:", st.session_state.transcript)
                st.caption(
                    f"🕒 Processing Time: {result.get('processing_time')}s")

# -------------------------------
# Choose Tone & Generate Response
# -------------------------------
if st.session_state.transcript:
    with st.expander("🎨 Step 3: Select Tone & Generate Response",
                     expanded=True):
        selected_tone = st.selectbox("Choose Tone", list(TONE_PROFILES.keys()),
                                     index=1)
        st.session_state.tone = selected_tone

        if st.button("🤖 Generate Response"):
            prompt = [
                {"role": "system", "content": TONE_PROFILES[selected_tone]},
                {"role": "user", "content": st.session_state.transcript}
            ]
            with st.spinner("Contacting Assistant..."):
                openai = get_openai_service()
                result = openai.ask(messages=prompt)

                st.session_state.response = result["text"]
                st.success("🎉 Assistant Response Received")
                st.write("🧠 Response:", st.session_state.response)
                st.caption(
                    f"⏱ Time: {result['time_taken']}s, 🔢 Tokens: {result['tokens']}")

# -------------------------------
# Say it Out Loud
# -------------------------------
if st.session_state.response:
    with st.expander("🔊 Step 4: Listen to Response", expanded=True):
        if st.button("🔈 Speak Out"):
            speech = get_speech_service()
            with st.spinner("Speaking..."):
                speech.text_to_speech(st.session_state.response)
            st.success("✅ Done Speaking!")
