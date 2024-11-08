from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient

from dotenv import load_dotenv

load_dotenv()

def text2vec(data: list[str]) -> list[list]:
    pass

def pdf2text(url: str) -> list[dict]:
    pass

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
        self.temp_data = body['files']

        paths = []
        files = body.get("files", [])
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

        return self.temp_data[0]['file']['data']['content']

        
