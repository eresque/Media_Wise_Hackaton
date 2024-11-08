from os import getenv

import requests
from dotenv import load_dotenv

from prompts import PROMPTS

import logging
logging.basicConfig(level=logging.INFO)

LLM_INSTRUCTION = PROMPTS['llm_instructions']
QUESTION = PROMPTS['question']


load_dotenv()

IAM_TOKEN = getenv('IAM_TOKEN')

url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
headers = {
    'Authorization': f'Bearer {IAM_TOKEN}',
    'Content-Type': 'application/json'
}


def llm_response(prompt, context):
        logging.info("GPT GENERATION")

        _question = QUESTION.format(
            context=context,
            prompt= prompt,
        )
        request_data = {
            "modelUri": "gpt://b1gjp5vama10h4due384/yandexgpt-32k/rc",
            "completionOptions": {
                "stream": False,
                "temperature": 0.2,
                "maxTokens": "32000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": f"{LLM_INSTRUCTION}"
                },
                {
                    "role": "user",
                    "text": f"{_question}"
                }
            ]
        }

        response = requests.post(url, headers=headers, json=request_data)

        if response.status_code == 200:
            response_text = response.json()['result']['alternatives'][0]['message']['text']
            logging.info(response_text)

            return response_text

        logging.error(f"Response status code: {response.status_code}")


if __name__ == "__main__":
    logging.info("Test llm response")
    response = llm_response("почему трава зеленая?", "")