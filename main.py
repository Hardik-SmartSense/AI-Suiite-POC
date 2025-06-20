import tempfile

import streamlit as st
from audiorecorder import audiorecorder

import constants
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


TONE_PROFILES = constants.CONVERSATION_TONE_CONFIG


def render_settings_panel():
    print("Rendering settings panel...")
    st.sidebar.title("⚙️ Voice Assistant Settings")

    with st.sidebar.expander("🗣️ Conversation Settings", expanded=True):
        st.session_state.selected_tone = st.selectbox(
            "Select AI Conversation Tone:",
            options=list(TONE_PROFILES.keys()),
            index=1,
            key="tone_setting"
        )

        st.session_state.selected_voice_tone = st.selectbox(
            "Select Voice Tone for TTS:",
            options=list(TONE_PROFILES.keys()),
            index=1,
            key="voice_tone_setting"
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("🎛️ Settings apply to upcoming interactions.")


# -------------------------------
# Streamlit App Logic
# -------------------------------
if __name__ == "__main__":
    st.set_page_config(page_title="AI Voice Assistant", layout="centered")
    st.title("🎙️ AI Suite Voice Assistant")
    st.markdown(
        "Talk to an AI using your voice. Record, transcribe, choose tone, and get spoken responses!")
    render_settings_panel()

# -------------------------------
# Init Session State
# -------------------------------
for key in ["recorded_audio", "transcript", "response", "tone"]:
    if key not in st.session_state:
        st.session_state[key] = None

# -------------------------------
# Record Audio
# -------------------------------
with st.expander("🎤 Record Audio", expanded=True):
    metadata = {}
    audio = audiorecorder("🎤 Start Recording", "⏹ Stop Recording")
    if len(audio) > 0:
        st.session_state.recorded_audio = audio
        st.audio(audio.export(format="wav").read(), format="audio/wav")
        st.toast("✅ Audio recorded. Proceed to transcription.")
        metadata.clear()

    # -------------------------------
    # Transcribe Audio
    # -------------------------------
    if st.session_state.recorded_audio:
        with st.spinner("Transcribing..."):
            with tempfile.NamedTemporaryFile(delete=False,
                                             suffix=".wav") as f:
                st.session_state.recorded_audio.export(f.name,
                                                       format="wav")
                wav_path = f.name

            speech = get_speech_service()
            result = speech.speech_to_text(wav_path)

            st.session_state.transcript = result.get("text")
            st.toast(
                f"🧠 Transcription Done ({result.get('processing_time')}s)")
            metadata["transcription_time"] = result.get('processing_time')
        if st.session_state.transcript:
            st.write("Transcript:", st.session_state.transcript)

    # -------------------------------
    # Choose Tone & Generate Response
    # -------------------------------
    if st.session_state.transcript:
        selected_tone = st.session_state.selected_tone
        system_prompt = TONE_PROFILES[selected_tone]["prompt"]
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": st.session_state.transcript}
        ]
        with st.spinner("Contacting Assistant..."):
            openai = get_openai_service()
            result = openai.ask(messages=prompt)

            st.session_state.response = result["text"]
            st.toast("🎉 Assistant Response Received")
            metadata.update({
                "prompt_tone": selected_tone,
                "prompt_result_time": result["time_taken"],
                "prompt_tokens": result["tokens"],
            })
        if st.session_state.response:
            st.write("🧠 Response:", st.session_state.response)

    # -------------------------------
    # Say it Out Loud
    # -------------------------------
    if st.session_state.response:
        speech = get_speech_service()
        with st.spinner("Speaking..."):
            speech.text_to_speech(
                text=st.session_state.response,
                tone=st.session_state.selected_voice_tone
            )
        st.toast(
            f"✅ Done Speaking, Tone: {st.session_state.selected_voice_tone}!")
        metadata["response_tone"] = st.session_state.selected_voice_tone

    if metadata:
        with st.expander("📋 Final Interaction Report", expanded=False):
            st.markdown("### 🧾 Summary Report")

            st.markdown(f"""
            #### 🔊 Audio Summary
            - **Transcription Time:** `{metadata.get('transcription_time', 'N/A')} sec`
    
            #### 💬 AI Model Summary
            - **Tone Selected:** `{metadata.get('prompt_tone', 'N/A')}`
            - **Response Time:** `{metadata.get('prompt_result_time', 'N/A')} sec`
            - **Tokens Used:** `{metadata.get('prompt_tokens', 'N/A')}`
            
            ### Voice Settings
            - **Voice Tone for TTS:** `{metadata.get('response_tone', 'N/A')}`
            """)