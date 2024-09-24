import json
from pathlib import Path

from tira.license_agreements import print_license_agreement

TIRA_ZENODO_BASE_URL = "https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation"

STATIC_REDIRECTS = {
    "ir-benchmarks": {
        "tira-ir-starter": {
            "Index (tira-ir-starter-pyterrier)": {
                "msmarco-passage-trec-dl-2019-judged-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-22-09-56.zip",
                    ],
                    "run_id": "2023-01-07-22-09-56",
                },
                "msmarco-passage-trec-dl-2020-judged-20230107-training": {
                    # better caching: dl2020 and 2019 used the same corpus
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-22-09-56.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-22-09-56.zip",
                    ],
                    "run_id": "2023-01-07-22-09-56",
                    # 'url': f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-09-19-37-45.zip",
                    # 'run_id': '2023-02-09-19-37-45',
                },
                "antique-test-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-13-40-04.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-13-40-04.zip",
                    ],
                    "run_id": "2023-01-07-13-40-04",
                },
                "vaswani-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-19-01-50.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-19-01-50.zip",
                    ],
                    "run_id": "2023-01-07-19-01-50",
                },
                "cranfield-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-13-39-11.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-13-39-11.zip",
                    ],
                    "run_id": "2023-01-07-13-39-11",
                },
                "medline-2004-trec-genomics-2004-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-07-19-37-49.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-07-19-37-49.zip",
                    ],
                    "run_id": "2023-01-07-19-37-49",
                },
                "medline-2017-trec-pm-2017-20230211-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-11-20-52-47.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-11-20-52-47.zip",
                    ],
                    "run_id": "2023-02-11-20-52-47",
                },
                "cord19-fulltext-trec-covid-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-01-08-15-18-20.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-01-08-15-18-20.zip",
                    ],
                    "run_id": "2023-01-08-15-18-20",
                },
                "nfcorpus-test-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-09-15-46-37.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-09-15-46-37.zip",
                    ],
                    "run_id": "2023-02-09-15-46-37",
                },
                "argsme-touche-2020-task-1-20230209-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-09-17-50-22.zip",
                    ],
                    "run_id": "2023-02-09-17-50-22",
                },
                "argsme-touche-2021-task-1-20230209-training": {
                    # better caching: dl2020 and 2019 used the same corpus
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-09-17-50-22.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-09-17-50-22.zip",
                    ],
                    "run_id": "2023-02-09-17-50-22",
                },
                "medline-2017-trec-pm-2018-20230211-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-11-15-15-35.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-11-15-15-35.zip",
                    ],
                    "run_id": "2023-02-11-15-15-35",
                },
                "medline-2004-trec-genomics-2005-20230107-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-02-09-22-14-32.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-02-09-22-14-32.zip",
                    ],
                    "run_id": "2023-02-09-22-14-32",
                },
                "trec-tip-of-the-tongue-dev-20230607-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-11-10-23-23-59.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-11-10-23-23-59.zip",
                    ],
                    "run_id": "2023-11-10-23-23-59",
                },
                "longeval-short-july-20230513-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-11-10-23-22-59.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-11-10-23-22-59.zip",
                    ],
                    "run_id": "2023-11-10-23-22-59",
                },
                "longeval-heldout-20230513-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-11-10-23-21-55.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-11-10-23-21-55.zip",
                    ],
                    "run_id": "2023-11-10-23-21-55",
                },
                "longeval-long-september-20230513-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-11-10-21-09-17.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-11-10-21-09-17.zip",
                    ],
                    "run_id": "2023-11-10-21-09-17",
                },
                "longeval-train-20230513-training": {
                    "urls": [
                        "https://zenodo.org/records/10743990/files/2023-11-11-06-49-15.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/pyterrier-indexes/2023-11-11-06-49-15.zip",
                    ],
                    "run_id": "2023-11-11-06-49-15",
                },
                "longeval-2023-01-20240423-training": {
                    "run_id": "2024-04-24-01-24-17",
                    "md5": "8bb006a0e8d32a2d1d3030f7140ea205",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/2024-04-24-01-24-17.zip"],
                },
                "longeval-2023-06-20240418-training": {
                    "run_id": "2024-04-18-18-04-27",
                    "md5": "bcc930aded82f2b20269e460a7e8d7bb",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/2024-04-18-18-04-27.zip"],
                },
                "longeval-2023-08-20240418-training": {
                    "run_id": "2024-04-18-18-16-52",
                    "md5": "47d62f254408281ef03c603248c44abc",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/2024-04-18-18-16-52.zip"],
                },
            }
        },
        "seanmacavaney": {
            "DocT5Query": {
                "msmarco-passage-trec-dl-2019-judged-20230107-training": {
                    "run_id": "2024-03-19-20-04-59",
                    "md5": "3d07a6c1364534a3c62825316703845a",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-20-04-59.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-20-04-59.zip",
                    ],
                },
                "msmarco-passage-trec-dl-2020-judged-20230107-training": {
                    # better caching: dl2020 and 2019 used the same corpus
                    "run_id": "2024-03-19-20-04-59",
                    "md5": "3d07a6c1364534a3c62825316703845a",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-20-04-59.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-20-04-59.zip",
                    ],
                },
                "trec-tip-of-the-tongue-dev-20230607-training": {
                    "run_id": "2024-03-19-19-58-58",
                    "md5": "365ff525cca8302608c2df113eaad170",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-58-58.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-58-58.zip",
                    ],
                },
                "antique-test-20230107-training": {
                    "run_id": "2024-03-19-18-06-23",
                    "md5": "b019d109841dfce4db65bb315750024b",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-18-06-23.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-18-06-23.zip",
                    ],
                },
                "vaswani-20230107-training": {
                    "run_id": "2024-03-19-19-32-44",
                    "md5": "00d788fd9ccc6eba51558800ba94c731",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-32-44.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-32-44.zip",
                    ],
                },
                "cranfield-20230107-training": {
                    "run_id": "2024-03-19-17-50-12",
                    "md5": "07d8fd9ab63569f6ea2a80aee86db55a",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-17-50-12.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-17-50-12.zip",
                    ],
                },
                "nfcorpus-test-20230107-training": {
                    "run_id": "2024-03-19-19-51-27",
                    "md5": "047e5276a69ab7353f584ab08e817539",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-51-27.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-51-27.zip",
                    ],
                },
                "medline-2017-trec-pm-2017-20230211-training": {
                    "run_id": "2024-03-19-19-48-04",
                    "md5": "e23d2535cc67c7bafe513c40510da6fa",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-48-04.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-48-04.zip",
                    ],
                },
                "argsme-touche-2020-task-1-20230209-training": {
                    "run_id": "2024-03-19-17-52-36",
                    "md5": "6698ba27029448dac2a8a7293d0376a2",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-17-52-36.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-17-52-36.zip",
                    ],
                },
                "argsme-touche-2021-task-1-20230209-training": {
                    "run_id": "2024-03-19-17-59-19",
                    "md5": "f22fdcb8c25255e64a2380de42414689",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-17-59-19.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-17-59-19.zip",
                    ],
                },
                "longeval-short-july-20230513-training": {
                    "run_id": "2024-03-19-19-57-39",
                    "md5": "ea47bb4a0f7d8999db1e510d45096214",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-57-39.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-57-39.zip",
                    ],
                },
                "longeval-heldout-20230513-training": {
                    "run_id": "2024-03-19-19-49-22",
                    "md5": "9b97188e7d7383d1cea4dc6630c37081",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-49-22.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-49-22.zip",
                    ],
                },
                "longeval-long-september-20230513-training": {
                    "run_id": "2024-03-19-19-52-58",
                    "md5": "1895e01418d7170ac02be6ac1a9a185f",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-52-58.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-52-58.zip",
                    ],
                },
                "longeval-train-20230513-training": {
                    "run_id": "2024-03-19-19-46-01",
                    "md5": "44504a96a16e4e4eaef760025cb9c91b",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-19-19-46-01.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/doc-t5-query/2024-03-19-19-46-01.zip",
                    ],
                },
            },
            "corpus-graph": {
                "msmarco-passage-trec-dl-2019-judged-20230107-training": {
                    "run_id": "2024-03-21-12-27-29",
                    "md5": "93d2166f8498bb664afc1782ffdf2106",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-27-29.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-27-29.zip",
                    ],
                },
                "msmarco-passage-trec-dl-2020-judged-20230107-training": {
                    # better caching: dl2020 and 2019 used the same corpus
                    "run_id": "2024-03-21-12-27-29",
                    "md5": "93d2166f8498bb664afc1782ffdf2106",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-27-29.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-27-29.zip",
                    ],
                },
                "antique-test-20230107-training": {
                    "run_id": "2024-03-21-15-00-49",
                    "md5": "0fe6df76b5fd121c395a5008c0485447",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-15-00-49.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-15-00-49.zip",
                    ],
                },
                "longeval-short-july-20230513-training": {
                    "run_id": "2024-03-21-12-45-07",
                    "md5": "cb813f8d7193b436132e035613f983d4",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-45-07.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-45-07.zip",
                    ],
                },
                "longeval-heldout-20230513-training": {
                    "run_id": "2024-03-21-12-39-51",
                    "md5": "290a3fb49d516b4dee3c1ddcf61c0884",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-39-51.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-39-51.zip",
                    ],
                },
                "longeval-long-september-20230513-training": {
                    "run_id": "2024-03-21-12-40-32",
                    "md5": "467241170d83d8320df5207a20c95454",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-40-32.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-40-32.zip",
                    ],
                },
                "longeval-train-20230513-training": {
                    "run_id": "2024-03-21-12-46-50",
                    "md5": "4c6a959deadcbd8a4327c10270ff5b63",
                    "urls": [
                        "https://zenodo.org/records/10852971/files/2024-03-21-12-46-50.zip?download=1",
                        f"{TIRA_ZENODO_BASE_URL}/corpus-graph/2024-03-21-12-46-50.zip",
                    ],
                },
            },
        },
    },
    "ir-lab-sose-2024": {
        "tira-ir-starter": {
            "Index (tira-ir-starter-pyterrier)": {
                "ir-acl-anthology-20240411-training": {
                    "run_id": "2024-04-11-19-43-23",
                    "md5": "ebb5b8f1d8c7ad36612f408da1203ff2",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-11-19-43-23.zip"],
                },
                "ir-acl-anthology-20240504-training": {
                    "run_id": "2024-05-04-16-05-53",
                    "md5": "d571b44aa24ecd06615932a246ff7e6b",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-05-04-16-05-53.zip"],
                },
            },
            "Index (pyterrier-stanford-lemmatizer)": {
                "ir-acl-anthology-20240411-training": {
                    "run_id": "2024-04-16-11-05-06",
                    "md5": "70aa7ce8a437ba47ebf9e17d75871a5f",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-16-11-05-06.zip"],
                }
            },
        },
        "seanmacavaney": {
            "DocT5Query": {
                "anthology-20240411-training": {
                    "run_id": "2024-04-09-22-03-26",
                    "md5": "1a0f65a8f47051db435ec6031106db7b",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-09-22-03-26.zip"],
                }
            },
            "corpus-graph": {
                "anthology-20240411-training": {
                    "run_id": "2024-04-09-16-35-50",
                    "md5": "75f743914d44d7252425844136ea9722",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-09-16-35-50.zip"],
                }
            },
            # "some-interface": {
            # copy of corpus-graph
            #    "anthology-20240411-training": {
            #        "run_id": "2024-04-09-16-35-50",
            #        "md5": "75f743914d44d7252425844136ea9722"
            #    }
            # }
        },
        "ows": {
            "pyterrier-anceindex": {
                "ir-acl-anthology-20240411-training": {
                    "run_id": "2024-04-11-19-47-18",
                    "md5": "1112dc9e60b6dfa4ac80571ad3425200",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-11-19-47-18.zip"],
                }
            }
        },
        "naverlabseurope": {
            "Splade (Index)": {
                "ir-acl-anthology-20240411-training": {
                    "run_id": "2024-04-14-08-40-58",
                    "md5": "03f73b47664cc1c843529b948094bf81",
                    "urls": [f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/2024-04-14-08-40-58.zip"],
                }
            }
        },
    },
}


