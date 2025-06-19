import tempfile

import streamlit as st
from audiorecorder import audiorecorder

TONE_PROFILES = {
    "formal": "You are a professional and respectful AI assistant. Use a formal and informative tone. Avoid slang.",
    "friendly": "You are a cheerful and friendly AI assistant. Use an approachable and conversational tone. Feel free to use light humor.",
    "concise": "You are a precise and efficient assistant. Keep your responses short, to the point, and avoid unnecessary elaboration.",
    "empathetic": "You are a supportive and understanding assistant. Respond kindly and acknowledge the user's feelings.",
    "technical": "You are a highly knowledgeable technical assistant. Provide detailed, structured explanations, especially for developers."
}

@st.cache_resource
def get_speech_service():
    from services.speech_service import SpeechService
    return SpeechService(play_audio=False)


@st.cache_resource
def get_openai_service():
    from services.openai_service import OpenAIService
    return OpenAIService()

class VoiceApp:
    def __init__(self):
        self.speech_service = get_speech_service()
        self.openai_service = get_openai_service()
        self.tone = st.selectbox(
            "Choose Conversation Tone",
            options=["formal", "friendly", "concise", "empathetic",
                     "technical"],
            index=1
        )

    def run(self):
        st.set_page_config(page_title="AI Voice Assistant", layout="centered")
        st.title("🎙️ AI Suite Voice Assistant")
        st.markdown(
            "Talk to an AI using your voice. Record, transcribe, get answers, and hear them back!")

        self.init_session()

        with st.expander("🎤 Step 1: Record Your Audio", expanded=True):
            self.record_audio()

        if st.session_state.recorded_audio:
            with st.expander("📝 Step 2: Transcribe Audio"):
                self.process_audio()

        if st.session_state.audio_transcription:
            with st.expander("🤖 Step 3: Talk to the Assistant"):
                self.initiate_ai_assistant()

        if st.session_state.model_response:
            with st.expander("🔊 Step 4: Hear the Response"):
                self.say_it_out()

    def init_session(self):
        print("Initializing session state...")
        session_parameters = [
            "recorded_audio",
            "audio_transcription",
            "model_response"
        ]
        for param in session_parameters:
            if param not in st.session_state:
                st.session_state[param] = None

    def record_audio(self):
        print("Recording audio...")
        # Step 1: Record audio
        st.subheader("Step 1: Record Your Audio")

        audio = audiorecorder("🎤 Start Recording", "⏹ Stop Recording")

        if len(audio) > 0:
            st.session_state.recorded_audio = audio

            # To play audio in frontend:
            st.audio(audio.export(format="wav").read(), format="audio/wav")

            # Show diagnostics
            st.write(
                f"⏱ Duration: `{audio.duration_seconds:.2f}` seconds"
            )

            st.success("✅ Audio recorded. Ready to process!")

    def process_audio(self):
        print("Processing audio...")
        audio = st.session_state.get("recorded_audio")

        if audio is None:
            st.warning("⚠️ No audio recorded yet. Please record first.")
        else:
            with st.spinner("Transcribing audio..."):
                # Export to a valid WAV file
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".wav") as temp_file:
                    audio.export(temp_file.name, format="wav")
                    valid_wav_path = temp_file.name

                    result = self.speech_service.speech_to_text(
                        valid_wav_path)
                    st.write("🧠 Transcript:",
                             result.get('text', 'No text recognized'))
                    st.write("⏱ Time Taken:",
                             result.get('processing_time', 'N/A'),
                             "seconds")
                    st.session_state.audio_transcription = result.get('text')

                st.info(f"💾 Valid WAV file saved at:\n`{valid_wav_path}`")

    def _build_prompt(self, user_input):
        system_prompt = TONE_PROFILES.get(self.tone, TONE_PROFILES["friendly"])
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

    def initiate_ai_assistant(self):
        print("Initiating AI assistant...")
        if st.session_state.recorded_audio is None:
            return
        if st.session_state.audio_transcription is None:
            st.warning(
                "⚠️ No transcription available. Please record and process audio first.")
            return

        st.subheader("Step 2: AI Assistant Interaction")
        with st.spinner("Loading AI assistant..."):
            response = self.openai_service.ask(
                messages=self._build_prompt(
                    st.session_state.audio_transcription)
            )

            st.session_state.model_response = response["text"]

            st.write("🧠 Assistant:", response["text"])
            st.write("⏱ Time Taken:", response["time_taken"], "seconds")
            st.write("🔢 Token Usage:", response["tokens"])
            return

    def say_it_out(self):
        print("Speaking out loud...")
        if st.session_state.audio_transcription is None:
            return
        if st.session_state.model_response is None:
            st.warning(
                "⚠️ No AI response available. Please interact with the AI assistant first.")
            return

        response_text = st.session_state.model_response
        with st.spinner("Speaking out loud..."):
            self.speech_service.text_to_speech(response_text)
            st.success("✅ Done speaking!")

if __name__ == "__main__":
    app = VoiceApp()
    app.run()
