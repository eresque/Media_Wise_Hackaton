from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient, Collection, connections
from pymilvus.client.abstract import SearchResult

from dotenv import load_dotenv
import requests
import json

load_dotenv()

def text2vec(doc: list[str]) -> list:
    return requests.post('http://embedder_inference:8082/embed', json={
        'sentences': doc
    }).json()['embeddings']

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Generation" 

    async def on_startup(self):
        pass

    async def on_shutdown(self):
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        vector = text2vec([user_message])

        connections.connect(host='milvus-standalone', port='19530', token='root:Milvus')
        collection = Collection('embeddings')

        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}  # Size of the dynamic candidate list during search
        }

        collection.load()

        res: SearchResult = collection.search(
            data=vector,
            anns_field='vector',
            param=search_params,
            limit=10, #TDB
            output_fields=['id', 'page_num', 'text', 'orig_file']
        )

        documents = []

        for hits in res:
            for hit in hits:
                documents.append(hit.entity.get('text'))



        collection.release()

        yield json.dumps({
            'query': user_message,
            'documents': documents,
        })

        response = requests.post('http://reranker_inference:8081/rerank', json={
            'query': user_message,
            'documents': documents,
        }).json()

        yield json.dumps(response)



