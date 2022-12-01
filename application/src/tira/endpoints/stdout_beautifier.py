#!/usr/bin/env python3
import re
from subprocess import run, PIPE
from bs4 import BeautifulSoup
import os
import logging

ansi_color_code_regex = re.compile("\[\\d+m")
aha_exec = os.path.abspath(__file__).replace('stdout_beautifier.py', 'aha')

logger = logging.getLogger('tira')

def is_start_of_ansi_code(txt, pos):
    if txt[pos] != '[':
        return False
    
    matches = ansi_color_code_regex.search(txt[pos: pos+5])
    
    return matches and matches.span()[0] == 0

def beautify_ansi_text(txt):
#    try:
        ret = ''
        for i in range(len(txt)):
            if is_start_of_ansi_code(txt, i):
                ret += '\033['
            else:
                ret += txt[i]
        p = run([aha_exec], stdout=PIPE, input=ret, encoding='utf8')
        ret = p.stdout
        if p.returncode != 0:
            raise ValueError(f'Returncode invalid: {p.returncode}. Got {ret}.')

        ret = BeautifulSoup(ret, 'html.parser')
        return '\n\n'.join([str(i) for i in ret.select('pre')])
#    except Exception as e:
#        print(f'Failed to beautify with {e}. Return original text')
#        logger.warn(f'Failed to beautify with {e}. Return original text', e)
#        
#        return txt

if __name__ == '__main__':
    print(beautify_ansi_text('''  [[92mo[0m] The file local-copy-of-input-run/run.jsonl is in JSONL format.
  [[92mo[0m] The file training-datasets-truth/clickbait-spoiling/task-2-spoiler-generation-validation-20220924-training/validation.jsonl is in JSONL format.
  [[92mo[0m] Spoiler generations have correct format. Found 800 Here I try to escape </pre><script>window.alert('Assasa')</script>
  [[92mo[0m] Spoiler generations have correct format. Found 800
'''))