def join_to_static_redirects(name, http_base_url):
    json_file = Path(__file__).parent.resolve() / "static_redirects" / f"{name}.json"
    json_file = json.load(open(json_file, "r"))
    for redirected_approach in json_file:
        task_id, team_name, approach_name = redirected_approach.split("/")
        cache_file_name = (
            json_file[redirected_approach]["class"]
            if "class" in json_file[redirected_approach]
            else f"{team_name}-{approach_name}".lower().replace(" ", "-").replace("(", "").replace(")", "")
        )
        cache_file_name += ".zip"

        if task_id not in STATIC_REDIRECTS:
            STATIC_REDIRECTS[task_id] = {}
        if team_name not in STATIC_REDIRECTS[task_id]:
            STATIC_REDIRECTS[task_id][team_name] = {}
        if approach_name not in STATIC_REDIRECTS[task_id][team_name]:
            STATIC_REDIRECTS[task_id][team_name][approach_name] = {}

        for dataset_id, run_id in json_file[redirected_approach]["runs"].items():
            if dataset_id in STATIC_REDIRECTS[task_id][team_name][approach_name]:
                raise ValueError("Duplicated execution in the cache.")

            STATIC_REDIRECTS[task_id][team_name][approach_name][dataset_id] = {
                "urls": [http_base_url + cache_file_name + "?download=1"],
                "run_id": run_id,
            }


join_to_static_redirects(
    "reneuir-2024",
    f"{TIRA_ZENODO_BASE_URL}/reneuir-2024/runs/",
)
TASKS_WITH_REDIRECT_MERGING = set()
RUN_ID_TO_SYSTEM = {}
for task in STATIC_REDIRECTS.keys():
    TASKS_WITH_REDIRECT_MERGING.add(task)
    for team in STATIC_REDIRECTS[task].keys():
        for system_name in STATIC_REDIRECTS[task][team].keys():
            system = STATIC_REDIRECTS[task][team][system_name]
            for config in system.values():
                RUN_ID_TO_SYSTEM[config["run_id"]] = system_name

