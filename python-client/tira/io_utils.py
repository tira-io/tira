import pandas as pd
from glob import glob


def __num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def load_output_of_directory(directory, evaluation=False, verbose=False):
    files = glob(str(directory) + '/*' )

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

