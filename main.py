import tempfile

import streamlit as st
from audiorecorder import audiorecorder

from services.speech_service import SpeechService


@st.cache_resource
def get_speech_service():
    """Initialize and return the speech service."""
    return SpeechService(play_audio=False)


class VoiceApp:
    def __init__(self):
        self.speech_service = get_speech_service()

    def run(self):
        st.title("🎙️ Two-Step Audio Recorder")

        self.init_session()
        self.record_audio()
        self.process_audio()

    def init_session(self):
        # Session state to persist audio between button clicks
        if "recorded_audio" not in st.session_state:
            st.session_state.recorded_audio = None

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
                    st.write(
                        f"Speech to Text Result: "
                        f"{result.get('text', 'No text recognized')}, "
                        f"Processing Time: {result.get('processing_time', 'N/A')} seconds"
                    )

                st.info(f"💾 Valid WAV file saved at:\n`{valid_wav_path}`")


if __name__ == "__main__":
    app = VoiceApp()
    app.run()
