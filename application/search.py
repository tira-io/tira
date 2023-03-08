import re
from abc import ABC, abstractmethod
import locale
import logging

from django.conf import settings

from chatnoir_search.types import *

class SerpContext:
    def __init__(self, query_string: str, ):
        self._query_string = query_string

    def to_dict(self, results=True, meta=True, extended_meta=False):
        d = {}
        if meta or extended_meta:
            d['meta'] = self.meta
        if extended_meta:
            d['meta'].update(self.meta_extended)
        if results:
            d['results'] = self.results

        return d

    # noinspection DuplicatedCode,PyProtectedMember
    @property
    def results(self):
        """
        List of search results.

        Entries in this list contain all available fields, independent of the current search mode,
        hence it should not be used as an API response. Use :attr:`results_filtered` instead.
        """

        results = []
        for i in range(10):
            result = {
                'index': '0',
                'trec_id': str(i),
                'score': i,
                'cache_uri': '?index=cw22&uuid=mC8VAylgVOCX_60h9sXS0Q',
                'title': 'Title ' + str(i),
                'snippet':'Title ' + str(i),
                "target_hostname":"en.wikipedia.org",
                "crawl_date":"2022-08-24T14:09:12",
                'content_type': None,
                'lang': 'en',
                'explanation': None
            }

            results.append(result)

        return results

    @property
    def meta(self):
        return {'indices': [{"id":"0","name":"Topic 0","selected":True}], 'resultsTo': 10, 'resultsFrom': 0, 'totalResults': 1000}

    @property
    def meta_extended(self):
        return {'indices': [{"id":"0","name":"Topic 0","selected":True}], 'resultsTo': 10, 'resultsFrom': 0, 'totalResults': 1000}

    def _index_name_to_shorthand(self, index_name):
        """
        Inversely resolve internal index name to defined shorthand name.

        :param index_name: internal index name
        :return: shorthand or unmodified index name if not found
        """
        for i, v in self.search.selected_indices.items():
            if v['index'] == index_name:
                return i
        return index_name

    @serp_api_meta
    def query_time(self):
        """Query time in milliseconds."""
        return 0

    @serp_api_meta
    def total_results(self):
        """Total hits found for the query."""
        return 1000

    @serp_api_meta
    def indices(self):
        """List of searched index IDs."""
        return ['0', '1', '2', '3']

    @serp_api_meta_extended
    def indices_(self):
        """List of dicts with index IDs and names and whether they were active for this search."""
        all_indices = self.search.allowed_indices
        selected_indices = self.search.selected_indices
        return [dict(id=k, name=v.get('display_name'), selected=k in selected_indices)
                for k, v in all_indices.items()]

    @serp_api_meta_extended
    def query_string(self):
        return self._query_string

    @serp_api_meta_extended
    def results_from(self):
        return 0

    @serp_api_meta_extended
    def results_to(self):
        return 10

    @serp_api_meta_extended
    def page_size(self):
        return 10

    @serp_api_meta_extended
    def max_page(self):
        return 100

    @serp_api_meta_extended
    def explain(self):
        return False

    @serp_api_meta_extended
    def terminated_early(self):
        return False


class SearchBase(ABC):
    SEARCH_VERSION = None

    def __init__(self, indices=None, search_from=0, num_results=10, explain=False):
        if indices is not None and type(indices) not in (list, tuple, set):
            raise TypeError('indices must be a list')

        if indices is None:
            indices = {settings.SEARCH_DEFAULT_INDICES[self.SEARCH_VERSION]}
        self._indices_unvalidated = set(indices)

        self.search_language = 'en'
        self.num_results = max(1, num_results)
        self.search_from = max(0, min(search_from, 10000 - self.num_results))
        self.explain = explain
        self.minimal_response = False

        self.query_logger = logging.getLogger(f'query_log.{self.__class__.__name__}')
        self.query_logger.setLevel(logging.INFO)

    @property
    def allowed_indices(self):
        return {"0": {"id":"cw09","name":"ClueWeb09","selected":True}}

    @property
    def selected_indices(self):
        return {"0": {"id":"cw09","name":"ClueWeb09","selected":True}}

    def log_query(self, query, extra):
        pass

    @abstractmethod
    def search(self, query):
        """
        Run a search based on given search fields.

        :param query: search query as string
        :return: :class:``serp.SerpContext`` with result
        """
        pass

    def get_snippet(self, hit, fields, max_len):
        return ''


class SimpleSearch(SearchBase):
    def __init__(self, indices=None, search_from=0, num_results=10, explain=False):
        super().__init__(indices, search_from, num_results, explain)
        settings.SEARCH_INDICES = {str(i): {'index': 'Topic ' + str(i), 'warc_index': '', 'warc_bucket': '', 'warc_uuid_prefix': '', 'display_name': '', 'compat_search_versions': [1], 'default': i==0} for i in range(1000)}

    def search(self, query):
        return SerpContext(query)

class PhraseSearch(SimpleSearch):
    pass

