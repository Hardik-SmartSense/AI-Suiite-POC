import html
import os
import re
import tempfile
import time

import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import AutoDetectSourceLanguageConfig
from pydub import AudioSegment
from pydub.playback import play

import constants


class SpeechService:
    def __init__(self, play_audio=True, method="RECOGNIZE_ONCE"):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_SERVICE_KEY"],
            endpoint=os.environ["AZURE_SPEECH_SERVICE_ENDPOINT"]
        )
        self.languages = ["en-US", "de-DE"]
        self.play_audio = play_audio
        self.method = method.upper()
        self.TONE_PROFILES = constants.CONVERSATION_TONE_CONFIG

    def clean_text(self, text):
        if not text:
            return ""

        # Preserve existing SSML tags before escaping
        preserved_tags = {
            "break": r"<break\s+[^>]*\/?>",
            "emphasis": r"<\/?emphasis\s*[^>]*>"
        }

        # Temporarily replace valid SSML tags with placeholders
        placeholders = {}
        for tag, pattern in preserved_tags.items():
            matches = re.findall(pattern, text)
            for i, match in enumerate(matches):
                key = f"__{tag.upper()}_{i}__"
                placeholders[key] = match
                text = text.replace(match, key)

        # Escape other content
        text = html.escape(text)

        # Reinsert preserved SSML tags
        for key, original_tag in placeholders.items():
            text = text.replace(key, original_tag)

        # Enrich punctuation for better SSML flow
        replacements = {
            r"&colon;": ",",  # Escaped colon
            r"\.\.\.": "<break time='400ms'/>",
            r"--": "<break time='300ms'/>",
            r"\?": "?<break time='200ms'/>",
            r"!": "!<break time='250ms'/>",
            r"\n+": "<break time='500ms'/>",
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        # Normalize spaces
        text = re.sub(r"\s{2,}", " ", text).strip()

        return text

    def text_to_speech(self, text, ssml_config, tone="friendly", lang="en-US"):
        print("-" * 100)
        print("Converting text to speech...")

        config = self.TONE_PROFILES.get(tone, self.TONE_PROFILES["friendly"])[
            lang]

        print(f"Default config: {config}")
        print(f"SSML config: {ssml_config}")

        config.update(ssml_config)
        ssml = f"""
        <speak version='1.0' xml:lang='{lang}'
               xmlns='http://www.w3.org/2001/10/synthesis'
               xmlns:mstts='https://www.w3.org/2001/mstts'>
            <voice name='{config["voice"]}'>
                <prosody rate='{config["rate"]}' pitch='{config["pitch"]}' volume='{config["volume"]}'>
                    <mstts:express-as style='{config["style"]}'>
                        {self.clean_text(text)}
                    </mstts:express-as>
                </prosody>
            </voice>
        </speak>
        """
        print("SSML:", ssml)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            output_path = f.name
        audio_config = speechsdk.audio.AudioOutputConfig(
            use_default_speaker=True, filename=output_path)

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config)

        start = time.time()
        result = synthesizer.speak_ssml_async(ssml).get()
        time_taken = round(time.time() - start, 2)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Speech synthesized successfully.")
            return output_path, time_taken
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print("❌ Speech synthesis canceled:", cancellation.reason)
        return None, time_taken

    def speech_to_text(self, audio_path):
        print("-" * 100)
        print("Converting speech to text...")

        audio_cfg = speechsdk.audio.AudioConfig(filename=audio_path)

        resp = {
            "name": audio_path,
            "status": "NOT_PROCESSED",
            "processing_time": 0.0,
            "method_used": "RECOGNIZE_ONCE",
            "text": "",
            "language": "en-US",
        }

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_cfg,
            auto_detect_source_language_config=AutoDetectSourceLanguageConfig(
                languages=self.languages)
        )

        start = time.time()
        if self.method == "RECOGNIZE_ONCE":
            resp.update(self._recognize_once(recognizer))
            resp["method_used"] = "RECOGNIZE_ONCE"
        else:
            resp.update(self._continue_recognition(recognizer))
            resp["method_used"] = "CONTINUOUS_RECOGNITION"
        resp["processing_time"] = round(time.time() - start, 2)

        if self.play_audio:
            print("Playing audio file: {}".format(audio_path))
            song = AudioSegment.from_wav(audio_path)
            while True:
                play(song)
                accurate = input("Is) it accurate? (1/0): ")
                if accurate in ("0", "1"):
                    break

        """
        while True:
            action = input(
                "Choose action - (1) Recognize Once, (2) Continue "
                "Recognition, (q) Exit: ")
            if action == "q":
                break
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_cfg
            )
            start = time.time()
            if action == "1":
                resp.update(self._recognize_once(recognizer))
                resp["method_used"] = "RECOGNIZE_ONCE"
            else:
                resp.update(self._continue_recognition(recognizer))
                resp["method_used"] = "CONTINUOUS_RECOGNITION"
            resp["processing_time"] = time.time() - start
            while True:
                play(song)
                accurate = input("Is) it accurate? (1/0): ")
                if accurate in ("0", "1"):
                    break
        """
        return resp

    def _recognize_once(self, speech_recognizer):

        speech_recognition_result = speech_recognizer.recognize_once()
        resp = {}

        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(speech_recognition_result.text))
            resp.update({
                "status": "Completed",
                "text": speech_recognition_result.text,
                "language": speech_recognition_result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                )
            })
        elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(
                speech_recognition_result.no_match_details))
            resp["status"] = "NoSpeech"
        elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_recognition_result.cancellation_details
            print("Speech Recognition canceled: {}".format(
                cancellation_details.reason))
            resp["status"] = "Canceled"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                resp["status"] = "Error"
                print("Error details: {}".format(
                    cancellation_details.error_details))
                print(
                    "Did you set the speech resource key and endpoint values?")

        return resp

    def _continue_recognition(self, recognizer):
        transcripts = []

        def recognized_handler(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"📝 Recognized: {evt.result.text}")
                transcripts.append(evt.result.text)

        def stop_handler(evt):
            print("⏹ Session ended.")

        recognizer.recognized.connect(recognized_handler)
        recognizer.session_stopped.connect(stop_handler)
        recognizer.canceled.connect(stop_handler)

        recognizer.start_continuous_recognition()

        done = False

        def stop_cb(evt):
            nonlocal done
            done = True

        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        # Wait until recognition is done
        while not done:
            time.sleep(0.5)

        recognizer.stop_continuous_recognition()

        full_text = " ".join(transcripts)

        return {
            "status": "COMPLETED" if transcripts else "NO_SPEECH",
            "text": full_text,
        }
