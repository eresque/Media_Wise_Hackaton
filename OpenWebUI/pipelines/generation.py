from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient

from dotenv import load_dotenv
import os

load_dotenv()

def text2vec(data: str) -> list[list]:
    pass

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
        
        self.milvus_client = MilvusClient(uri="http://milvus-standalone:19530", token='root:Milvus')

        if not self.milvus_client.has_collection(collection_name='embeddings'):
            self.milvus_client.create_collection('embeddings', 1024, auto_id=True)
        
        vector = text2vec(user_message)

        res = self.milvus_client.search(
            collection_name='embeddings',
            data=vector,
            limit=10, #TDB
            output_fields=['page_num', 'text', 'orig_file']
        )

        self.milvus_client.close()

        return 'working'
