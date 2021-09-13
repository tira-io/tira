from datetime import datetime
import logging

from .proto import TiraClientWebMessages_pb2 as modelpb

logger = logging.getLogger("tira")


def get_tira_id():
    dt = datetime.now()
    return dt.strftime("%Y-%m-%d-%H-%M-%S")


def auto_reviewer(review_path, run_id):
    """ Do standard checks for reviews so we do not need to wait for a reviewer to check for:
     - failed runs (
     """
    review_file = review_path / "run-review.bin"
    review = modelpb.RunReview()

    if review_file.exists():  # TODO this will throw if the file is corrupt. Let it throw to not overwrite files.
        try:
            review.ParseFromString(open(review_file, "rb").read())
            return review
        except Exception as e:
            logger.exception(f"review file: {review_file} exists but is corrupted with {e}")
            raise FileExistsError(f"review file: {review_file} exists but is corrupted with {e}")

    review.reviewerId = 'tira'
    review.reviewDate = str(datetime.utcnow())
    review.hasWarnings = False
    review.hasErrors = False
    review.hasNoErrors = False
    review.blinded = True
    review.runId = run_id

    try:
        if not (review_path / "run.bin").exists():  # No Run file
            review.comment = "Internal Error: No run definition recorded. Please contact the support."
            review.hasErrors = True
            review.hasNoErrors = False
            review.blinded = False

        if not (review_path / "output").exists():  # No Output directory
            review.comment = "No Output was produced"
            review.hasErrors = True
            review.hasNoErrors = False
            review.blinded = True
            review.missingOutput = True
            review.hasErrorOutput = True

    except Exception as e:
        review_path.mkdir(parents=True, exist_ok=True)
        review.reviewerId = 'tira'
        review.comment = f"Internal Error: {e}. Please contact the support."
        review.hasErrors = True
        review.hasNoErrors = False
        review.blinded = False

    return review
