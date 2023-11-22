import pandas as pd
from glob import glob
import gzip
import json
import os
from typing import Any, Iterable


def parse_jsonl_line(line: str | bytearray | bytes, load_default_text: bool) -> Any:
    jsonline = json.loads(line)
    if load_default_text:
        for field_to_del in ['original_query', 'original_document']:
            if field_to_del in jsonline:
                del jsonline[field_to_del]

        for field_to_str in ['qid', 'docno']:
            if field_to_str in jsonline:
                jsonline[field_to_str] = str(jsonline[field_to_str])

    return jsonline


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
