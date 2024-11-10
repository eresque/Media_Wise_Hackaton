import pandas as pd
import requests

from tqdm import tqdm

from pymilvus import MilvusClient, Collection, connections
from pymilvus.client.abstract import SearchResult

from rouge_score import rouge_scorer

import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize

nltk.download('punkt_tab')


import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

N_RECORDS = 30

def calculate_rouge(pred, ref):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(pred, ref)
    return scores


def calculate_bleu(row):
    ref = row['answer']
    pred = row['answer_pred']
    reference = [word_tokenize(ref.lower())]
    candidate = word_tokenize(pred.lower())
    return sentence_bleu(reference, candidate)


tqdm.pandas()

connections.connect(host='localhost', port='19530', token='root:Milvus')
collection = Collection('embeddings')


def text2vec(doc: list[str]) -> list:
    return requests.post('http://localhost:8082/embed', json={
        'sentences': doc
    }).json()['embeddings']


def generate_rag_predictions(row, ):
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
    llm_response = llm_response['response']
    return llm_response, file_name_pred, page_pred


def main():
    benchmark_df = pd.read_csv("data/benchmarking_dataset.csv")[:N_RECORDS]
    rag_predictions_df = benchmark_df.progress_apply(generate_rag_predictions, axis=1, )
    rag_predictions_df_lst = rag_predictions_df.tolist()
    answer_pred, filename_pred, slide_number_pred = zip(*rag_predictions_df_lst)

    benchmark_df['answer_pred'] = answer_pred
    benchmark_df['filename_pred'] = filename_pred
    benchmark_df['slide_number_pred'] = slide_number_pred

    benchmark_df['file_prediction_correctness'] = benchmark_df['filename_pred'].astype(str) == benchmark_df['filename'].astype(str)
    benchmark_df['page_prediction_correctness'] = benchmark_df['slide_number'].astype(str) == benchmark_df['slide_number_pred'].astype(str)

    benchmark_df.to_csv("./data/benchmark_pre_calc_metrics.csv", index=False)
    # benchmark_df = pd.read_csv("./data/benchmark_pre_calc_metrics.csv")

    benchmark_df['blue'] = benchmark_df.apply(calculate_bleu, axis=1)

    logging.info(f"File prediction accuracy: {benchmark_df['file_prediction_correctness'].mean()}")
    logging.info(f"Page prediction accuracy: {benchmark_df['page_prediction_correctness'].mean()}")

    logging.info(f"Mean BLUE score: {benchmark_df['blue'].mean()}")

    benchmark_df.to_csv("./data/benchmarking_results.csv", index=False)


if __name__ == "__main__":
    main()
