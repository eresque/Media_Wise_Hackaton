from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient
import pymupdf

from dotenv import load_dotenv

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

def text2vec(text: str) -> list:
    return [1 for _ in range(1024)]

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
        self.milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')

        if not self.milvus_client.has_collection(collection_name='embeddings'):
            self.milvus_client.create_collection('embeddings', 1024, auto_id=True)
        
    async def on_shutdown(self):
        self.milvus_client.close()

    async def inlet(self, body: dict, user: dict) -> dict:
        self.temp_data = body['files']

        paths = []
        files = body.get("files", [])
        for file_data in files:
            file = file_data['file']

            paths.append({
                'name': file['filename'],
                'path': './backend/data/uploads/' + file['filename'],
            })
        body['file_data'] = paths
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        for pdf in body.get('file_data', []):
            for page in pdf2text(pdf['path']):
                vector = text2vec(page['text']) # TODO: IMPLEMENT
                data = {
                    'vector': vector,
                    'text': page['text'],
                    'page_num': page['page_num'],
                    'orig_file': page['path'],
                }

                self.milvus_client.insert(collection_name='embeddings', data=data)
        return 'Knowledge-base updated!'
        
        
