#!/usr/bin/env python3
import pathlib
import pandas as pd
import argparse
from tira.third_party_integrations import ensure_pyterrier_is_loaded
from tira.tira_client import RestClient
from tqdm import tqdm


def __normalize_queries(q):
    return q.lower().strip()

def load_oracle_index(file_name, allowed_dataset_ids):
    print(f'Load oracle index from {file_name}')
    entries = pd.read_json(file_name, orient='records', lines=True)
    entries = [i.to_dict() for _, i in entries.iterrows() if i['relevance'] > 0]
    ret = {}
    dataset_counts = {i: 0 for i in allowed_dataset_ids}

    for entry in entries:
        if entry['dataset'] not in allowed_dataset_ids:
            continue
        query = __normalize_queries(entry['query'])
        if query not in ret:
            ret[query] = []
        ret[query].append(entry)
        dataset_counts[entry['dataset']] += 1

    print(f'Done. Loaded entries from the oracle {dataset_counts}.')

    return ret

def parse_args():
    parser = argparse.ArgumentParser(description='Construct neighbors')
    parser.add_argument('--input-dataset', type=str, help='Input file', default='cranfield-20230107-training')
    parser.add_argument('--output-dir', type=str, help='Output file', required=True)
    parser.add_argument('--query-document-pairs', type=str, help='Output file', default=str((pathlib.Path(__file__).parent.resolve() / 'oracle-index.jsonl.gz').absolute()), required=False)
    parser.add_argument('--fb-terms', type=list, help='fb_terms passed to pyterrier', nargs='+', default=[10, 20, 30], required=False)
    parser.add_argument('--w-models', type=list, help='weighting models passed to pyterrier', nargs='+', default=['BM25', 'DirichletLM'], required=False)
    parser.add_argument('--oracle-dataset-ids', type=str, help='allowed dataset ids', nargs='+', required=True)
    parser.add_argument('--fb-docs', type=list, help='fb_docs passed to pyterrier', nargs='+', default=[5, 10], required=False)
    parser.add_argument('--first-stage-top-k', type=int, help='top-k documents used for query reformulation', default=900, required=False)
    return parser.parse_args()


def get_overlapping_queries(pt_dataset, oracle_index):
    print('Look for overlapping queries...')
    overlapping_queries = {i.query_id: i.default_text() for i in pt_dataset.irds_ref().queries_iter()}
    overlapping_queries = {k: v for k, v in overlapping_queries.items() if __normalize_queries(v) in oracle_index}

    print(f'Done. Found {len(overlapping_queries)} overlapping queries.')
    return overlapping_queries


def get_overlapping_topics(pt_dataset, overlapping_queries):
    print('Select overlapping topics...')
    topics = pt_dataset.get_topics('text')
    topics = topics[topics['qid'].isin(overlapping_queries.keys())]

    print(f'Done. Found {len(topics)} overlapping topics.')
    return topics


def build_reformulation_index(oracle_index, bm25_raw, topics, pt_dataset):
    additional_docs = {}

    for i in oracle_index:
        for j in oracle_index[i]:
            additional_docs[j['doc_id']] = j['doc']

    additional_docs = [{'docno': 'ADD_' + k, 'text': v} for k, v in additional_docs.items()]
    print(f'Have {len(additional_docs)} documents from the oracle.')

    doc_ids = []

    for _, i in bm25_raw(topics).iterrows():
        if i['qid'] in overlapping_queries:
            doc_ids.append(i['docno'])
    
    doc_ids = set(doc_ids)

    docs_for_reformulation = []

    for i in tqdm(pt_dataset.get_corpus_iter()):
        if i['docno'] not in doc_ids:
            continue
        docs_for_reformulation += [i]
    
    print(f'Have {len(additional_docs)} documents for reformulation.')

    iter_indexer = pt.IterDictIndexer("/tmp/reformulation-index", meta={'docno': 50, 'text': 4096}, overwrite=True)
    return iter_indexer.index(tqdm(docs_for_reformulation + additional_docs, 'Index'))

