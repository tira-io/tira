import tempfile
import os
from pathlib import Path
from glob import glob
import docker
import pandas as pd


def __extract_image_and_command(identifier):
    return '', ''


def run(identifier=None, image=None, command=None, data=None, verbose=False):
    if image is None or command is None or data is None:
        image, command = __extract_image_and_command(identifier)
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    
    tmp_dir = Path(tempfile.TemporaryDirectory().name)
    input_dir = tmp_dir / 'input'
    output_dir = tmp_dir / 'output'

    os.makedirs(str(input_dir.absolute()), exist_ok=True)
    os.makedirs(str(output_dir.absolute()), exist_ok=True)

    if verbose:
        print(f'Write {len(data)} records to {input_dir}/input.jsonl')
    
    data.to_json(input_dir / 'input.jsonl', lines=True, orient='records')
    command = command.replace('$inputDataset', '/tira-data/input').replace('$outputDir', '/tira-data/output')
    
    if verbose:
        print(f'docker run --rm -ti -v {tmp_dir}:/tira-data --entrypoint sh {image} {command}')
    
    client.containers.run(image, entrypoint='sh', command=f'-c "{command}"', volumes={str(tmp_dir): {'bind': '/tira-data/', 'mode': 'rw'}})
    
    output_files = glob(str(output_dir) + '/*' )
    if len(output_files) != 1:
        raise ValueError('Expected exactly one output file. Got: ', output_file)
    
    if verbose:
        print(f'Read output from {output_files[0]}')
              
    return pd.read_json(output_files[0], lines=True, orient='records')

