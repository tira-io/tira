#!/usr/bin/env python
import argparse
from tira.rest_api_client import Client as RestClient
import os
import shutil
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .tira_client import TiraClient


def parse_args():
    parser = argparse.ArgumentParser(prog='tira-cli')
    
    parser.add_argument('-v', '--verbose', required=False, default=False, action='store_true')
    subparsers = parser.add_subparsers(dest='command')
    parser_download = subparsers.add_parser('download', help='Download runs or datasets from TIRA.io')
    parser_download.add_argument('--approach', required=False, default=None, help='Download the outputs of the specified approach. Usage: --approach <task-id>/<user-id>/<approach-name>')
    parser_download.add_argument('--dataset', required=True, help='The dataset.')
    
    parser_upload = subparsers.add_parser('upload', help='Upload runs or datasets to TIRA.io')

    parser_login = subparsers.add_parser('login', help='Login your TIRA client to the tira server.')
    parser_login.add_argument('--token', required=True, default=None, help='The token to login to the server.')

    args = parser.parse_args()

    return args


def download_run(client, approach, dataset):
    help()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    client: "TiraClient" = RestClient()

    if args.command == 'download':
        if args.approach is not None:
            print(client.get_run_output(args.approach, args.dataset))
        else:
            print(client.download_dataset(None, args.dataset))
    if args.command == 'login':
        client.login(args.token)
