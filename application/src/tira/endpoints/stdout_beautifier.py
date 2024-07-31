#!/usr/bin/env python3
import logging
import os
import re
from subprocess import PIPE, run

from bs4 import BeautifulSoup

ansi_color_code_regex = re.compile("\\[(\\d)+(;)*(\\d)*m")
aha_exec = os.path.abspath(__file__).replace("stdout_beautifier.py", "aha")

logger = logging.getLogger("tira")


def is_start_of_ansi_code(txt: str, pos: int) -> bool:
    if txt[pos] != "[":
        return False

    matches = ansi_color_code_regex.search(txt[pos : pos + 8])

    return matches is not None and matches.span()[0] == 0


def beautify_ansi_text(txt: str) -> str:
    #    try:
    ret = ""
    for i in range(len(txt)):
        if is_start_of_ansi_code(txt, i):
            ret += "\033["
        else:
            ret += txt[i]
    p = run([aha_exec], stdout=PIPE, input=ret, encoding="utf8")
    ret = p.stdout
    if p.returncode != 0:
        raise ValueError(f"Returncode invalid: {p.returncode}. Got {ret}.")

    soup = BeautifulSoup(ret, "html.parser")
    return "\n\n".join([str(i) for i in soup.select("pre")])


if __name__ == "__main__":
    print(
        beautify_ansi_text(
            """  [[92mo[0m] The file local-copy-of-input-run/run.jsonl is in JSONL format.
  [[92mo[0m] The file training-datasets-truth/clickbait-spoiling/task-2-spoiler-generation-validation-20220924-training/validation.jsonl is in JSONL format.
  [[92mo[0m] Spoiler generations have correct format. Found 800 Here I try to escape </pre><script>window.alert('Assasa')</script>
  [[92mo[0m] Spoiler generations have correct format. Found 800
"""
        )
    )

    print(
        beautify_ansi_text(
            """[0;32m/opt/conda/lib/python3.7/site-packages/requests/adapters.py in [0;36msend[0;34m(self, request, stream, timeout, verify, cert, proxies)
[1;32m    517                 [0;32mraise SSLError[0;34m(e[0;34m, request[0;34m=request[0;34m)[0;34m[0;34m
[1;32m    518 [0;34m
[0;32m--> 519[0;31m             [0;32mraise ConnectionError[0;34m(e[0;34m, request[0;34m=request[0;34m)[0;34m[0;34m
[1;32m    520 [0;34m
[1;32m    521         [0;32mexcept ClosedPoolError [0;32mas e[0;34m:[0;34m[0;34m"""
        )
    )
