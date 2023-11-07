# The TIRA Client

This is a python client for [TIRA.io](https://tira.io).

## Setup REST Client to Access Non-Public Endpoints

To access non-public endpoints, you will need an authentication via an API key to ensure that you have the correct access credentials.
Please generate your API key online at [tira.io/admin/api/keys](https://www.tira.io/admin/api/keys) and create a credentials file at `~/.tira/.tira-settings.json` with the following content:

```
{"api_key": "<YOUR-API-KEY>"}
```

## Download The results of some Submission

You can download runs of published and unblinded submissions via:

```
from tira.rest_api_client import Client

tira = Client()
output = tira.get_run_output('<task>/<team>/<approach>', '<dataset>')
```

As an example, you can download all baseline BM25 runs submitted to [TIREx](https://www.tira.io/tirex) via:

```
from tira.rest_api_client import Client
from tira.tirex import TIREX_DATASETS

tira = Client()

for dataset in TIREX_DATASETS:
    output = tira.get_run_output('ir-benchmarks/tira-ir-starter/BM25 Re-Rank (tira-ir-starter-pyterrier)', dataset)
```

## Overview of public submissions

As an example, you can see all public software submissions submitted to [TIREx](https://www.tira.io/tirex) via:

```
from tira.rest_api_client import Client

tira = Client()
submissions = tira.all_softwares("ir-benchmarks")
```

## Export datasets

You can export datasets if you are the owner or if the dataset is public.
Export a dataset via the cli:

```
tira-run --export-dataset '<task>/<tira-dataset>' --output-directory tira-dataset
```

Export a dataset via the python API:
```
from tira.rest_api_client import Client

tira = Client()
tira.download_dataset('<task>', '<tira-dataset>')
```

## Running Jupyter Notebooks with TIRA


```bash
docker build -t tira/submission-base-image:1.0.0 -f Dockerfile .
```
Testing the model locally can be done using the following command:
```bash
tira-run \
  --input-directory ${PWD}/input \
  --output-directory ${PWD}/output \
  --image tira/submission-base-image:1.0.0 \
  --command 'tira-run-notebook --input $inputDataset --output $outputDir /workspace/template-notebook.ipynb'
```
---
Afterwards you can push the image to TIRA
```bash
docker push tira/submission-base-image:1.0.0
```
and set the command:
```bash
tira-run-notebook --input $inputDataset --output $outputDir /workspace/template-notebook.ipynb
```

---
Finally, if the actual processing in notebook is toggled via `is_running_as_inference_server()` (as seen in the
[template notebook](template-notebook.ipynb))
and your notebook defines a function named `predict` in the format
```python
def predict(input_list: List) -> List:
```
you can start an inference server for your model with:
```bash
PORT=8001

docker run --rm -it --init \
  -v "$PWD/logs:/workspace/logs" \
  -p $PORT:$PORT \
  tira/submission-base-image:1.0.0 \
  tira-run-inference-server --notebook /workspace/template-notebook.ipynb --port $PORT
```

Exemplary request for a server running on `localhost:8001` are
```bash
# POST (JSON list as payload)
curl -X POST -H "application/json" \
  -d "[\"element 1\", \"element 2\", \"element 3\"]" \
  localhost:8001
```
and
```bash
# GET (JSON object string(s) passed to the 'payload' parameter)
curl "localhost:8001?payload=\"element+1\"&payload=\"element+2\"&payload=\"element+3\""
```
