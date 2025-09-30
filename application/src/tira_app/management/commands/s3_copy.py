from django.core.management.base import BaseCommand
from tqdm import tqdm

from tira_app import model as modeldb
from tira_app.data.S3Database import S3Database


class Command(BaseCommand):
    help = "Copy all mirrors S3"

    def handle(self, *args, **options):
        s3_db = S3Database()
        to_upload = []
        for i in modeldb.MirroredResource.objects.all():
            if not s3_db.s3_file_exists(i):
                to_upload.extend([i])

        for i in tqdm(to_upload, "Upload"):
            s3_db.upload_mirrored_resource(i)
