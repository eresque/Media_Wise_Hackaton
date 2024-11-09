from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient
import pymupdf
import sqlite3

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
        body['file_data'] = body['files']
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        conn = sqlite3.connect('./backend/data/vector_db/chroma.sqlite3')
        cursor = conn.cursor()

        for file_data in body.get('file_data'):
            file_id = file_data['id']
        
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

                data = {
                    # 'vector': vector,
                    'text': page_data['chroma:document'],
                    'page_num': page_data['page'],
                    'orig_file': page_data['source'],
                }

                self.milvus_client.insert('embeddings', data=data)