QUERY_PROCESSORS = {
    "ir-benchmarks": {
        "qpptk": {
            "all-predictors": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "1c25b7cce08acbb6deb0be767a5d6fa2",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-27-21-30-47",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-27-21-31-54",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-02-27-21-36-40",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "049143bd2cfc933f1f0b9d765444349b",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-27-20-06-32",
                        "vaswani-20230107-training": "2024-02-27-21-38-47",
                        "cranfield-20230107-training": "2024-02-27-20-20-33",
                        "nfcorpus-test-20230107-training": "2024-02-27-21-34-23",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "d1d967b33760c76ddd150b38004f13f1",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-02-27-21-21-07",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-27-21-27-05",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-27-20-18-28",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-27-21-28-47",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-02-27-21-26-22",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "362f8efcdad0932917bd4a5d029668cc",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-27-20-09-14",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-27-20-10-51",
                        "longeval-short-july-20230513-training": "2024-02-27-21-15-17",
                        "longeval-heldout-20230513-training": "2024-02-27-20-56-41",
                        "longeval-long-september-20230513-training": "2024-02-27-21-10-42",
                        "longeval-train-20230513-training": "2024-02-27-21-19-19",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "7f2d29c20638f9a901fe5ffb23772834",
                    "run_ids": {
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-27-20-13-20",
                        "gov-trec-web-2002-20230209-training": "2024-02-27-20-26-06",
                        "gov-trec-web-2003-20230209-training": "2024-02-27-20-27-09",
                        "gov-trec-web-2004-20230209-training": "2024-02-27-20-29-21",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-27-20-30-58",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-27-20-33-27",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-27-20-37-51",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "9119381b68f4f405deb3feeed7ab300f",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-27-21-40-17",
                        "disks45-nocr-trec8-20230209-training": "2024-02-27-20-24-50",
                        "disks45-nocr-trec7-20230209-training": "2024-02-27-20-23-24",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-27-20-22-13",
                    },
                },
            }
        },
        "salamander": {
            "classify-comparative-queries": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "b5bcfbbabfab68ca7769f52dc74ff3d2",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-25-16-58-54",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-25-20-36-41",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "595b9fd7a6e84ae0f7711be00f7dee25",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-25-15-17-55",
                        "vaswani-20230107-training": "2024-02-25-20-40-09",
                        "cranfield-20230107-training": "2024-02-25-15-45-40",
                        "nfcorpus-test-20230107-training": "2024-02-25-20-37-46",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "99fad757c51ec589fad627c509db1375",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-02-25-16-09-36",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-25-16-12-21",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-25-15-44-30",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-25-16-57-26",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-02-25-16-11-16",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "cdc91e48f0e0794aed6d3564a3184f23",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-25-15-19-08",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-25-15-20-13",
                        "longeval-short-july-20230513-training": "2024-02-25-16-04-17",
                        "longeval-heldout-20230513-training": "2024-02-25-16-01-03",
                        "longeval-long-september-20230513-training": "2024-02-25-16-03-12",
                        "longeval-train-20230513-training": "2024-02-25-16-06-29",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "0e213ab92e2d6d769673b091dba167b0",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-02-25-15-21-18",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-02-25-15-24-17",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-02-25-15-25-22",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-02-25-15-26-28",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-02-25-15-27-38",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-02-25-15-28-44",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-25-15-29-50",
                        "clueweb12-trec-web-2013-20230107-training": "2024-02-25-15-30-55",
                        "clueweb12-trec-web-2014-20230107-training": "2024-02-25-15-32-03",
                        "gov-trec-web-2002-20230209-training": "2024-02-25-15-51-54",
                        "gov-trec-web-2003-20230209-training": "2024-02-25-15-53-06",
                        "gov-trec-web-2004-20230209-training": "2024-02-25-15-54-30",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-25-15-55-44",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-25-15-58-17",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-25-15-59-47",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "49e5f5fd0ea51f8fba703a80602cbc49",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-25-20-41-24",
                        "disks45-nocr-trec8-20230209-training": "2024-02-25-15-51-07",
                        "disks45-nocr-trec7-20230209-training": "2024-02-25-15-49-58",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-25-15-48-48",
                    },
                },
            }
        },
        "ows": {
            "query-segmentation-hyb-a": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "76653ff365f88c7df931c17a84424b71",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-25-07-57-14",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-25-07-58-43",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "aad5c93fbfe4d0e47875500cdf426229",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-25-06-14-01",
                        "vaswani-20230107-training": "2024-02-25-09-10-19",
                        "nfcorpus-test-20230107-training": "2024-02-25-09-31-46",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "f382c48941b16add98dd22bf29e645d6",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-02-25-06-54-36",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-25-06-58-31",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-25-00-17-52",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-25-08-00-37",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "f0f7812a0b768d88ff2c953075bcf032",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-25-06-15-29",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-24-23-35-21",
                        "longeval-short-july-20230513-training": "2024-02-25-08-11-42",
                        "longeval-heldout-20230513-training": "2024-02-25-08-09-09",
                        "longeval-long-september-20230513-training": "2024-02-25-08-10-24",
                        "longeval-train-20230513-training": "2024-02-25-08-12-47",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "2d39fe456528038eae1a97901e789449",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2023-11-02-13-08-25",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-02-24-23-38-34",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-02-24-23-43-13",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-02-24-23-44-25",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-02-24-23-45-36",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-02-24-23-46-38",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-24-23-53-25",
                        "clueweb12-trec-web-2013-20230107-training": "2024-02-24-23-55-48",
                        "clueweb12-trec-web-2014-20230107-training": "2024-02-25-00-16-12",
                        "gov-trec-web-2002-20230209-training": "2024-02-25-06-18-07",
                        "gov-trec-web-2003-20230209-training": "2024-02-25-00-35-06",
                        "gov-trec-web-2004-20230209-training": "2024-02-25-00-36-45",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-25-00-38-02",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-25-00-40-11",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-25-00-41-47",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "d8516b14523e4247d46a2eea3d3e794f",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-25-06-52-49",
                        "disks45-nocr-trec8-20230209-training": "2024-02-25-00-25-21",
                        "disks45-nocr-trec7-20230209-training": "2024-02-25-00-19-33",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2023-11-02-13-07-52",
                    },
                },
            }
        },
        "dossier": {
            "pre-retrieval-query-intent": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "de6205ef151b2bfef951c8fa10d797f7",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-26-19-33-36",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-26-19-35-37",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-02-26-19-40-46",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "c893a8ab6400830388bccdc1dbb7f518",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-26-17-12-41",
                        "vaswani-20230107-training": "2024-02-26-19-42-46",
                        "cranfield-20230107-training": "2024-02-26-17-44-46",
                        "nfcorpus-test-20230107-training": "2024-02-26-19-37-52",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "366042bb1882101df3eaae684ac88115",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-02-26-19-28-40",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-26-19-31-16",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-26-17-43-08",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-26-19-32-28",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-02-26-19-30-06",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "a03cb859e1e32852ceac58d8afa00611",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-26-17-15-36",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-26-17-17-33",
                        "longeval-short-july-20230513-training": "2024-02-26-19-25-39",
                        "longeval-heldout-20230513-training": "2024-02-26-19-22-37",
                        "longeval-long-september-20230513-training": "2024-02-26-19-24-16",
                        "longeval-train-20230513-training": "2024-02-26-19-27-33",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "62e7365ada547fc5a0810237cb78ad0b",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-02-26-17-18-45",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-02-26-17-20-45",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-02-26-17-24-55",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-02-26-17-29-51",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-02-26-17-30-59",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-02-26-17-32-36",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-26-17-36-05",
                        "clueweb12-trec-web-2013-20230107-training": "2024-02-26-17-37-38",
                        "clueweb12-trec-web-2014-20230107-training": "2024-02-26-17-40-20",
                        "gov-trec-web-2002-20230209-training": "2024-02-26-17-51-12",
                        "gov-trec-web-2003-20230209-training": "2024-02-26-17-53-35",
                        "gov-trec-web-2004-20230209-training": "2024-02-26-17-56-43",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-26-19-13-24",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-26-19-14-39",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-26-19-15-59",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "a72ba671e6b4884a0a86563160062d8a",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-26-19-44-28",
                        "disks45-nocr-trec8-20230209-training": "2024-02-26-17-49-59",
                        "disks45-nocr-trec7-20230209-training": "2024-02-26-17-47-43",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-26-17-46-48",
                    },
                },
            }
        },
        "tu-dresden-03": {
            "qe-gpt3.5-sq-zs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "48f980dca163c86b81c27db640f1a144",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-10-23-21-00",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-10-23-24-23",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-10-23-53-03",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "fc483a0f40b82f9bc783f8c6813ce6bc",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-10-22-10-01",
                        "vaswani-20230107-training": "2024-03-10-23-31-54",
                        "cranfield-20230107-training": "2024-03-10-22-35-20",
                        "nfcorpus-test-20230107-training": "2024-03-10-23-28-11",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "cf0e31c5d4881cde60f3cd67c2c487d5",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-10-23-07-10",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-10-23-13-46",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-10-22-31-58",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-10-23-17-22",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-10-23-10-24",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "fad007784ba10e714164cf4401556656",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-10-22-13-28",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-10-22-17-02",
                        "longeval-short-july-20230513-training": "2024-03-10-23-46-07",
                        "longeval-heldout-20230513-training": "2024-03-10-23-38-30",
                        "longeval-long-september-20230513-training": "2024-03-10-23-42-12",
                        "longeval-train-20230513-training": "2024-03-10-23-49-34",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "344735a5aff3aa53f27aafc6e6ee627a",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-10-21-45-42",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-10-21-49-07",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-10-21-52-44",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-10-21-56-30",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-10-22-20-43",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-10-22-24-26",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-10-22-28-13",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-10-22-00-00",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-10-22-03-19",
                        "gov-trec-web-2002-20230209-training": "2024-03-10-22-45-29",
                        "gov-trec-web-2003-20230209-training": "2024-03-10-22-49-06",
                        "gov-trec-web-2004-20230209-training": "2024-03-10-22-52-40",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-10-22-56-22",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-10-22-59-53",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-10-23-03-34",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "2e314cfcc068a7f07fec8cafc980d630",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-10-23-35-07",
                        "disks45-nocr-trec8-20230209-training": "2024-03-10-22-42-10",
                        "disks45-nocr-trec7-20230209-training": "2024-03-10-22-38-46",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-10-22-06-48",
                    },
                },
            },
            "qe-llama-sq-zs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "0ee2e3c08f6f7018be9e03186f5be4ed",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-11-11-24-14",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-11-11-28-01",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-11-12-56-13",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "6b046261eacd0e2e36841a46a4673f1b",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-11-10-12-20",
                        "vaswani-20230107-training": "2024-03-11-12-33-41",
                        "cranfield-20230107-training": "2024-03-11-10-37-42",
                        "nfcorpus-test-20230107-training": "2024-03-11-11-31-37",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "a98d3d0cf8d1cf5e072c9a5d60104776",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-11-11-09-58",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-11-11-17-03",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-11-10-34-13",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-11-11-20-41",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-11-11-13-15",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "4b67a7a755bb76eb652e3bfd4c7fd596",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-11-10-15-56",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-11-10-19-55",
                        "longeval-short-july-20230513-training": "2024-03-11-12-48-27",
                        "longeval-heldout-20230513-training": "2024-03-11-12-41-01",
                        "longeval-long-september-20230513-training": "2024-03-11-12-44-42",
                        "longeval-train-20230513-training": "2024-03-11-12-52-26",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "b795cbd7a4b16f19aeedacbe5a81ed25",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-11-09-48-10",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-11-09-51-37",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-11-09-55-00",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-11-09-58-17",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-11-10-23-31",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-11-10-27-09",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-11-10-30-45",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-11-10-01-45",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-11-10-05-13",
                        "gov-trec-web-2002-20230209-training": "2024-03-11-10-48-40",
                        "gov-trec-web-2003-20230209-training": "2024-03-11-10-52-24",
                        "gov-trec-web-2004-20230209-training": "2024-03-11-10-56-10",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-11-10-59-35",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-11-11-03-01",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-11-11-06-26",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "8d3b6fef513d1177fd5ced6f9a8d9208",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-11-12-37-19",
                        "disks45-nocr-trec8-20230209-training": "2024-03-11-10-45-12",
                        "disks45-nocr-trec7-20230209-training": "2024-03-11-10-41-34",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-11-10-08-47",
                    },
                },
            },
            "qe-llama-sq-fs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "0951ad895a5691d5e556e89b17fa2c6c",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-11-09-12-36",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-11-09-16-25",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-11-09-44-45",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "d245515ace5292f547f3778ccb7870fa",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-11-08-01-16",
                        "vaswani-20230107-training": "2024-03-11-09-23-25",
                        "cranfield-20230107-training": "2024-03-11-08-26-26",
                        "nfcorpus-test-20230107-training": "2024-03-11-09-20-02",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "c8b5d88c36cfb68fa1d4c89662c22f90",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-11-08-58-33",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-11-09-05-18",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-11-08-22-58",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-11-09-08-56",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-11-09-01-54",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "6a828227d3dad624245ec74aee56d165",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-11-08-05-00",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-11-08-08-49",
                        "longeval-short-july-20230513-training": "2024-03-11-09-37-33",
                        "longeval-heldout-20230513-training": "2024-03-11-09-30-01",
                        "longeval-long-september-20230513-training": "2024-03-11-09-34-00",
                        "longeval-train-20230513-training": "2024-03-11-09-41-08",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "4260663fa19abd78ac31666a40486b23",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-11-07-35-54",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-11-07-39-18",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-11-07-43-07",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-11-07-46-27",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-11-08-12-28",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-11-08-16-20",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-11-08-19-45",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-11-07-50-22",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-11-07-54-08",
                        "gov-trec-web-2002-20230209-training": "2024-03-11-08-36-41",
                        "gov-trec-web-2003-20230209-training": "2024-03-11-08-40-26",
                        "gov-trec-web-2004-20230209-training": "2024-03-11-08-44-20",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-11-08-48-05",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-11-08-51-47",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-11-08-55-01",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "42d67874e8bc3cbbcdc964603e8b4da0",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-11-09-26-47",
                        "disks45-nocr-trec8-20230209-training": "2024-03-11-08-33-25",
                        "disks45-nocr-trec7-20230209-training": "2024-03-11-08-30-00",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-11-07-57-21",
                    },
                },
            },
            "qe-llama-cot": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "fbd5e1faa6a736834f2af75fa06975a4",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-11-06-44-59",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-11-06-48-35",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-11-07-32-21",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "ae412a1b1dec44b06c47b03dd95d3b9a",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-11-05-02-44",
                        "vaswani-20230107-training": "2024-03-11-06-56-01",
                        "cranfield-20230107-training": "2024-03-11-05-58-31",
                        "nfcorpus-test-20230107-training": "2024-03-11-06-52-23",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "069290938ac20bc05c3fb5983f4f4da8",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-11-06-30-51",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-11-06-37-54",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-11-05-54-54",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-11-06-41-21",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-11-06-34-42",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "83b8e2e70372fa213e1944a67fb9bc78",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-11-05-06-08",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-11-05-09-23",
                        "longeval-short-july-20230513-training": "2024-03-11-07-24-45",
                        "longeval-heldout-20230513-training": "2024-03-11-07-18-03",
                        "longeval-long-september-20230513-training": "2024-03-11-07-21-27",
                        "longeval-train-20230513-training": "2024-03-11-07-28-35",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "16cdb82694d55b3e354ad983033f6689",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-11-04-38-08",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-11-04-41-35",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-11-04-44-59",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-11-04-48-37",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-11-05-12-59",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-11-05-48-01",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-11-05-51-18",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-11-04-52-19",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-11-04-55-40",
                        "gov-trec-web-2002-20230209-training": "2024-03-11-06-09-07",
                        "gov-trec-web-2003-20230209-training": "2024-03-11-06-12-49",
                        "gov-trec-web-2004-20230209-training": "2024-03-11-06-16-30",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-11-06-20-18",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-11-06-23-56",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-11-06-27-22",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "15f86d3f20a648233cd6ed41475f9dcc",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-11-06-59-20",
                        "disks45-nocr-trec8-20230209-training": "2024-03-11-06-05-33",
                        "disks45-nocr-trec7-20230209-training": "2024-03-11-06-02-12",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-11-04-59-00",
                    },
                },
            },
            "qe-flan-ul2-sq-zs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "a4789c3bf75c582eb9ccb0655592a0e2",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-12-13-22-06",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-12-13-24-02",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-12-13-45-36",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "d16a3ba3bfe06f163179282765146898",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-12-11-42-21",
                        "vaswani-20230107-training": "2024-03-12-13-32-08",
                        "cranfield-20230107-training": "2024-03-12-12-47-07",
                        "nfcorpus-test-20230107-training": "2024-03-12-13-25-53",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "f0073b2adface58ff32385fd875ae247",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-12-13-09-45",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-12-13-13-39",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-12-12-44-56",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-12-13-15-57",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-12-13-11-55",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "81db68c792f16e69f36aaad5e1462323",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-12-11-44-07",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-12-11-46-01",
                        "longeval-short-july-20230513-training": "2024-03-12-13-41-03",
                        "longeval-heldout-20230513-training": "2024-03-12-13-36-26",
                        "longeval-long-september-20230513-training": "2024-03-12-13-38-45",
                        "longeval-train-20230513-training": "2024-03-12-13-43-24",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "d9e9b07116977c31cdc5ea805657e259",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-12-11-23-47",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-12-11-25-47",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-12-11-27-50",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-12-11-30-10",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-12-11-48-17",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-12-12-40-51",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-12-12-43-11",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-12-11-31-55",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-12-11-34-12",
                        "gov-trec-web-2002-20230209-training": "2024-03-12-12-57-09",
                        "gov-trec-web-2003-20230209-training": "2024-03-12-12-59-04",
                        "gov-trec-web-2004-20230209-training": "2024-03-12-13-01-12",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-12-13-03-24",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-12-13-05-30",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-12-13-07-43",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "545ab1286c97e133297ecdeb4fbdaff4",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-12-13-34-24",
                        "disks45-nocr-trec8-20230209-training": "2024-03-12-12-55-11",
                        "disks45-nocr-trec7-20230209-training": "2024-03-12-12-49-05",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-12-11-36-08",
                    },
                },
            },
            "qe-flan-ul2-sq-fs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "bdd2ae8e122c9f2813c083e5cc53caf0",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-12-11-02-51",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-12-11-04-38",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-12-11-21-42",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "ea1a73d34c8f7f5126537e90dbb4630f",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-12-10-02-37",
                        "vaswani-20230107-training": "2024-03-12-11-08-58",
                        "cranfield-20230107-training": "2024-03-12-10-30-49",
                        "nfcorpus-test-20230107-training": "2024-03-12-11-06-57",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "1467be7a2498802e0e928ff15b53a206",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-12-10-50-07",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-12-10-58-26",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-12-10-28-22",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-12-11-00-24",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-12-10-52-16",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "f0a4af915e2602952728bdd84ba5f5bb",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-12-10-06-10",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-12-10-09-37",
                        "longeval-short-july-20230513-training": "2024-03-12-11-17-17",
                        "longeval-heldout-20230513-training": "2024-03-12-11-13-18",
                        "longeval-long-september-20230513-training": "2024-03-12-11-15-27",
                        "longeval-train-20230513-training": "2024-03-12-11-19-15",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "7aeb6d134efe34265d4bc0d10a744393",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-12-07-17-33",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-12-07-21-00",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-12-07-25-45",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-12-07-29-27",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-12-10-13-17",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-12-10-16-50",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-12-10-26-15",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-12-07-33-04",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-12-07-46-07",
                        "gov-trec-web-2002-20230209-training": "2024-03-12-10-37-15",
                        "gov-trec-web-2003-20230209-training": "2024-03-12-10-39-25",
                        "gov-trec-web-2004-20230209-training": "2024-03-12-10-41-33",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-12-10-43-44",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-12-10-45-46",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-12-10-47-58",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "6406cdef3e742f69c79349454d7b7650",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-12-11-11-20",
                        "disks45-nocr-trec8-20230209-training": "2024-03-12-10-35-20",
                        "disks45-nocr-trec7-20230209-training": "2024-03-12-10-32-58",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-12-08-07-04",
                    },
                },
            },
            "qe-flan-ul2-cot": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "aab25cd1484743d8c517dfc9d43ee1f2",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-12-06-37-28",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-12-06-42-04",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-12-07-13-34",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "0058d5c0edd93628144be7ad5080bdb3",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-12-05-24-20",
                        "vaswani-20230107-training": "2024-03-12-06-49-24",
                        "cranfield-20230107-training": "2024-03-12-05-49-13",
                        "nfcorpus-test-20230107-training": "2024-03-12-06-45-38",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "fddd31d6afa99bd79a80571dd03faa17",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-12-06-23-45",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-12-06-30-44",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-12-05-45-38",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-12-06-34-03",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-12-06-27-14",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "7790edd534f2246a006f7e7baacd449a",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-12-05-28-04",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-12-05-31-40",
                        "longeval-short-july-20230513-training": "2024-03-12-07-04-50",
                        "longeval-heldout-20230513-training": "2024-03-12-06-57-04",
                        "longeval-long-september-20230513-training": "2024-03-12-07-01-01",
                        "longeval-train-20230513-training": "2024-03-12-07-08-41",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "50dba42a54725539960a258684c1f7db",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-12-04-59-29",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-12-05-03-01",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-12-05-06-29",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-12-05-09-47",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-12-05-35-03",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-12-05-38-40",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-12-05-42-03",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-12-05-13-21",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-12-05-16-59",
                        "gov-trec-web-2002-20230209-training": "2024-03-12-06-00-17",
                        "gov-trec-web-2003-20230209-training": "2024-03-12-06-05-21",
                        "gov-trec-web-2004-20230209-training": "2024-03-18-20-10-36",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-12-06-12-33",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-12-06-16-24",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-12-06-20-20",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "4bfa0b1e37e937747c3c8dd8547670e2",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-12-06-53-10",
                        "disks45-nocr-trec8-20230209-training": "2024-03-12-05-56-41",
                        "disks45-nocr-trec7-20230209-training": "2024-03-12-05-52-57",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-12-05-20-39",
                    },
                },
            },
            "qe-gpt3.5-cot": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "32d25d3a75c6258ceecd8f650bf5f55d",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-10-18-45-51",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-10-18-49-22",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-10-19-17-06",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "7e6d1489a65618a78987e7a4e1830a08",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-10-17-31-31",
                        "vaswani-20230107-training": "2024-03-10-18-56-33",
                        "cranfield-20230107-training": "2024-03-10-17-42-13",
                        "nfcorpus-test-20230107-training": "2024-03-10-18-53-00",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "c7b945e6442fdbe6d80f9bad5cb39f5a",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-10-18-32-29",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-10-18-39-13",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-10-17-40-32",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-10-18-42-37",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-10-18-35-54",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "0112c97ed2e28e0ff322bcad90576948",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-10-17-32-46",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-10-17-34-14",
                        "longeval-short-july-20230513-training": "2024-03-10-19-10-03",
                        "longeval-heldout-20230513-training": "2024-03-10-19-03-22",
                        "longeval-long-september-20230513-training": "2024-03-10-19-06-51",
                        "longeval-train-20230513-training": "2024-03-10-19-13-34",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "82b3ccccc34bd196ce1565fe4ee2fc0c",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-10-17-20-21",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-10-17-22-14",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-10-17-23-46",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-10-17-25-13",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-10-17-35-41",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-10-17-37-10",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-10-17-38-57",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-10-17-26-54",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-10-17-28-24",
                        "gov-trec-web-2002-20230209-training": "2024-03-10-18-11-34",
                        "gov-trec-web-2003-20230209-training": "2024-03-10-18-15-02",
                        "gov-trec-web-2004-20230209-training": "2024-03-10-18-18-27",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-10-18-21-41",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-10-18-25-14",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-10-18-28-55",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "7b636c58af4baaa08f474503806ae6d4",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-10-19-00-01",
                        "disks45-nocr-trec8-20230209-training": "2024-03-10-18-10-11",
                        "disks45-nocr-trec7-20230209-training": "2024-03-10-17-43-32",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-10-17-30-14",
                    },
                },
            },
            "qe-gpt3.5-sq-fs": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "8793483c977595724712a6951332bd51",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-03-10-21-11-31",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-03-10-21-14-53",
                        "trec-tip-of-the-tongue-dev-20230607-training": "2024-03-10-21-42-29",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "e80f50688920a6b6b798da594686361a",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-03-10-20-00-03",
                        "vaswani-20230107-training": "2024-03-10-21-21-33",
                        "cranfield-20230107-training": "2024-03-10-20-24-07",
                        "nfcorpus-test-20230107-training": "2024-03-10-21-18-21",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "7a718f02aeebfd4afe7637517c8c9faf",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-03-10-20-57-14",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-03-10-21-04-20",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-03-10-20-20-39",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-03-10-21-08-00",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-03-10-21-00-38",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "516be0356639a85827a74e06e5bd70cc",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-03-10-20-03-26",
                        "argsme-touche-2021-task-1-20230209-training": "2024-03-10-20-06-52",
                        "longeval-short-july-20230513-training": "2024-03-10-21-35-45",
                        "longeval-heldout-20230513-training": "2024-03-10-21-28-33",
                        "longeval-long-september-20230513-training": "2024-03-10-21-32-14",
                        "longeval-train-20230513-training": "2024-03-10-21-39-04",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "d618c8366fd636fc0fdaed6d5237550e",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-03-10-19-36-04",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-03-10-19-39-29",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-03-10-19-42-56",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-03-10-19-46-08",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-03-10-20-10-08",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-03-10-20-13-30",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-03-10-20-17-02",
                        "clueweb12-trec-web-2013-20230107-training": "2024-03-10-19-49-33",
                        "clueweb12-trec-web-2014-20230107-training": "2024-03-10-19-53-03",
                        "gov-trec-web-2002-20230209-training": "2024-03-10-20-36-15",
                        "gov-trec-web-2003-20230209-training": "2024-03-10-20-39-59",
                        "gov-trec-web-2004-20230209-training": "2024-03-10-20-43-27",
                        "gov2-trec-tb-2004-20230209-training": "2024-03-10-20-46-40",
                        "gov2-trec-tb-2005-20230209-training": "2024-03-10-20-49-59",
                        "gov2-trec-tb-2006-20230209-training": "2024-03-10-20-53-41",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "f1aaba145adc4161918f6a8c809dcada",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-03-10-21-24-53",
                        "disks45-nocr-trec8-20230209-training": "2024-03-10-20-32-47",
                        "disks45-nocr-trec7-20230209-training": "2024-03-10-20-29-11",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-03-10-19-56-39",
                    },
                },
            },
        },
        "marcel-gohsen": {
            "query-interpretation": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "0e5fbc02af1872495a2e37f3e2990768",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-24-22-34-40",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-24-22-38-34",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "88657d3bf9af7982c5e03e0c594288ab",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-22-23-06-50",
                        "vaswani-20230107-training": "2024-02-28-15-30-25",
                        "nfcorpus-test-20230107-training": "2024-02-28-15-31-40",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "20d8fa59027461fac4b792eea51863a1",
                    "run_ids": {
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-24-22-31-42",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-23-04-47-37",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-24-22-32-52",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "95f8170a327825eb79280422b2dd85b5",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-22-23-21-20",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-22-23-22-30",
                        "longeval-short-july-20230513-training": "2024-02-23-07-15-45",
                        "longeval-heldout-20230513-training": "2024-02-23-07-14-14",
                        "longeval-long-september-20230513-training": "2024-02-23-07-15-04",
                        "longeval-train-20230513-training": "2024-02-23-07-19-23",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "b5ca99da00426646e6541af91dffa916",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-02-22-23-07-41",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-02-22-23-29-37",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-02-22-23-31-22",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-02-22-23-32-55",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-02-23-04-25-20",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-02-23-04-26-17",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-23-04-27-35",
                        "clueweb12-trec-web-2013-20230107-training": "2024-02-23-04-29-23",
                        "clueweb12-trec-web-2014-20230107-training": "2024-02-23-04-31-19",
                        "gov-trec-web-2002-20230209-training": "2024-02-23-05-05-06",
                        "gov-trec-web-2003-20230209-training": "2024-02-23-05-08-10",
                        "gov-trec-web-2004-20230209-training": "2024-02-23-05-09-53",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-23-05-11-24",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-23-05-13-20",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-23-05-15-32",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "ef3bff5dff970e3e064e3530c0867968",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-24-22-42-50",
                        "disks45-nocr-trec8-20230209-training": "2024-02-23-04-59-49",
                        "disks45-nocr-trec7-20230209-training": "2024-02-23-04-53-54",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-22-23-05-54",
                    },
                },
            },
            "entity-linking": {
                "trec-recent": {
                    "dataset_group": "trec-recent",
                    "md5": "af22310c31d58bbf0137ac3280aa66cf",
                    "run_ids": {
                        "msmarco-passage-trec-dl-2019-judged-20230107-training": "2024-02-22-05-34-17",
                        "msmarco-passage-trec-dl-2020-judged-20230107-training": "2024-02-22-05-39-34",
                    },
                },
                "tiny-test-collections": {
                    "dataset_group": "tiny-test-collections",
                    "md5": "d4c2c24d48c476e868092549541bf977",
                    "run_ids": {
                        "antique-test-20230107-training": "2024-02-21-16-29-52",
                        "vaswani-20230107-training": "2024-02-22-05-59-53",
                        "cranfield-20230107-training": "2024-02-21-22-39-20",
                        "nfcorpus-test-20230107-training": "2024-02-22-05-52-56",
                    },
                },
                "trec-medical": {
                    "dataset_group": "trec-medical",
                    "md5": "a75b38300b97651da95ee02b19bcc39c",
                    "run_ids": {
                        "medline-2004-trec-genomics-2004-20230107-training": "2024-02-22-05-21-04",
                        "medline-2017-trec-pm-2017-20230211-training": "2024-02-22-05-28-20",
                        "cord19-fulltext-trec-covid-20230107-training": "2024-02-21-22-38-29",
                        "medline-2017-trec-pm-2018-20230211-training": "2024-02-22-05-31-55",
                        "medline-2004-trec-genomics-2005-20230107-training": "2024-02-22-05-24-31",
                    },
                },
                "clef-labs": {
                    "dataset_group": "clef-labs",
                    "md5": "c1a872c8eaff45e92c28b008c974d3dd",
                    "run_ids": {
                        "argsme-touche-2020-task-1-20230209-training": "2024-02-21-20-33-45",
                        "argsme-touche-2021-task-1-20230209-training": "2024-02-21-20-34-46",
                        "longeval-short-july-20230513-training": "2024-02-22-05-03-49",
                        "longeval-heldout-20230513-training": "2024-02-22-04-59-59",
                        "longeval-long-september-20230513-training": "2024-02-22-05-02-53",
                        "longeval-train-20230513-training": "2024-02-22-05-05-35",
                    },
                },
                "clueweb": {
                    "dataset_group": "clueweb",
                    "md5": "0d30215c5ae65ef12b9dbe3d52819af1",
                    "run_ids": {
                        "clueweb09-en-trec-web-2009-20230107-training": "2024-02-21-20-42-58",
                        "clueweb09-en-trec-web-2010-20230107-training": "2024-02-21-20-49-58",
                        "clueweb09-en-trec-web-2011-20230107-training": "2024-02-21-22-23-42",
                        "clueweb09-en-trec-web-2012-20230107-training": "2024-02-21-22-25-05",
                        "clueweb12-touche-2020-task-2-20230209-training": "2024-02-21-22-26-58",
                        "clueweb12-touche-2021-task-2-20230209-training": "2024-02-21-22-28-07",
                        "clueweb12-trec-misinfo-2019-20240214-training": "2024-02-21-22-30-48",
                        "clueweb12-trec-web-2013-20230107-training": "2024-02-21-22-32-07",
                        "clueweb12-trec-web-2014-20230107-training": "2024-02-21-22-36-37",
                        "gov-trec-web-2002-20230209-training": "2024-02-21-22-54-51",
                        "gov-trec-web-2003-20230209-training": "2024-02-21-23-16-48",
                        "gov-trec-web-2004-20230209-training": "2024-02-21-23-18-01",
                        "gov2-trec-tb-2004-20230209-training": "2024-02-21-23-18-59",
                        "gov2-trec-tb-2005-20230209-training": "2024-02-21-23-19-48",
                        "gov2-trec-tb-2006-20230209-training": "2024-02-21-23-21-01",
                    },
                },
                "trec-core": {
                    "dataset_group": "trec-core",
                    "md5": "9ecadc8064384bf4f37f0202004c63cf",
                    "run_ids": {
                        "wapo-v2-trec-core-2018-20230107-training": "2024-02-22-06-00-47",
                        "disks45-nocr-trec8-20230209-training": "2024-02-21-22-46-17",
                        "disks45-nocr-trec7-20230209-training": "2024-02-21-22-45-10",
                        "disks45-nocr-trec-robust-2004-20230209-training": "2024-02-21-15-01-26",
                    },
                },
            },
        },
    }
}

