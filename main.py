import tempfile

import streamlit as st
from audiorecorder import audiorecorder


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

    def run(self):
        st.title("🎙️ AI Suite Voice Assistant")

        self.init_session()
        self.record_audio()
        self.process_audio()
        self.initiate_ai_assistant()
        self.say_it_out()

        if st.button("🔁"):
            if st.session_state.audio_transcription is None:
                st.warning(
                    "⚠️ No transcription available. Please record and process audio first.")
            else:
                self.say_it_out()

    def init_session(self):
        session_parameters = [
            "recorded_audio",
            "audio_transcription",
            "model_response"
        ]
        for param in session_parameters:
            if param not in st.session_state:
                st.session_state[param] = None

    def record_audio(self):
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

    def initiate_ai_assistant(self):
        if st.session_state.recorded_audio is None:
            return
        if st.session_state.audio_transcription is None:
            st.warning(
                "⚠️ No transcription available. Please record and process audio first.")
            return

        st.subheader("Step 2: AI Assistant Interaction")
        with st.spinner("Loading AI assistant..."):
            response = self.openai_service.ask(
                user_prompt=st.session_state.audio_transcription)

            st.session_state.model_response = response["text"]

            st.write("🧠 Assistant:", response["text"])
            st.write("⏱ Time Taken:", response["time_taken"], "seconds")
            st.write("🔢 Token Usage:", response["tokens"])
            return

    def say_it_out(self):
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
