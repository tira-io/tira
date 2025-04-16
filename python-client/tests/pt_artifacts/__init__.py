def load_artifact(url):
    import pyterrier as pt

    return pt.Artifact.from_url(url)