QUERY_PROCESSORS_PREFIX = {
    "ir-benchmarks": {
        "qpptk": {
            "all-predictors": "https://zenodo.org/records/10852738/files/qpptk-all-predictors",
            # f"{TIRA_ZENODO_BASE_URL}/query-processors-in-progress/qpptk-all-predictors"
        },
        "salamander": {
            "classify-comparative-queries": (
                "https://zenodo.org/records/10852738/files/salamander-classify-comparative-queries"
            ),
            # f"{TIRA_ZENODO_BASE_URL}/query-processors-in-progress/salamander-classify-comparative-queries"
        },
        "ows": {
            "query-segmentation-hyb-a": "https://zenodo.org/records/10852738/files/ows-query-segmentation-hyb-a",
            # f"{TIRA_ZENODO_BASE_URL}/query-processors-in-progress/ows-query-segmentation-hyb-a"
        },
        "dossier": {
            "pre-retrieval-query-intent": (
                "https://zenodo.org/records/10852738/files/dossier-pre-retrieval-query-intent"
            ),
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/dossier-pre-retrieval-query-intent'
        },
        "tu-dresden-03": {
            "qe-gpt3.5-sq-zs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-gpt3.5-sq-zs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-gpt3.5-sq-zs',
            "qe-gpt3.5-cot": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-gpt3.5-cot",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-gpt3.5-cot',
            "qe-gpt3.5-sq-fs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-gpt3.5-sq-fs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-gpt3.5-sq-fs',
            "qe-llama-sq-zs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-llama-sq-zs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-llama-sq-zs',
            "qe-llama-sq-fs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-llama-sq-fs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-llama-sq-fs',
            "qe-llama-cot": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-llama-cot",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-llama-cot',
            "qe-flan-ul2-sq-zs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-flan-ul2-sq-zs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-flan-ul2-sq-zs',
            "qe-flan-ul2-sq-fs": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-flan-ul2-sq-fs",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-flan-ul2-sq-fs',
            "qe-flan-ul2-cot": "https://zenodo.org/records/10852738/files/tu-dresden-03-qe-flan-ul2-cot",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/tu-dresden-03-qe-flan-ul2-cot',
        },
        "marcel-gohsen": {
            "query-interpretation": "https://zenodo.org/records/10852738/files/marcel-gohsen-query-interpretation",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/marcel-gohsen-query-interpretation',
            "entity-linking": "https://zenodo.org/records/10852738/files/marcel-gohsen-entity-linking",
            # 'https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/query-processors-in-progress/marcel-gohsen-entity-linking'
        },
    }
}