def get_oracle_retrieval_results(topics, oracle_index, overlapping_queries):
    ret = []

    for _, topic in topics.iterrows():
        r = 0
        for hit in sorted(oracle_index[__normalize_queries(overlapping_queries[topic['qid']])], key=lambda x: x['relevance'], reverse=True):
            r += 1
            ret += [{'qid': topic['qid'], 'query': topic['query'], 'docno': 'ADD_' + hit['doc_id'], 'rank': r, 'score': 100-r, 'run_id': 'oracle'}]

    ret = pd.DataFrame(ret)
    return pt.transformer.get_transformer(ret)

def run_foo(index, reformulation_index, weighting_models, fb_terms, fb_docs, out_dir, oracle_retrieval_results, topics):
    
    for wmodel in weighting_models:
        for fb_term in fb_terms:
            for fb_doc in fb_docs:
                print(f'Run RM3 on {wmodel} {fb_term} {fb_doc}')

                rm3_keyquery_bm25 = oracle_retrieval_results >> pt.rewrite.RM3(reformulation_index, fb_docs=fb_doc, fb_terms=fb_term) >> pt.BatchRetrieve(index, wmodel=wmodel)

                rm3_keyquery_bm25(topics).to_json(f'{out_dir}/rm3_{wmodel}_{fb_term}_{fb_doc}.jsonl.gz', index=False, lines=True, orient='records')

                print(f'Run BO1 on {wmodel} {fb_term} {fb_doc}')

                bo1_keyquery_bm25 = oracle_retrieval_results >> pt.rewrite.Bo1QueryExpansion(reformulation_index, fb_docs=fb_doc, fb_terms=fb_term) >> pt.BatchRetrieve(index, wmodel="BM25")

                bo1_keyquery_bm25(topics).to_json(f'{out_dir}/bo1_{wmodel}_{fb_term}_{fb_doc}.jsonl.gz', index=False, lines=True, orient='records')

                print(f'Run KL on {wmodel} {fb_term} {fb_doc}')

                kl_keyquery_bm25 = oracle_retrieval_results >> pt.rewrite.KLQueryExpansion(reformulation_index, fb_docs=fb_doc, fb_terms=fb_term) >> pt.BatchRetrieve(index, wmodel="BM25")

                kl_keyquery_bm25(topics).to_json(f'{out_dir}/kl_{wmodel}_{fb_term}_{fb_doc}.jsonl.gz', index=False, lines=True, orient='records')

if __name__ == '__main__':
    args = parse_args()
    ensure_pyterrier_is_loaded()
    import pyterrier as pt

    tira = RestClient()

    pt_dataset = pt.get_dataset(f'irds:ir-benchmarks/{args.input_dataset}')
    oracle_index = load_oracle_index(args.query_document_pairs, args.oracle_dataset_ids)
    overlapping_queries = get_overlapping_queries(pt_dataset, oracle_index)
    topics = get_overlapping_topics(pt_dataset, overlapping_queries)
    oracle_retrieval_results = get_oracle_retrieval_results(topics, oracle_index, overlapping_queries)

    bm25_raw = tira.pt.from_submission('ir-benchmarks/tira-ir-starter/BM25 (tira-ir-starter-pyterrier)', args.input_dataset) % args.first_stage_top_k
    index = tira.pt.index('ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)', args.input_dataset)
    reformulation_index = build_reformulation_index(oracle_index, bm25_raw, topics, pt_dataset)

    index = tira.pt.index('ir-benchmarks/tira-ir-starter/Index (tira-ir-starter-pyterrier)', args.input_dataset)

    run_foo(index, reformulation_index, args.w_models, args.fb_terms, args.fb_docs, args.output_dir, oracle_retrieval_results, topics)

