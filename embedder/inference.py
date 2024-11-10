from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import asyncio

import os

os.environ['HF_HOME'] = '/models'

model = SentenceTransformer('deepvk/USER-bge-m3')

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])


class SentenceRequest(BaseModel):
    sentences: list[str]


@app.post("/embed")
async def embed_sentences(request: SentenceRequest) -> dict:
    embeddings = await asyncio.to_thread(model.encode, request.sentences)
    return {"embeddings": embeddings.tolist()}
