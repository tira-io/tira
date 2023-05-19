def register_dataset_from_re_rank_file(ir_dataset_id, df_re_rank, original_ir_datasets_id=None):
    """
    Load a dynamic ir_datasets integration from a given re_rank_file.
    The dataset will be registered for the id ir_dataset_id.
    The original_ir_datasets_id is used to infer the class of documents, qrels, and queries.
    """
    import ir_datasets
    from ir_datasets.datasets.base import Dataset
    original_dataset = ir_datasets.load(original_ir_datasets_id) if original_ir_datasets_id else None

    docs = __docs(df_re_rank, original_dataset)
    queries = __queries(df_re_rank, original_dataset)
    qrels = __qrels(df_re_rank, original_dataset)
    scoreddocs = __scored_docs(df_re_rank, original_dataset)

    dataset = Dataset(docs, queries, qrels, scoreddocs)
    ir_datasets.registry.register(ir_dataset_id, dataset)

    __check_registration_was_successful(ir_dataset_id)


def __docs(df, original_dataset):
    print(df.iloc[0].keys())
    fields = df.iloc[0]['original_document'].keys()

    for _, query_doc_pair in df.iterrows():
        pass

    return None


def __queries(df, original_dataset):
    qids = set()

    for _, query_doc_pair in df.iterrows():
        pass

    return None


def __qrels(path_to_re_rank_file, original_dataset):
    return original_dataset.get_qrels() if original_dataset else None


def __scored_docs(path_to_re_rank_file, original_dataset):
    return None


def __document_class(fields):
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

