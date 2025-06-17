import datetime
import os
import random
import time

import azure.cognitiveservices.speech as speechsdk
import pandas as pd
from pydub import AudioSegment
from pydub.playback import play


class SpeechService:
    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.environ["AZURE_SPEECH_SERVICE_KEY"],
            endpoint=os.environ["AZURE_SPEECH_SERVICE_ENDPOINT"]
        )

    def speech_to_text(self, folder, file):
        audio_path = os.path.join(folder, file)
        audio_cfg = speechsdk.audio.AudioConfig(filename=audio_path)

        resp = {
            "name": file,
            "path": folder,
            "status": "NOT_PROCESSED",
            "processing_time": 0.0,
            "method_used": "RECOGNIZE_ONCE",
            "text": "",
        }

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_cfg
        )

        start = time.time()
        resp.update(self._continue_recognition(recognizer))
        resp["method_used"] = "CONTINUOUS_RECOGNITION"
        resp["processing_time"] = time.time() - start

        print("Playing audio file: {}".format(file))
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


if __name__ == "__main__":
    service = SpeechService()
    final_resp = []
    path = "audio_files"
    for sub_folder in os.listdir(path):
        item_path = os.path.join(path, sub_folder)
        if os.path.isdir(item_path):
            print("-" * 100)
            print(f"Visiting : {sub_folder}...")
            print("-" * 50)

            idx = 0
            max_sample = int(input("How many samples to process? : "))
            while idx < max_sample:
                file = random.choice(os.listdir(item_path))
                if not file.endswith(".wav"):
                    continue
                print(f"{idx + 1}. {file}")
                idx += 1
                res = service.speech_to_text(folder=item_path, file=file)
                final_resp.append(res)

    df = pd.json_normalize(final_resp)
    df.to_csv(f"static/output_{datetime.datetime.now()}.csv", index=False)
