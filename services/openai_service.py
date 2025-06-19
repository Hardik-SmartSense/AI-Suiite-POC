import os
import time

from openai import AzureOpenAI


class OpenAIService:
    def __init__(self):
        self.deployment = os.environ["OPENAI_DEPLOYMENT_NAME"]
        self.client = AzureOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            azure_endpoint=os.environ["OPENAI_BASE_URL"],
            api_version=os.environ["OPENAI_API_VERSION"]
        )

    def ask(self, messages, temperature=0.5, max_tokens=300):
        print("-" * 100)
        print("Asking OpenAI API...")
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {
            "time_taken": round(time.time() - start_time, 2),
            "tokens": response.usage.total_tokens,
            "text": response.choices[0].message.content
        }
