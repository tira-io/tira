import pandas as pd
from glob import glob
import gzip
import json
import os
from typing import Any, Iterable, Dict, Union


def parse_jsonl_line(input: Union[str, bytearray, bytes], load_default_text: bool) -> Dict:

    """
    Deseralizes the line using JSON deserialization. Optionally strips the 'original_query' and 'original_document'
    fields from the resulting object and converts the qid and docno fields to strings.

    :param str | bytearray | bytes input: A json-serialized string.
    :param bool load_default_text: If true, the origianl_query and original_document fields are removed and the qid and docno
        values are converted to strings.
    :return: The deserialized and (optionally) processed object.
    :rtype: dict

    :Example:
        >>> parse_jsonl_line('{}', False)
        {}
        >>> parse_jsonl_line('{"original_query": "xxxx"}', False)
        {'original_query': 'xxxx'}
        >>> parse_jsonl_line('{"original_query": "xxxx"}', True)
        {}
        >>> parse_jsonl_line('{"original_query": "xxxx", "qid": 42, "pi": 3.14}', False)
        {'original_query': 'xxxx', 'qid': 42, 'pi': 3.14}
        >>> parse_jsonl_line('{"original_query": "xxxx", "qid": 42, "pi": 3.14}', True)
        {'qid': '42', 'pi': 3.14}
    """
    obj = json.loads(input)
    assert isinstance(obj, dict)
    if load_default_text:
        for field_to_del in ['original_query', 'original_document']:
            obj.pop(field_to_del, None)

        for field_to_str in ['qid', 'docno']:
            if field_to_str in obj:
                obj[field_to_str] = str(obj[field_to_str])

    return obj


def stream_all_lines(input_file, load_default_text):
    if type(input_file) is str:
        if not os.path.isfile(input_file):
            return

        if input_file.endswith('.gz'):
            with gzip.open(input_file, 'rt', encoding='utf-8') as f:
                yield from stream_all_lines(f, load_default_text)
        else:
            with open(input_file, 'r') as f:
                yield from stream_all_lines(f, load_default_text)

        return

    for line in input_file:
        yield parse_jsonl_line(line, load_default_text)


def all_lines_to_pandas(input_file: str | Iterable[str], load_default_text):
    if type(input_file) is str:
        if input_file.endswith('.gz'):
            with gzip.open(input_file, 'rt', encoding='utf-8') as f:
                return all_lines_to_pandas(f, load_default_text)
        else:
            with open(input_file, 'r') as f:
                return all_lines_to_pandas(f, load_default_text)

    import pandas as pd
    ret = []

    for line in input_file:
        ret += [parse_jsonl_line(line, load_default_text)]

    return pd.DataFrame(ret)


def __num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def run_cmd(cmd, ignore_failure=False):
    import subprocess
    exit_code = subprocess.call(cmd)

    if not ignore_failure and exit_code != 0:
        raise ValueError(f'Command {cmd} did exit with return code {exit_code}.')


def parse_prototext_key_values(file_name):
    for i in [i for i in open(file_name, 'r').read().split('measure {')]:
        ret = {}
        for l in i.split('\n'):
            if len(l.split(':')) < 2:
                continue
            elif len(l.split(':')) > 2:
                raise ValueError(f'Could not parse "{l}".')
            key = l.split(':')[0]
            value = l.split(':')[1].split('"')[1]
            ret[key.strip()] = __num(value.strip())
        if len(ret) > 0:
            yield ret


def all_environment_variables_for_github_action_or_fail(params):
    ret = {}

    for i in params:
        if len(i.split('=')) != 2:
            raise ValueError(f"Expect that exactly one '=' occurs in each passed parameter, got: '{i}'")

        key, value = i.split('=')

        if key in ret:
            raise ValueError(f"Got duplicated key: '{key}'")
        
        ret[key] = value

    expected_keys = ['GITHUB_SHA', 'TIRA_VM_ID', 'TIRA_TASK_ID', 'TIRA_DOCKER_REGISTRY_TOKEN', 'TIRA_DOCKER_REGISTRY_USER',
                     'TIRA_CLIENT_TOKEN', 'TIRA_CLIENT_USER', 'TIRA_CODE_REPOSITORY_ID']

    for k in expected_keys:
        if k not in ret or not ret[k]:
            raise ValueError(f'I need the parameter {k} to continue, but could not find one or it is empty. This likely is a configuration error, e.g., due to missing secrets.')

    if 'TIRA_JUPYTER_NOTEBOOK' in ret:
        for to_del in ['TIRA_DOCKER_FILE', 'TIRA_DOCKER_PATH', 'TIRA_COMMAND']:
            if to_del in ret:
                del ret[to_del]
        ret['IMAGE_TAG'] = f'registry.webis.de/code-research/tira/tira-user-{ret["TIRA_VM_ID"]}/submission:{ret["GITHUB_SHA"]}'
    else:
        for expected_key in ['TIRA_DOCKER_FILE', 'TIRA_DOCKER_PATH', 'TIRA_COMMAND']:
            if k not in ret or not ret[k]:
                raise ValueError(f'I need the parameter {k} to continue, but could not find one or it is empty. This likely is a configuration error, e.g., due to missing secrets.')
            
            ret['IMAGE_TAG'] = f'registry.webis.de/code-research/tira/tira-user-{ret["TIRA_VM_ID"]}/submission-{ret["TIRA_DOCKER_PATH"].replace("/", "-").replace(" ", "-")}:{ret["GITHUB_SHA"]}'

    return [k + '=' + v for k, v in ret.items()]


def load_output_of_directory(directory, evaluation=False, verbose=False):
    files = glob(str(directory) + '/*')

    if evaluation:
        files = [i for i in files if i.endswith('.prototext')]

    if len(files) != 1:
        raise ValueError('Expected exactly one output file. Got: ', files)

    files = files[0]

    if verbose:
        print(f'Read file from {files}')

    if evaluation:
        ret = {}
        for i in [i for i in open(files, 'r').read().split('measure') if 'key:' in i and 'value:' in i]:
            key = i.split('key:')[1].split('value')[0].split('"')[1]
            value = i.split('key:')[1].split('value')[1].split('"')[1]

            ret[key.strip()] = __num(value.strip())

        return ret
    else:
        return pd.read_json(files, lines=True, orient='records')
