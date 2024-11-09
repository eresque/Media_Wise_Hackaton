from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient, Collection, connections
from pymilvus.client.abstract import SearchResult

from dotenv import load_dotenv
import requests
import json
import pymupdf

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
        latest_message = messages[-1]['content']

        vector = text2vec([latest_message])

        connections.connect(host='milvus-standalone', port='19530', token='root:Milvus')
        collection = Collection('embeddings')

        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}
        }

        collection.load()

        res: SearchResult = collection.search(
            data=vector,
            anns_field='vector',
            param=search_params,
            limit=10,
            output_fields=['id', 'page_num', 'text', 'orig_file']
        )

        documents = []
        metadata = []

        for hits in res:
            for hit in hits:
                documents.append(hit.entity.get('text'))
                metadata.append({
                    'page': hit.entity.get('page_num'),
                    'orig': hit.entity.get('orig_file'),
                    'id': hit.entity.get('id'),
                })

        collection.release()

        rerank_response = requests.post('http://reranker_inference:8081/rerank', json={
            'query': latest_message,
            'documents': documents,
        }).json()

        top_metadata = [metadata[documents.index(doc_data[1])] for doc_data in rerank_response['ranked_documents']]

        top_file_name = top_metadata[0]['orig'].split('/')[-1].split('_')[1].split('.')[0]

        yield f'File: {top_file_name}\nPage: {top_metadata[0]["page"] + 1}\n'

        with requests.post('http://llm_inference:8087/llm-response-streaming', json={
            'prompt': latest_message,
            'context': ' '.join([doc_data[1] for doc_data in rerank_response['ranked_documents']])
            }, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(1024):  # or, for line in r.iter_lines():
                yield json.loads(chunk)['response']