STATIC_DATASET_REDIRECTS = {
    "iranthology-20230618-training": "https://zenodo.org/records/10628640/files/",
    "validation-20231104-training": "https://zenodo.org/records/10628882/files/",
    "training-20231104-training": "https://zenodo.org/records/10628882/files/",
    "jena-topics-small-20240119-training": "https://zenodo.org/records/10628882/files/",
    "leipzig-topics-small-20240119-training": "https://zenodo.org/records/10628882/files/",
    "ir-acl-anthology-20240411-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/",
    "longeval-2023-01-20240423-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-2023-06-20240418-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-2023-08-20240418-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-heldout-20230513-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-train-20230513-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-short-july-20230513-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "longeval-long-september-20230513-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-padua2024/",
    "ir-acl-anthology-20240504-training": f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/",
    "ir-acl-anthology-topics-koeln-20240614-in-progress-test": f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/",
    # ReNeuIr 2024
    # mirror: https://files.webis.de/data-in-production/data-research/tira-zenodo-dump-preparation/reneuir-2024/corpora/
    "dl-top-10-docs-20240701-training": "https://zenodo.org/records/12722918/files/",
    "dl-top-100-docs-20240701-training": "https://zenodo.org/records/12722918/files/",
    "dl-top-1000-docs-20240701-training": "https://zenodo.org/records/12722918/files/",
    "ms-marco-100-queries-20240629-training": "https://zenodo.org/records/12722918/files/",
    "ms-marco-1000-queries-20240629-training": "https://zenodo.org/records/12722918/files/",
    "ms-marco-all-dev-queries-20240629-training": "https://zenodo.org/records/12722918/files/",
    "re-rank-spot-check-20240624-training": "https://zenodo.org/records/12722918/files/",
}

