from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import asyncio

model = SentenceTransformer('deepvk/USER-bge-m3')

app = FastAPI()


class SentenceRequest(BaseModel):
    sentences: list[str]


@app.post("/embed")
async def embed_sentences(request: SentenceRequest):
    embeddings = await asyncio.to_thread(model.encode, request.sentences)
    return {"embeddings": embeddings.tolist()}
