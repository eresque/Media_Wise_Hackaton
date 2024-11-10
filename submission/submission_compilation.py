import pandas as pd
import requests

from tqdm import tqdm

from pymilvus import MilvusClient, Collection, connections
from pymilvus.client.abstract import SearchResult

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

tqdm.pandas()

connections.connect(host='localhost', port='19530', token='root:Milvus')
collection = Collection('embeddings')


def text2vec(doc: list[str]) -> list:
    return requests.post('http://localhost:8082/embed', json={
        'sentences': doc
    }).json()['embeddings']


def generate_rag_predictions(row, ):
    import time 
    query = row['question']
    vectorized_query = text2vec([query])

    search_params = {
        "metric_type": "COSINE",
        "params": {"ef": 64}
    }

    collection.load()

    res: SearchResult = collection.search(
        data=vectorized_query,
        anns_field='vector',
        param=search_params,
        limit=30,
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

    rerank_response = requests.post('http://localhost:8081/rerank', json={
        'query': query,
        'documents': documents,
    }).json()

    top_metadata = [metadata[documents.index(doc_data[1])] for doc_data in rerank_response['ranked_documents']]

    file_name_pred = top_metadata[0]['orig'].split('/')[-1].split('_')[1].split('.')[0]

    page_pred = top_metadata[0]["page"] + 1

    llm_response = requests.post('http://localhost:8087/llm-response', json={
        'prompt': query,
        'context': ' '.join([doc_data[1] for doc_data in rerank_response['ranked_documents']])
    }).json()
    time.sleep(0.1)
    print(llm_response)
    llm_response = llm_response['response']
    return llm_response, file_name_pred, page_pred


def main():
    benchmark_df = pd.read_csv("submission/base_submission.csv")
    benchmark_df_sliced = benchmark_df[95:].copy()

    rag_predictions_df = benchmark_df_sliced.progress_apply(generate_rag_predictions, axis=1, )
    rag_predictions_df_lst = rag_predictions_df.tolist()
    answer_pred, filename_pred, slide_number_pred = zip(*rag_predictions_df_lst)

    benchmark_df_sliced['answer'] = answer_pred
    benchmark_df_sliced['filename'] = filename_pred
    benchmark_df_sliced['slide_number'] = slide_number_pred

    benchmark_df_sliced.to_csv("submission/submission_over95.csv", index=False)


if __name__ == "__main__":
    main()