RESOURCE_REDIRECTS = {
    "Passage_ANCE_FirstP_Checkpoint.zip": f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/Passage_ANCE_FirstP_Checkpoint.zip",
    "custom-terrier-token-processing-1.0-SNAPSHOT-jar-with-dependencies.jar": (
        f"{TIRA_ZENODO_BASE_URL}/ir-lab-sose2024/custom-terrier-token-processing-1.0-SNAPSHOT-jar-with-dependencies.jar"
    ),
}

DATASET_ID_REDIRECTS = {
    "longeval-tiny-train-20240315-training": "training-20231104-training",
    "longeval-2023-06-20240422-training": "longeval-2023-06-20240418-training",
    "longeval-2023-08-20240422-training": "longeval-2023-08-20240418-training",
}


def dataset_ir_redirects(dataset_id):
    return DATASET_ID_REDIRECTS.get(dataset_id, dataset_id)


for task in QUERY_PROCESSORS.keys():
    for team in QUERY_PROCESSORS[task].keys():
        if team not in STATIC_REDIRECTS[task]:
            STATIC_REDIRECTS[task][team] = {}

        for system_name in QUERY_PROCESSORS[task][team].keys():
            system = QUERY_PROCESSORS[task][team][system_name]
            if system_name not in STATIC_REDIRECTS[task][team]:
                STATIC_REDIRECTS[task][team][system_name] = {}
            for dataset_group in system.keys():
                for dataset_id, run_id in sorted(list(system[dataset_group]["run_ids"].items())):
                    RUN_ID_TO_SYSTEM[run_id] = system_name
                    STATIC_REDIRECTS[task][team][system_name][dataset_id] = {
                        "run_id": run_id,
                        "urls": [QUERY_PROCESSORS_PREFIX[task][team][system_name] + f"-{dataset_group}.zip"],
                    }

