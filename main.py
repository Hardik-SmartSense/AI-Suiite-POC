import copy
import json
import random
import tempfile
import time
from datetime import datetime

import streamlit as st
from audiorecorder import audiorecorder
from pydub import AudioSegment
from pydub.playback import play

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
        self.AZURE_SYSTEM_PROMPT_BASE = constants.AZURE_SYSTEM_PROMPT_BASE
        self.OPENAI_SYSTEM_PROMPT_BASE = constants.OPENAI_SYSTEM_PROMPT_BASE
        self.speech = get_speech_service()
        self.openai = get_openai_service()
        self.tone_profiles = constants.CONVERSATION_TONE_CONFIG

        self.init_session_state()
        self.render_settings_panel()

    def init_session_state(self):
        default_key_paris = {
            "audio_unchanged": False,
            "language": "en-US",
            "selected_tone": "friendly",
            "selected_voice_tone": "friendly",
            "recorded_audio": None,
            "transcript": None,
            "ssml_config": {},
            "response": None,
            "transcription_time": None,
            "prompt_result_time": None,
            "prompt_tokens": None,
            "conversation_history": [],
            "tts_service": None,
        }
        for key, value in default_key_paris.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def render_settings_panel(self):
        st.sidebar.title("⚙️ Voice Assistant Settings")

        with st.sidebar.expander("🔧 TTS Settings", expanded=True):
            st.session_state.tts_service = st.selectbox(
                "Select Voice Service for TTS:",
                options=["Azure", "OpenAI"],
                index=1,
                key="tts_service_setting"
            )

            if st.session_state.tts_service == "OpenAI":
                voice_options = ["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]
                st.session_state.openai_voice_option = st.selectbox(
                    "Select Voice Service for TTS:",
                    options=voice_options,
                    index=random.randint(0, len(voice_options)-1),
                    key="openai_voice_options"
                )

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
        st.session_state.audio_unchanged = (audio == st.session_state.recorded_audio)
        if len(audio) > 0:
            st.session_state.recorded_audio = audio
            st.audio(audio.export(format="wav").read(), format="audio/wav")
            if not st.session_state.audio_unchanged:
                st.toast("✅ Audio recorded!")
            return True
        return False

    def transcribe_audio(self):
        audio = st.session_state.get("recorded_audio")
        if not audio:
            return False

        if st.session_state.audio_unchanged is False:
            with st.spinner("Transcribing..."):
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".wav") as f:
                    audio.export(f.name, format="wav")
                    wav_path = f.name

                result = self.speech.speech_to_text(wav_path)
                st.session_state.transcript = result.get("text")
                st.session_state.transcription_time = result.get(
                    "processing_time")

                st.session_state.language = result.get("language", "en-US")

                st.toast(
                    f"🧠 Transcription Done ({result.get('processing_time')}s)")
        else:
            print("Cached Transcript found, skipping AI call.")

        if st.session_state.transcript:
            st.write("Transcript:", st.session_state.transcript)
            return True
        return False

    def _gen_system_prompt(self):
        if st.session_state.tts_service == "OpenAI":
            system_prompt = self.OPENAI_SYSTEM_PROMPT_BASE
        else:
            system_prompt = self.AZURE_SYSTEM_PROMPT_BASE
        system_role = self.tone_profiles[st.session_state.selected_tone][
            st.session_state.language]["prompt"]

        chat_history = ""
        for history in st.session_state.get("conversation_history", [])[:3]:
            chat_history = f"""
            User's question: {history.get("transcript", "N/A")}
            Assistant's Answer: {history.get("response", "N/A")}
            SSML config: {history.get("ssml_config", {})}
            """ + chat_history

        chat_history = chat_history if chat_history else "N/A"

        system_prompt = system_prompt.format(
            role=system_role,
            chat_history=chat_history,
            language=st.session_state.language
        )
        print(f"system_prompt : {system_prompt}")
        return system_prompt

    def get_response(self):
        ssml_config = None
        transcript = st.session_state.get("transcript")
        if not transcript:
            return False

        if st.session_state.audio_unchanged:
            print("Cached response found, skipping AI call.")
            st.write("🧠 Response:", st.session_state.response)
            return True

        tone = st.session_state.selected_tone
        system_prompt = self._gen_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ]

        with st.spinner("Contacting Assistant..."):
            result = self.openai.ask(messages=messages)
        print(f"OpenAI response: {result}")

        result_json = json.loads(result["content"])

        if st.session_state.tts_service == "OpenAI":
            result_text = result_json.get("response")
            ssml_config = result_json.get("instructions", "")

            st.session_state.response = result_text
            st.session_state.ssml_config = ssml_config
        else:
            result_text = result_json.get("text")
            ssml_config = result_json.get("ssml_config", {})

            st.session_state.response = result_text
            st.session_state.ssml_config = ssml_config

        st.session_state.update({
            "prompt_tone": tone,
            "prompt_result_time": result["time_taken"],
            "prompt_tokens": result["tokens"]
        })

        st.toast("🎉 Assistant Response Received")
        st.write("🧠 Response:", st.session_state.response)
        return ssml_config

    def speak_response(self, ssml_config):
        response = st.session_state.get("response")
        if not response:
            return

        if st.session_state.audio_unchanged:
            print("Cached TTS response found, skipping TTS call.")
            st.audio(st.session_state.output_path, format="audio/mp3")
            return

        tone = st.session_state.selected_voice_tone
        with st.spinner("Speaking..."):
            if st.session_state.tts_service == "OpenAI":
                start_time = time.time()
                output_path = self.openai.speak(
                    text=response,
                    voice=st.session_state.openai_voice_option,
                    instructions=ssml_config
                )
                song = AudioSegment.from_mp3(output_path)
                st.session_state.output_path = output_path
                st.session_state.speech_time = round(time.time() -
                                                     start_time, 2)
            else:
                output_path, time_taken = self.speech.text_to_speech(
                    text=response,
                    ssml_config=ssml_config,
                    tone=tone,
                    lang=st.session_state.language
                )
                song = AudioSegment.from_wav(output_path)
                st.session_state.output_path = output_path
                st.session_state.speech_time = time_taken

            play(song)

        st.audio(output_path, format="audio/mp3")
        st.toast(f"✅ Generating Report!")

    def render_report(self):
        with st.expander("📋 Final Interaction Report", expanded=False):
            st.markdown(f"""
            #### 🔊 Audio Summary
            - **Language Detected:** `{st.session_state.get('language', 'N/A')}`
            - **Transcription Time:** `{st.session_state.get('transcription_time', 'N/A')} sec`

            #### 💬 AI Model Summary
            - **Tone Selected:** `{st.session_state.get('selected_tone', 'N/A')}`
            - **Response Time:** `{st.session_state.get('prompt_result_time', 'N/A')} sec`
            - **Tokens Used:** `{st.session_state.get('prompt_tokens', 'N/A')}`

            ### 🎙 Voice Settings
            - **Voice Tone for TTS:** `{st.session_state.get('selected_voice_tone', 'N/A')}`
            - **SSML Config:** `{st.session_state.get('ssml_config', {})}`
            - **Speech Time:** `{st.session_state.get('speech_time', 'N/A')} sec`
            """)

    def append_conversation_history(self, convo_timestamp):
        convo_log = copy.deepcopy(st.session_state.to_dict())
        convo_log["timestamp"] = convo_timestamp
        st.session_state.conversation_history = [convo_log] + st.session_state.conversation_history
        print("Added.")

    def render_history(self):
        if st.session_state.conversation_history:
            with st.expander("🗂️ Chat History", expanded=False):
                for history in st.session_state.conversation_history:
                    st.markdown(
                        f"### 🗓️ Interaction on {history.get('timestamp', 'N/A')}")
                    if history.get('recorded_audio'):
                        st.audio(history.get('recorded_audio').export(
                            format="wav").read(), format="audio/wav")
                    st.markdown(f"""
                        - **Language Detected:** `{history.get('language', 'N/A')}`
                        - **Transcription Time:** `{history.get('transcription_time', 'N/A')} sec`

                        #### 💬 AI Model Summary
                        - **Response:** {history.get("response", "N/A")} 
                        - **Tone Selected:** `{history.get('selected_tone', 'N/A')}`
                        - **Response Time:** `{history.get('prompt_result_time', 'N/A')} sec`
                        - **Tokens Used:** `{history.get('prompt_tokens', 'N/A')}`

                        ### 🎙 Voice Settings
                        - **Voice Tone for TTS:** `{history.get('selected_voice_tone', 'N/A')}`
                        - **SSML Config:** `{st.session_state.get('ssml_config', {})}`
                        - **Speech Time:** `{history.get('speech_time', 'N/A')} sec`
                    """)
                    if history.get('output_path'):
                        st.audio(history.get('output_path', None),
                                 format="audio/mp3")
                    st.markdown("---")

    def run(self):
        st.set_page_config(page_title="AI Voice Assistant", layout="centered")
        st.title("🎙️ AI Suite Voice Assistant")
        st.markdown(
            "Talk to an AI using your voice. Record, transcribe, choose tone, and get spoken responses!")

        # st.subheader("📝 Enter your message")
        # user_input = st.text_area("Type your message here:", key="text_input")
        #
        # if user_input:
        #     st.session_state.transcript = user_input
        #     convo_timestamp = datetime.now()
        #     if ssml_config := self.get_response():
        #         self.speak_response(ssml_config)
        #         self.render_report()
        #         self.append_conversation_history(convo_timestamp)

        with st.expander("🎤 Record Audio", expanded=True):
            if self.record_audio():
                convo_timestamp = datetime.now()
                if self.transcribe_audio():
                    if ssml_config := self.get_response():
                        self.speak_response(ssml_config)
                        self.render_report()
                        self.append_conversation_history(convo_timestamp)

        self.render_history()

# ---------------------------------------
# Main
# ---------------------------------------
if __name__ == "__main__":
    print("Initializing AI Voice Assistant...")
    app = VoiceAgentApp()
    app.run()
