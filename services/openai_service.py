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

    def ask(self, user_prompt, temperature=0.5, max_tokens=300):
        system_prompt = "You are an intelligent AI assistant. Respond clearly and concisely to user questions."

        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return {
            "time_taken": round(time.time() - start_time, 2),
            "tokens": response.usage.total_tokens,
            "text": response.choices[0].message.content
        }
