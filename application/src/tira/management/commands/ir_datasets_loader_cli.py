import os
import django
    
from django.conf import settings
import logging
import time
from contextlib import contextmanager
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.core.cache import cache
import json

from pathlib import Path
from tira.ir_datasets_loader import IrDatasetsLoader

logger = logging.getLogger("tira")


class Command(BaseCommand):
    """Run ir_datasets_loader via cli.
       Loads a dataset by a given ir_datasets ID and maps the data to standardized formats 
       in preparation to full-rank or re-rank operations with PyTerrier

       @param --ir_dataset_id: required, string: the dataset ID as used by ir_datasets 
       @param --output_dataset_path: required, string: the path to the directory where the output will be stored
       @param --output_dataset_truth_path: required, string: the path to the directory where the output will be stored
       @param --include_original {True}: optional, boolean: flag to signal, if the original data should be included
       @param --rerank: optional, string: if used, mapping will be in preparation for re-ranking operations and a path to file 
                        with TREC-run formatted data is required
    """

    def import_dataset_for_fullrank(self, ir_datasets_id: str, output_dataset_path: Path, output_dataset_truth_path: Path, include_original: bool, skip_documents: bool, skip_qrels: bool, skip_duplicate_ids: bool):
        print(f'Task: Full-Rank -> create files: \n documents.jsonl \n queries.jsonl \n qrels.txt \n at {output_dataset_path}/')
        datasets_loader = IrDatasetsLoader()
        datasets_loader.load_dataset_for_fullrank(ir_datasets_id, output_dataset_path, output_dataset_truth_path, include_original, skip_documents = skip_documents, skip_qrels = skip_qrels, skip_duplicate_ids = skip_duplicate_ids)


    def import_dataset_for_rerank(self, ir_datasets_id: str, output_dataset_path: Path, output_dataset_truth_path: Path, include_original: bool, run_file: Path, skip_qrels: bool):
        print(f'Task: Re-Rank -> create files: \n rerank.jsonl \n qrels.txt \n at {output_dataset_path}/')
        datasets_loader = IrDatasetsLoader()
        datasets_loader.load_dataset_for_rerank(ir_datasets_id, output_dataset_path, output_dataset_truth_path, include_original, run_file)


    def contains_all_required_args(self, options):
        if 'input_dataset_directory' in options and options['input_dataset_directory']:
            metadata = json.load(open(options['input_dataset_directory'] + '/metadata.json'))
            options['ir_datasets_id'] = metadata['ir_datasets_id']
    
        return 'ir_datasets_id' in options and options['ir_datasets_id'] \
            and 'output_dataset_path' in options and options['output_dataset_path']

    def handle(self, *args, **options):            
        if not self.contains_all_required_args(options):
            raise ValueError('Could not handle options' + str(options))
            return
        
        truth_path = Path(options['output_dataset_truth_path']) if 'output_dataset_truth_path' in options and options['output_dataset_truth_path'] else None
        
        if options['rerank']:
            self.import_dataset_for_rerank(
                options['ir_datasets_id'],
                Path(options['output_dataset_path']),
                truth_path,
                options['include_original'],
                options['rerank'],
                skip_qrels = options['skip_qrels'],
            )
        else:
            self.import_dataset_for_fullrank(
                options['ir_datasets_id'],
                Path(options['output_dataset_path']),
                truth_path,
                options['include_original'],
                skip_documents = options['skip_documents'],
                skip_qrels = options['skip_qrels'],
                skip_duplicate_ids = options['skip_duplicate_ids'],
                allowlist_path_ids = options['allowlist_path_ids']
            )

    def add_arguments(self, parser):
        parser.add_argument('--ir_datasets_id', default=None, type=str)
        parser.add_argument('--output_dataset_path', default=None, type=Path)
        parser.add_argument('--output_dataset_truth_path', default=None, type=Path)
        parser.add_argument('--include_original', default=True, type=bool)
        parser.add_argument('--skip_documents', default=False, type=bool)
        parser.add_argument('--skip_qrels', default=False, type=bool)
        parser.add_argument('--input_dataset_directory', default=None, type=str)
        parser.add_argument('--skip_duplicate_ids', default=True, type=bool)
        parser.add_argument('--rerank', default=None, type=Path)
        parser.add_argument('--allowlist_path_ids', default=None, type=Path, required=False)

