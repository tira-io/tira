from datetime import datetime as dt
from datetime import timezone
import logging

from .proto import TiraClientWebMessages_pb2 as modelpb
from django.conf import settings


logger = logging.getLogger("tira")


class TiraModelWriteError(Exception):
    pass


class TiraModelIntegrityError(Exception):
    pass


def get_tira_id():
    return dt.now().strftime("%Y-%m-%d-%H-%M-%S")


def get_today_timestamp():
    return dt.now().strftime("%Y%m%d")


def now():
    return dt.now(timezone.utc).strftime("%a %b %d %X %Z %Y")


def extract_year_from_dataset_id(dataset_id: str) -> str:
    try:
        splits = dataset_id.split("-")
        return splits[-3] if len(splits) > 3 and (1990 <= int(splits[-3])) else ""
    except IndexError:
        return ""
    except ValueError:
        return ""


def reroute_host(hostname):
    """ If we use a local deployment and use a local (mock) host, we need to change all hostnames to localhost.
    Otherwise we may contact the real vm-hosts while developing.
      """
    return 'localhost' if settings.GRPC_HOST == 'local' else hostname


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
    review.reviewDate = str(dt.utcnow())
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
