def register_dataset_from_re_rank_file(ir_dataset_id, path_to_re_rank_file, original_ir_datasets_id=None):
    """
    """
    import ir_datasets
    from ir_datasets.datasets.base import Dataset
    original_dataset = ir_datasets.load(original_dataset) if original_dataset else None

    docs = __docs(path_to_re_rank_file, original_dataset)
    queries = __queries(path_to_re_rank_file, original_dataset)
    qrels = __qrels(path_to_re_rank_file, original_dataset)
    scored_docs = __scored_docs(path_to_re_rank_file, original_dataset)

    dataset = Dataset(docs, queries, qrels, )
    ir_datasets.registry.register(ir_dataset_id, dataset, qrels)

    __check_registration_was_successful(ir_dataset_id)


def __docs(path_to_re_rank_file, original_dataset):
    return None


def __queries(path_to_re_rank_file, original_dataset):
    return None


def __qrels(path_to_re_rank_file, original_dataset):
    return None


def __scored_docs(path_to_re_rank_file, original_dataset):
    return None


def __create_document_class(fields):
    """
    Given the passed fields, this method creates a ir-datasets class for a document that has this fields.
    I.e., if the fields are [x, y, z], the method should return a class with fields x, y, and z.
    """
    pass


def __create_query_class(fields):
    """
    Given the passed fields, this method creates a ir-datasets class for a query that has this fields.
    I.e., if the fields are [x, y, z], the method should return a class with fields x, y, and z.
    """
    pass


def __check_registration_was_successful(ir_dataset_id):
    import ir_datasets
    dataset = ir_datasets.load(ir_dataset_id)

    assert dataset.has_docs(), "dataset has no documents"
    assert dataset.has_queries(), "dataset has no queries"
    assert dataset.has_qrels(), "dataset has no qrels"
    assert dataset.has_scored_docs(), "dataset has no scored_docs"

