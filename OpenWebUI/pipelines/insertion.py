from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient, Collection, connections
import pymupdf
import sqlite3

from dotenv import load_dotenv

import requests
import json

load_dotenv()

def text2vec(doc: list[str]) -> list:
    return requests.post('http://embedder_inference:8082/embed', json={
        'sentences': doc
    }).json()['embeddings']

def pdf2text(path: str) -> list[dict]:
    result = []

    doc = pymupdf.open(path)

    for page in doc:
        text = page.get_text()
        result.append({
            'page_num': page.number,
            'text': text,
            'path': path,
        })

    return result

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Insertion"

    async def on_startup(self):
        pass
        
    async def on_shutdown(self):
        pass

    async def inlet(self, body: dict, user: dict) -> dict:
        body['file_data'] = body['files']
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        connections.connect(host='milvus-standalone', port='19530', token='root:Milvus')
        collection = Collection('embeddings')

        # milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')
        # if not milvus_client.has_collection(collection_name='embeddings'):
        #     milvus_client.create_collection('embeddings', 1024, auto_id=True)

        conn = sqlite3.connect('./backend/data/vector_db/chroma.sqlite3')
        cursor = conn.cursor()

        for file_data in body.get('file_data'):
            file_id = file_data['id']

            meta_data = []
        
            cursor.execute(f'SELECT id FROM embedding_metadata WHERE "key" = "file_id" and "string_value" = "{file_id}"')
            table_ids = cursor.fetchall()

            for table_id in table_ids:
                page_data = {}

                cursor.execute(f'SELECT * FROM embedding_metadata WHERE "id" = {table_id[0]}')
                tables = cursor.fetchall()

                for table in tables:
                    if table[1] == 'source' or table[1] == 'chroma:document':
                        page_data[table[1]] = table[2]
                    if table[1] == 'page':
                        page_data[table[1]] = table[3]

                meta_data.append(page_data)

            document_content = [page['chroma:document'] for page in meta_data]
            vectors = text2vec(document_content)

            data = [ {
                'vector': vectors[i],
                'text': document_content[i],
                'page_num': meta_data[i]['page'],
                'orig_file': meta_data[i]['source']
            } for i in range(len(vectors))]

            collection.insert(data)
            
        collection.flush()
        res = json.dumps([collection.num_entities])

        return res
