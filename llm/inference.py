from os import getenv
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from dotenv import load_dotenv

from prompts import PROMPTS

import logging

import requests

import json

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.add_middleware( CORSMiddleware, allow_origins=['*'] )


LLM_INSTRUCTION = PROMPTS['llm_instructions']
QUESTION = PROMPTS['question']

load_dotenv()

IAM_TOKEN = getenv('IAM_TOKEN')

url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
headers = {
    'Authorization': f'Bearer {IAM_TOKEN}',
    'Content-Type': 'application/json'
}


class Query(BaseModel):
    prompt: str
    context: Optional[str] = ""

@app.post('/llm-response-streaming')
async def llm_response_streaming(query: Query):
    def streamer():
        _question = QUESTION.format(
            context=query.context,
            prompt=query.prompt,
        )

        request_data = {
            "modelUri": "gpt://b1gjp5vama10h4due384/yandexgpt-32k/rc",
            "completionOptions": {
                "stream": True,
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

        with requests.post(url, headers=headers, json=request_data, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(1024):
                response_text = json.loads(chunk)['result']['alternatives'][0]['message']['text']
                yield json.dumps({"response": response_text}).encode()

    return StreamingResponse(streamer())


@app.post("/llm-response")
async def llm_response(query: Query):
    logging.info("GPT GENERATION")

    _question = QUESTION.format(
        context=query.context,
        prompt=query.prompt,
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

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=request_data)
            response.raise_for_status()

            if response.status_code == 200:
                response_text = response.json()['result']['alternatives'][0]['message']['text']
                logging.info(response_text)
                return {"response": response_text}

        except httpx.HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            raise HTTPException(status_code=500, detail="Error communicating with LLM service")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    return {"message": "LLM Service is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8087)