MIRROR_URLS = {}

for task in STATIC_REDIRECTS.keys():
    for team in STATIC_REDIRECTS[task].keys():
        for system_name in STATIC_REDIRECTS[task][team].keys():
            system = STATIC_REDIRECTS[task][team][system_name]
            for dataset_id in system.keys():
                urls = system[dataset_id].get("urls")
                if urls and len(urls) > 0:
                    for url in urls:
                        MIRROR_URLS[url] = [i for i in urls if i != url]


def mirror_url(url):
    mirror_urls = MIRROR_URLS.get(url)
    if mirror_urls and len(mirror_urls) > 0:
        print(f"Switch to mirror {mirror_urls[0]} as due to outage of {url}")
        return mirror_urls[0]
    return url


def mirror_urls_for_run_output(task, team, dataset, run_id):
    system = RUN_ID_TO_SYSTEM.get(run_id, None)
    ret = STATIC_REDIRECTS.get(task, {}).get(team, {}).get(system, {}).get(dataset)
    if ret is None:
        return []
    else:
        return ret["urls"]


def redirects(approach=None, dataset=None, url=None):
    default_ret = {"urls": [url]}
    if url is not None:
        print_license_agreement(url)

        if "/task/" in url and "/user/" in url and "/dataset/" in url and "/download/" in url and ".zip" in url:
            # /task/{task}/user/{team}/dataset/{dataset}/download/{run_id}.zip
            ret = url.split("/task/")[1]
            ret = ret.split("/")
            task, team, dataset, run_id = ret[0], ret[2], ret[4], ret[6].replace(".zip", "")
            system = RUN_ID_TO_SYSTEM.get(run_id, None)
        elif "/data-download/training/" in url or "/data-download/test/" in url:
            dataset_id = url.split("/")[-1].replace(".zip", "")
            dataset_id = DATASET_ID_REDIRECTS.get(dataset_id, dataset_id)
            suffix = "-truths.zip" if "/input-truth/" in url else "-inputs.zip"

            if dataset_id in STATIC_DATASET_REDIRECTS:
                ds_id = (
                    dataset_id if "20230618" in dataset_id else dataset_id.replace("-training", "").replace("-test", "")
                )
                suffix = suffix if "20230618" in dataset_id or suffix != "-truths.zip" else "-truth.zip"
                return {"urls": [STATIC_DATASET_REDIRECTS[dataset_id] + ds_id + suffix + "?download=1"]}
            else:
                return default_ret
        else:
            return default_ret

    else:
        task, team, system = approach.split("/")

    return STATIC_REDIRECTS.get(task, {}).get(team, {}).get(system, {}).get(dataset, default_ret)
