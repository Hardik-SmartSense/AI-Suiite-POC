import tempfile

import streamlit as st
from audiorecorder import audiorecorder

import constants
from services.openai_service import OpenAIService
from services.speech_service import SpeechService


# ---------------------------------------
# Cached Service Loaders
# ---------------------------------------
@st.cache_resource
def get_speech_service():
    return SpeechService(play_audio=False)

@st.cache_resource
def get_openai_service():
    return OpenAIService()


# ---------------------------------------
# Voice Agent Class
# ---------------------------------------
class VoiceAgentApp:
    def __init__(self):
        self.speech = get_speech_service()
        self.openai = get_openai_service()
        self.tone_profiles = constants.CONVERSATION_TONE_CONFIG

        self.init_session_state()
        self.render_settings_panel()

    def init_session_state(self):
        default_key_paris = {
            "audio_updated": True,
            "selected_tone": "friendly",
            "selected_voice_tone": "friendly",
            "recorded_audio": None,
            "transcript": None,
            "response": None,
            "transcription_time": None,
            "prompt_result_time": None,
            "prompt_tokens": None
        }
        for key, value in default_key_paris.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def render_settings_panel(self):
        st.sidebar.title("⚙️ Voice Assistant Settings")

        with st.sidebar.expander("🗣️ Conversation Settings", expanded=True):
            st.session_state.selected_tone = st.selectbox(
                "Select AI Conversation Tone:",
                options=list(self.tone_profiles.keys()),
                index=1,
                key="tone_setting"
            )

            st.session_state.selected_voice_tone = st.selectbox(
                "Select Voice Tone for TTS:",
                options=list(self.tone_profiles.keys()),
                index=1,
                key="voice_tone_setting"
            )

        st.sidebar.markdown("---")

    def record_audio(self):
        audio = audiorecorder("🎤 Start Recording", "⏹ Stop Recording")
        st.session_state.audio_updated = (audio == st.session_state.recorded_audio)
        if len(audio) > 0:
            st.session_state.recorded_audio = audio
            st.audio(audio.export(format="wav").read(), format="audio/wav")
            st.toast("✅ Audio recorded. Proceed to transcription.")
            return True
        return False

    def transcribe_audio(self):
        audio = st.session_state.get("recorded_audio")
        if not audio:
            return False

        if st.session_state.audio_updated is False:
            with st.spinner("Transcribing..."):
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".wav") as f:
                    audio.export(f.name, format="wav")
                    wav_path = f.name

                result = self.speech.speech_to_text(wav_path)
                st.session_state.transcript = result.get("text")
                st.session_state.transcription_time = result.get(
                    "processing_time")

                st.toast(
                    f"🧠 Transcription Done ({result.get('processing_time')}s)")
        else:
            print("Cached Transcript found, skipping AI call.")

        if st.session_state.transcript:
            st.write("Transcript:", st.session_state.transcript)
            return True
        return False

    def get_response(self):
        transcript = st.session_state.get("transcript")
        if not transcript:
            return False

        if st.session_state.audio_updated:
            print("Cached response found, skipping AI call.")
            st.write("🧠 Response:", st.session_state.response)
            return True

        tone = st.session_state.selected_tone
        system_prompt = self.tone_profiles[tone]["prompt"]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ]

        with st.spinner("Contacting Assistant..."):
            result = self.openai.ask(messages=messages)

        st.session_state.response = result["text"]
        st.session_state.update({
            "prompt_tone": tone,
            "prompt_result_time": result["time_taken"],
            "prompt_tokens": result["tokens"]
        })

        st.toast("🎉 Assistant Response Received")
        st.write("🧠 Response:", st.session_state.response)
        return True

    def speak_response(self):
        response = st.session_state.get("response")
        if not response:
            return

        if st.session_state.audio_updated:
            print("Cached TTS response found, skipping TTS call.")
            st.audio(st.session_state.output_path, format="audio/mp3")
            return

        tone = st.session_state.selected_voice_tone
        with st.spinner("Speaking..."):
            output_path = self.speech.text_to_speech(response, tone=tone)
            st.session_state.output_path = output_path

        st.audio(output_path, format="audio/mp3")
        st.toast(f"✅ Done Speaking, Tone: {tone}")

    def render_report(self):
        with st.expander("📋 Final Interaction Report", expanded=False):
            st.markdown("### 🧾 Summary Report")
            st.markdown(f"""
            #### 🔊 Audio Summary
            - **Transcription Time:** `{st.session_state.get('transcription_time', 'N/A')} sec`

            #### 💬 AI Model Summary
            - **Tone Selected:** `{st.session_state.get('selected_tone', 'N/A')}`
            - **Response Time:** `{st.session_state.get('prompt_result_time', 'N/A')} sec`
            - **Tokens Used:** `{st.session_state.get('prompt_tokens', 'N/A')}`

            ### 🎙 Voice Settings
            - **Voice Tone for TTS:** `{st.session_state.get('selected_voice_tone', 'N/A')}`
            """)

    def run(self):
        st.set_page_config(page_title="AI Voice Assistant", layout="centered")
        st.title("🎙️ AI Suite Voice Assistant")
        st.markdown(
            "Talk to an AI using your voice. Record, transcribe, choose tone, and get spoken responses!")
        with st.expander("🎤 Record Audio", expanded=True):
            if self.record_audio():
                if self.transcribe_audio():
                    if self.get_response():
                        self.speak_response()
                        self.render_report()


# ---------------------------------------
# Main
# ---------------------------------------
if __name__ == "__main__":
    print("Initializing AI Voice Assistant...")
    app = VoiceAgentApp()
    app.run()
