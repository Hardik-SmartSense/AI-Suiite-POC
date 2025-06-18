import csv
import os

import soundfile as sf
from datasets import load_dataset


# Optional login if using private datasets
# login("hf_your_token")

def generate_audio_csv(dataset_name: str, subset: str, language_code: str,
                       split: str = "train", count: int = 25):
    print(f"📦 Loading {dataset_name}::{language_code} ({split})")
    dataset = load_dataset(dataset_name, language_code, split=split)
    dataset = dataset.shuffle(seed=42).select(range(count))

    output_dir = f"./data/{language_code}"
    os.makedirs(output_dir, exist_ok=True)

    csv_rows = []

    for i, item in enumerate(dataset):
        # Decode and save audio
        audio = item["audio"]
        audio_array = audio["array"]
        sample_rate = audio["sampling_rate"]

        audio_path = os.path.join(output_dir, f"{i+1:03d}.wav")
        sf.write(audio_path, audio_array, sample_rate)

        # Collect transcript
        transcript = item.get("transcription", item.get("sentence", ""))
        csv_rows.append({
            "language_code": language_code,
            "audio_path": audio_path,
            "transcript": transcript
        })
    return csv_rows


def save_to_csv(csv_rows, dataset_name: str):
    # Save to CSV
    csv_path = f"./data/{dataset_name.replace('/', '_')}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["language_code", "audio_path", "transcript"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✅ Generated {csv_path} with {len(csv_rows)} samples.\n")


if __name__ == "__main__":
    csv_rows = []
    for lang in ["en_us", "de_de"]:
        csv_rows += generate_audio_csv(
            dataset_name="google/fleurs",
            subset="google/fleurs",
            language_code=lang,
            split="train",
            count=50
        )
    save_to_csv(csv_rows, dataset_name="google/fleurs")
