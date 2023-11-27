from django.test import TestCase
from utils_for_testing import method_for_url_pattern, mock_request
import json

url = 'api/snippets-for-tirex-components'
snippet_function = method_for_url_pattern(url)


class TestSnippetGenerationForSingleComponents(TestCase):

    def test_for_single_query_component_hyb_i(self):
        # Arrange
        expected_snippet = '''dataset = pt.get_dataset("irds:disks45/nocr/trec-robust-2004")
topics = dataset.get_topics(variant='title')
tira.pt.transform_queries('ir-benchmarks/ows/query-segmentation-hyb-i', dataset)'''
        request = mock_request('', url)
        request.GET['components'] = 'ir-benchmarks/ows/query-segmentation-hyb-i'

        # Act
        actual = snippet_function(request)
        actual_json = json.loads(actual.content.decode())

        self.assertEquals(0, actual_json['status'])
        self.assertEquals(expected_snippet, actual_json['context']['snippet'])

    def test_for_single_query_component_hyb_b(self):
        # Arrange
        request = mock_request('', url)
        request.GET['components'] = 'ir-benchmarks/ows/query-segmentation-hyb-b'

        # Act
        actual = snippet_function(request)

        # TODO: Add assertions

    def test_for_single_document_processor_bce_fo(self):
        # Arrange
        request = mock_request('', url)
        request.GET['components'] = 'ir-benchmarks/ows/bce-fo'

        # Act
        actual = snippet_function(request)

        # TODO: Add assertions
        # Should contain something like pt.transform_documents('ir-benchmarks/ows/bce-fo')
