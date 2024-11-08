from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient

from dotenv import load_dotenv
import os

load_dotenv()

def text2vec(data: list[str]) -> list[list]:
    pass

def pdf2text(url: str) -> list[dict]:
    pass

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Generation" 

    async def on_startup(self):
        self.milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')

        if 'embeddings' not in self.milvus_client.list_collections():
            self.milvus_client.create_collection('embeddings', 1024)

    async def on_shutdown(self):
        self.milvus_client.close()

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        return 'working'#self.milvus_client.search('embeddings', )
