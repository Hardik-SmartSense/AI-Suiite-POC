import datetime
import os
import random

import pandas as pd

from speech_service import SpeechService
from text_eval import evaluate_text


def eval_speech_service():
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


def eval_german_audio_transcriptions(folder="german_dataset",
                                     csv_path="transcript.csv"):
    service = SpeechService(play_audio=False)
    df = pd.read_csv(os.path.join(folder, csv_path))

    resp = []
    max_sample = int(input("How many samples to process? : "))
    for idx in range(max_sample):
        file_row = df.sample(1).to_dict(orient="records")[0]
        res = service.speech_to_text(folder=folder,
                                     file=file_row["loc"])
        res_transcript = res.get("text", "")
        og_transcript = file_row["transcript"]
        file_row["gen_transcript"] = res_transcript
        file_row["word_error_rate"] = evaluate_text(og_transcript, res_transcript)
        resp.append(file_row)

    resp_df = pd.json_normalize(resp)
    resp_df.to_csv(f"static/output_{datetime.datetime.now()}.csv",
                   index=False)

if __name__ == "__main__":
    eval_german_audio_transcriptions()
