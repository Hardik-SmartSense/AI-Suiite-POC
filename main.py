import datetime
import os
import random

import pandas as pd

from speech_service import SpeechService


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

def compare_transcriptions(folder_name):
    return

if __name__ == "__main__":
    eval_speech_service()