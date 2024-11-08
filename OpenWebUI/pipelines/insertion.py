from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient

from dotenv import load_dotenv
from lib import pdf2text, text2vec

load_dotenv()

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Insertion" 

    async def on_startup(self):
        self.milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')

        if 'embeddings' not in self.milvus_client.list_collections():
            self.milvus_client.create_collection('embeddings', 1024)

    async def on_shutdown(self):
        self.milvus_client.close()

    async def inlet(self, body: dict, user: dict) -> dict:
        files = body.get("files", [])
        paths = []
        for file in files:
            content_url = file["url"] + "/content"
            paths.append({
                'name': file['name'],
                'path': content_url,
            })
        body['file_paths'] = paths
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        file_paths = body.get('file_paths', [])
        
