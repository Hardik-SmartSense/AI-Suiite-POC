import datetime
import os
import random

import pandas as pd

from services.speech_service import SpeechService
from services.text_eval import evaluate_text


def eval_speech_service(path):
    service = SpeechService()
    final_resp = []
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
                res = service.speech_to_text(audio_path=file)
                final_resp.append(res)

    df = pd.json_normalize(final_resp)
    df.to_csv(f"static/output_{datetime.datetime.now()}.csv", index=False)


def eval_audio_transcriptions(path, csv_name):
    service = SpeechService(play_audio=False)
    df = pd.read_csv(os.path.join(path, csv_name))

    resp = []
    max_sample = input("How many samples to process? Leave blank for all : ")
    if max_sample in (None, ""):
        max_sample = len(df)

    for idx in range(int(max_sample)):
        print("Processing file index:", idx)
        file_row = df.iloc[idx].to_dict()
        res = service.speech_to_text(audio_path=file_row["audio_path"])
        gen_transcript = res.get("text", "")
        og_transcript = file_row["transcript"]
        file_row.update({
            "transcript": og_transcript,
            "gen_transcript": gen_transcript,
            "word_error_rate": evaluate_text(og_transcript, gen_transcript)
        })
        resp.append(file_row)
        print(f"""
        File Name: {file_row["audio_path"]},
        File Transcript: {og_transcript},
        Generated Transcript: {gen_transcript},
        File WER: {file_row["word_error_rate"]}
        """)
        print("-" * 50)

    resp_df = pd.json_normalize(resp)
    resp_df.to_csv(f"static/output_{datetime.datetime.now()}.csv",
                   index=False)

if __name__ == "__main__":
    # eval_speech_service(path="audio_files")
    eval_audio_transcriptions(path="data",
                              csv_name="google_fleurs.csv")
