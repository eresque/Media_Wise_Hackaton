from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient, Collection, connections
from pymilvus.client.abstract import SearchResult

from dotenv import load_dotenv
import requests
import json

import pymupdf
import datetime

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
        milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')
        if not milvus_client.has_collection(collection_name='embeddings'):
            milvus_client.create_collection('embeddings', 1024, auto_id=True)
        milvus_client.close()

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
        top_file_name = top_metadata[0]['orig'].split('/')[-1].split('_')[-1].split('.')[0]

        pdf_file = pymupdf.open(top_metadata[0]['orig'])
        pdf_file.select([top_metadata[0]['page'], top_metadata[0]['page'] + 1])
        
        generated_path_dir = '/app/backend/data/'
        generated_filename = body['user']['id'] + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + ".pdf"

        pdf_file.save(generated_path_dir + generated_filename)

        yield f'[http://pdf_retriever:8450/getFile?filename={generated_filename}](Исходные данные)'

        prev_response = ''
        with requests.post('http://llm_inference:8087/llm-response-streaming', json={
            'prompt': latest_message,
            'context': ' '.join([doc_data[1] for doc_data in rerank_response['ranked_documents']])
        }, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=None):
                resp = json.loads(chunk)['response']
                yield resp.replace(prev_response, '')
                prev_response = resp

        