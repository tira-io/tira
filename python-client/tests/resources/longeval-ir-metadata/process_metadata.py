from repro_eval.metadata import MetadataHandler

mh = MetadataHandler(metadata_path='ir-metadata.yml', run_path=None)
print(mh.get_metadata())
