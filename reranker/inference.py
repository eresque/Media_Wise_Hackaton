from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import CrossEncoder
import asyncio
import os

os.environ['HF_HOME'] = '/models'

app = FastAPI()
app.add_middleware( CORSMiddleware, allow_origins=['*'] )

RERANKER_MODEL = CrossEncoder('DiTy/cross-encoder-russian-msmarco', max_length=512, device='cuda')


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_k: int = 3


def rerank_documents(query: str, documents: list, top_k: int = 3):
    pairs = [[query, doc] for doc in documents]
    scores = RERANKER_MODEL.predict(pairs)
    scored_documents = list(zip(scores.tolist(), documents))
    ranked_documents = sorted(scored_documents, key=lambda x: x[0], reverse=True)
    top_k = min(top_k, len(ranked_documents))
    top_results = ranked_documents[:top_k]

    return top_results


async def async_rerank_documents(query, documents, top_k):
    return await asyncio.to_thread(rerank_documents, query, documents, top_k)


@app.post("/rerank/")
async def rerank(request: RerankRequest):
    top_results = await async_rerank_documents(request.query, request.documents, request.top_k)
    return {"ranked_documents": top_results}
