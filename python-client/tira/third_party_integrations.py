import os
import json
from tira.io_utils import all_lines_to_pandas
import logging


def ensure_pyterrier_is_loaded(boot_packages=("com.github.terrierteam:terrier-prf:-SNAPSHOT", ), packages=(), patch_ir_datasets=True):
    import pyterrier as pt

    # Detect if we are in the TIRA sandbox
    if patch_ir_datasets:
        try:
            import ir_datasets as original_ir_datasets
            original_ir_datasets.load = load_ir_datasets().load
            logging.info('Due to execution in TIRA, I have patched ir_datasets to always return the single input dataset mounted to the sandbox.')
        except Exception as e:
            logging.error('Could not patch ir_datasets.', exc_info=e)
    else:
        import ir_datasets as original_ir_datasets
        from tira.ir_datasets_util import original_ir_datasets_load
        original_ir_datasets.load = original_ir_datasets_load

    pt_version = os.environ.get('PYTERRIER_VERSION', '5.7')
    pt_helper_version = os.environ.get('PYTERRIER_HELPER_VERSION', '0.0.7')

    if not pt.started():
        logging.info(f'Start PyTerrier with version={pt_version}, helper_version={pt_helper_version}, no_download=True')
        pt.init(version=pt_version, helper_version=pt_helper_version, no_download=True, boot_packages=list(boot_packages), packages=list(packages))


def get_preconfigured_chatnoir_client(config_directory, features=['TARGET_URI'], num_results=10, retries=25, page_size=10):
    from chatnoir_pyterrier import ChatNoirRetrieve
    from chatnoir_api import Index as ChatNoirIndex
    from chatnoir_pyterrier.feature import Feature

    chatnoir_config = json.load(open(config_directory + '/chatnoir-credentials.json'))

    chatnoir = ChatNoirRetrieve(api_key=chatnoir_config['apikey'], staging=chatnoir_config.get('staging', False))
    chatnoir.features = [getattr(Feature, i) for i in features]
    chatnoir.num_results = num_results
    chatnoir.retries = retries
    chatnoir.page_size = page_size
    chatnoir.index = getattr(ChatNoirIndex, chatnoir_config['index'])

    logging.info(f'ChatNoir Client will retrieve the top-{chatnoir.num_results} with page size of {chatnoir.page_size} from index {chatnoir_config["index"]} with {chatnoir.retries} retries.')

    return chatnoir


def get_output_directory(default_output: str = '/tmp/'):
    output_directory = os.environ.get('TIRA_OUTPUT_DIR', default_output)
    logging.info(f'The output directory is {output_directory}')
    return output_directory


def get_input_directory_and_output_directory(default_input, default_output: str = '/tmp/'):
    input_directory = os.environ.get('TIRA_INPUT_DATASET', None)

    if input_directory:
        print(f'I will read the input data from {input_directory}.')
    else:
        input_directory = default_input
        print(f'I will use a small hardcoded example located in {input_directory}.')

    return (input_directory, get_output_directory(default_output))


def is_running_as_inference_server():
    return os.environ.get('TIRA_INFERENCE_SERVER', None) is not None


def load_rerank_data(default, load_default_text=True):
    default_input = get_input_directory_and_output_directory(default)[0]

    if not os.path.isdir(default_input) and len(default.split('/')) == 2:
        from tira.rest_api_client import Client as RestClient
        default_input = RestClient().download_dataset(default.split('/')[0], default.split('/')[1])

    if not default_input.endswith('rerank.jsonl') and not default_input.endswith('rerank.jsonl.gz'):
        if os.path.isfile(default_input + '/rerank.jsonl.gz'):
            default_input = default_input + '/rerank.jsonl.gz'
        elif os.path.isfile(default_input + '/rerank.jsonl'):
            default_input = default_input + '/rerank.jsonl'

    return all_lines_to_pandas(default_input, load_default_text)


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

    register_dataset_from_re_rank_file(ir_dataset_id, default_input, original_ir_datasets_id)


def persist_and_normalize_run(run, system_name, default_output=None, output_file=None, depth=1000):
    if output_file is None and default_output is None:
        print('I use the environment variable "TIRA_OUTPUT_DIR" to determine where I should store the run file using "." as default.')
        output_file = os.environ.get('TIRA_OUTPUT_DIR', '.')

    if default_output is not None:
        if os.environ.get('TIRA_OUTPUT_DIR') is None:
            print(f'The run file is normalized outside the TIRA sandbox, I will store it at "{default_output}".')
            output_file = default_output
        else:
            output_file = os.environ.get('TIRA_OUTPUT_DIR')
            print(f'The run file is normalized inside the TIRA sandbox, I will store it at "{output_file}".')

    if not output_file.endswith('run.txt'):
        output_file = output_file + '/run.txt'
    normalize_run(run, system_name, depth).to_csv(output_file, sep=" ", header=False, index=False)
    print(f'Done. run file is stored under "{output_file}".')


def normalize_run(run, system_name, depth=1000):
    try:
        run['qid'] = run['qid'].astype(int)
    except Exception:
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


def load_ir_datasets():
    # Detect if we are in the TIRA sandbox
    if 'TIRA_INPUT_DATASET' in os.environ:
        from tira.ir_datasets_util import static_ir_dataset

        if os.path.isfile(os.path.join(os.environ['TIRA_INPUT_DATASET'], 'rerank.jsonl.gz')) or os.path.isfile(os.path.join(os.environ['TIRA_INPUT_DATASET'], 'rerank.jsonl')):
            import ir_datasets as original_ir_datasets
            register_rerank_data_to_ir_datasets(os.environ['TIRA_INPUT_DATASET'], 'dynamic-ds-in-tira')

            return static_ir_dataset(os.environ['TIRA_INPUT_DATASET'], original_ir_datasets.load('dynamic-ds-in-tira'))

        return static_ir_dataset(os.environ['TIRA_INPUT_DATASET'])
    else:
        try:
            from tira.ir_datasets_util import ir_dataset_from_tira_fallback_to_original_ir_datasets
            return ir_dataset_from_tira_fallback_to_original_ir_datasets()
        except Exception:
            return None


ir_datasets = load_ir_datasets()
