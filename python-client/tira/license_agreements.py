def print_license_agreement(url):
    if not url:
        return
    if (
        url
        and "longeval" in url
        or "leipzig-topics-small-20240119" in url
        or "jena-topics-20231026-test" in url
        or "jena-topics-small-20240119-training" in url
        or "leipzig-topics-20231025-test" in url
        or "training-20231104-training" in url
        or "validation-20231104-training" in url
    ):
        print(
            'The download is derived from The LongEval Dataset under the "Qwant LongEval'
            ' Attribution-NonCommercial-ShareAlike License". Hence, the download is also under this License. By using'
            " it, you agree to the terms of this license. Please find details at:"
            " https://lindat.mff.cuni.cz/repository/xmlui/page/Qwant_LongEval_BY-NC-SA_License"
        )
