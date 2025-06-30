import os
import tempfile
import time

from openai import AzureOpenAI
from pydub import AudioSegment
from pydub.playback import play


class OpenAIService:
    def __init__(self):
        self.deployment = os.environ["OPENAI_DEPLOYMENT_NAME"]

    def ask(self, messages, temperature=0.5, max_tokens=300):
        print("-" * 100)
        print(f"Asking OpenAI API...: {messages}")
        start_time = time.time()
        client = AzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["OPENAI_BASE_URL"],
            api_version=os.environ["OPENAI_API_VERSION"]
        )
        response = client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {
            "time_taken": round(time.time() - start_time, 2),
            "tokens": response.usage.total_tokens,
            "content": response.choices[0].message.content
        }

    def speak(self, text, voice="nova", instructions=None):
        start_time = time.time()
        client = AzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["OPENAI_BASE_URL"],
            api_version=os.environ["OPENAI_API_VERSION"]
        )
        response = client.audio.speech.create(
            model=os.environ["OPENAI_TTS_MODEL"],
            voice=voice,
            input=text,
            instructions=instructions
        )
        time_taken = round(time.time() - start_time)
        output_path = tempfile.mktemp(suffix=".mp3")
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Audio saved to: {output_path}")
        return output_path, time_taken


if __name__ == "__main__":
    service = OpenAIService()
    audio_path = service.speak(
    """
    [whispers] Cricket is a sport that
    began in England… now played all over the world."""
    )
    print(f"Audio file created at: {audio_path}")
    song = AudioSegment.from_mp3(audio_path)
    play(song)
