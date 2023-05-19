import os
import json
import gzip


def ensure_pyterrier_is_loaded(boot_packages=("com.github.terrierteam:terrier-prf:-SNAPSHOT"), packages=()):
    import pyterrier as pt
    
    if 'PYTERRIER_VERSION' not in os.environ or 'PYTERRIER_HELPER_VERSION' not in os.environ:
        raise ValueError(f'I expect to find the environment variables PYTERRIER_VERSION and PYTERRIER_HELPER_VERSION. Current environment variables: {os.environ}')
    
    pt_version = os.environ['PYTERRIER_VERSION']
    pt_helper_version = os.environ['PYTERRIER_HELPER_VERSION']
    
    if not pt.started():
        print(f'Start PyTerrier with version={pt_version}, helper_version={pt_helper_version}, no_download=True')
        pt.init(version=pt_version, helper_version=pt_helper_version, no_download=True, boot_packages=list(boot_packages), packages=list(packages))


def get_preconfigured_chatnoir_client(config_directory, features=['TARGET_URI'], verbose=True, num_results=10, retries=25, page_size=10):
    from chatnoir_pyterrier import ChatNoirRetrieve
    from chatnoir_api import Index as ChatNoirIndex
    from chatnoir_pyterrier.feature import Feature

    chatnoir_config = json.load(open(config_directory + '/chatnoir-credentials.json'))

    chatnoir = ChatNoirRetrieve(api_key=chatnoir_config['apikey'], staging=chatnoir_config.get('staging', False))
    chatnoir.features = [getattr(Feature, i) for i in features]
    chatnoir.verbose = verbose
    chatnoir.num_results = num_results
    chatnoir.retries = retries
    chatnoir.page_size = page_size
    chatnoir.index = getattr(ChatNoirIndex, chatnoir_config['index'])
    
    print(f'ChatNoir Client will retrieve the top-{chatnoir.num_results} with page size of {chatnoir.page_size} from index {chatnoir_config["index"]} with {chatnoir.retries} retries.')
    
    return chatnoir


def get_input_directory_and_output_directory(default_input, default_output: str = '/tmp/'):
    input_directory = os.environ.get('TIRA_INPUT_DIRECTORY', None)

    if input_directory:
        print(f'I will read the input data from {input_directory}.')
    else:
        input_directory = default_input
        print(f'I will use a small hardcoded example located in {input_directory}.')

    output_directory = os.environ.get('TIRA_OUTPUT_DIRECTORY', default_output)
    print(f'The output directory is {output_directory}')
    
    return (input_directory, output_directory)


def is_running_as_inference_server():
    return os.environ.get('TIRA_INFERENCE_SERVER', None) is not None


def all_lines_to_pandas(input_file, load_default_text):
    import pandas as pd
    ret = []
    
    for l in input_file:
        l = json.loads(l)
        if load_default_text:
            del l['original_query']
            del l['original_document']
        l['qid'] = str(l['qid'])
        l['docno'] = str(l['docno'])
        ret += [l]
    
    return pd.DataFrame(ret)
    
                
def load_rerank_data(default_input, load_default_text=True):
    default_input = get_input_directory_and_output_directory(default_input)[0]

    if not default_input.endswith('rerank.jsonl') and not default_input.endswith('rerank.jsonl.gz'):
        if os.path.isfile(default_input + '/rerank.jsonl.gz'):
            default_input = default_input + '/rerank.jsonl.gz'
        elif os.path.isfile(default_input + '/rerank.jsonl'):
            default_input = default_input + '/rerank.jsonl'
    
    ret = []

    if default_input.endswith('.gz'):
        with gzip.open(default_input, 'rt', encoding='utf-8') as input_file:
            return all_lines_to_pandas(input_file, load_default_text)
    else:
        with open(default_input, 'r') as input_file:
            return all_lines_to_pandas(input_file, load_default_text)


def register_rerank_data_to_ir_datasets(path_to_rerank_file, ir_dataset_id, original_ir_datasets_id=None):
    """
    Load a dynamic ir_datasets integration from a given re_rank_file.
    The dataset will be registered for the id ir_dataset_id.
    The original_ir_datasets_id is used to infer the class of documents, qrels, and queries.
    """
    from tira.ir_datasets_util import register_dataset_from_re_rank_file
    default_input = get_input_directory_and_output_directory(path_to_rerank_file)[0]

    if not default_input.endswith('rerank.jsonl') and not default_input.endswith('rerank.jsonl.gz'):
        if os.path.isfile(default_input + '/rerank.jsonl.gz'):
            default_input = default_input + '/rerank.jsonl.gz'
        elif os.path.isfile(default_input + '/rerank.jsonl'):
            default_input = default_input + '/rerank.jsonl'

    if default_input.endswith('.gz'):
        with gzip.open(default_input, 'rt', encoding='utf-8') as input_file:
            df_re_rank = all_lines_to_pandas(input_file, False)
    else:
        with open(default_input, 'r') as input_file:
            df_re_rank = all_lines_to_pandas(input_file, False)

    register_dataset_from_re_rank_file(ir_dataset_id, df_re_rank, original_ir_datasets_id)


def persist_and_normalize_run(run, system_name, output_file, depth=1000):
    if not output_file.endswith('run.txt'):
        output_file = output_file + '/run.txt'
    normalize_run(run, system_name, depth).to_csv(output_file, sep=" ", header=False, index=False)


def normalize_run(run, system_name, depth=1000):
    try:
        run['qid'] = run['qid'].astype(int)
    except:
        pass

    run['system'] = system_name
    run = run.copy().sort_values(["qid", "score", "docno"], ascending=[True, False, False]).reset_index()

    if 'Q0' not in run.columns:
        run['Q0'] = 0

    run = run.groupby("qid")[["qid", "Q0", "docno", "score", "system"]].head(depth)

    # Make sure that rank position starts by 1
    run["rank"] = 1
    run["rank"] = run.groupby("qid")["rank"].cumsum()
    
    return run[['qid', 'Q0', 'docno', 'rank', 'score', 'system']]

