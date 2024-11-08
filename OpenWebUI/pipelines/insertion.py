from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
from pymilvus import MilvusClient
import logging

logging.basicConfig(level=logging.INFO)

client = MilvusClient(
    uri="http://milvus-standalone:19530",
    token="root:Milvus",
    db_name='default'
)

client.create_collection(
    collection_name="quick_setup",
    dimension=5
)

class Pipeline:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.name = "Insertion"

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        
        return client.get_load_state(collection_name="quick_setup")
