from hashlib import md5

import requests

from tira.rest_api_client import Client
from tira.tira_redirects import redirects


def md5_of_first_kilobyte_of_http_resource(url):
    # if not url.startswith('https://files.webis.de'):
    #    raise ValueError(f'URL {url} is not from webis.de respectively zenodo')
    print(url, flush=True)
    return md5(requests.get(url, headers={"Range": "bytes=0-1024"}).content).hexdigest()


def digest_of_resource(resource):
    from tira.tira_redirects import RESOURCE_REDIRECTS

    if resource not in RESOURCE_REDIRECTS:
        raise ValueError("Could not find resource {resource}.")

    url = RESOURCE_REDIRECTS[resource]

    return {
        "url": url,
        "redirect_url": redirects(url=url),
        "md5_of_first_kilobyte": md5_of_first_kilobyte_of_http_resource(url),
    }


def digest_of_dataset(dataset_id, truth=False):
    t = "input-" if not truth else "input-truth"
    tira_url = f"https://www.tira.io/data-download/training/{t}/{dataset_id}.zip"
    url_redirects = redirects(url=tira_url)

    return {
        "tira_url": tira_url,
        "redirect_url": url_redirects,
        "md5_of_first_kilobyte": md5_of_first_kilobyte_of_http_resource(url_redirects["urls"][0]),
    }


def digest_of_run_output(approach, dataset_id, run_ids):
    tira = Client()
    task, team, system = approach.split("/")
    filename = f"{run_ids[task][team][system][dataset_id]}.zip"
    run_url = f"https://www.tira.io/task/{task}/user/{team}/dataset/{dataset_id}/download/{filename}"

    return {
        "redirect_url": redirects(approach, dataset_id),
        "run_execution": tira.get_run_execution_or_none(approach, dataset_id),
        "run_url": run_url,
        "redirected_run_url": redirects(url=run_url),
        "md5_of_first_kilobyte": md5_of_first_kilobyte_of_http_resource(redirects(url=run_url)["urls"][0]),
    }
