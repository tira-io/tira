import unittest

from tira.local_client import Client


def retrieval_submission(queries):
    tira = Client("tests/resources/")
    run = tira.trectools.from_submission("ir-benchmarks/tira-ir-starters/retriever", "d1")

    return [
        {"qid": i["query"], "docno": i["docid"], "score": i["score"]}
        for _, i in run.run_data.iterrows()
        if i["query"] in queries
    ]


class TestTrecToolsFromRetrieverSubmissionLoaderTest(unittest.TestCase):
    def test_for_multiple_queries(self):
        expected = [
            {"qid": "1", "docno": "doc-1", "score": 10},
            {"qid": "1", "docno": "doc-2", "score": 9},
            {"qid": "3", "docno": "doc-3", "score": 1},
        ]

        actual = retrieval_submission(["1", "3"])

        self.assertEqual(len(actual), 3)
        self.assertEqual(actual[0], expected[0])
        self.assertEqual(actual[1], expected[1])
        self.assertEqual(actual[2], expected[2])
