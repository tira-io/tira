import configparser
import os
from typing import Optional, Tuple

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from django.conf import settings

from tira_app import model as modeldb

_aws_access_key_id: "Optional[str]" = None
_aws_secret_access_key: "Optional[str]" = None
_use_https: bool = True
_endpoint_url: "Optional[str]" = None

DO_NOT_USE_S3 = str(settings.S3_BUCKET).lower() == "none"

_s3_config_file = os.path.expanduser(settings.S3_CONFIG)
if not os.path.exists(_s3_config_file):
    raise ValueError(f"Config file does not exist: {_s3_config_file}")


class S3Database:
    def read_credentials(self) -> Tuple:
        if DO_NOT_USE_S3:
            raise ValueError("foo")
        config = configparser.ConfigParser()
        global _s3_config_file
        config.read(_s3_config_file)

        section = "default"
        aws_access_key_id = config[section]["access_key"]
        aws_secret_access_key = config[section]["secret_key"]
        use_https = config[section].getboolean("use_https", True)
        protocol = "https" if use_https else "http"
        endpoint_url = f"{protocol}://{config[section]['host_base']}"

        return aws_access_key_id, aws_secret_access_key, use_https, endpoint_url

    def s3_client(self) -> BaseClient:
        global _aws_access_key_id
        global _aws_secret_access_key
        global _use_https
        global _endpoint_url

        if not _aws_access_key_id:
            _aws_access_key_id, _aws_secret_access_key, _use_https, _endpoint_url = self.read_credentials()

        return boto3.client(
            "s3",
            aws_access_key_id=_aws_access_key_id,
            aws_secret_access_key=_aws_secret_access_key,
            endpoint_url=_endpoint_url,
            use_ssl=_use_https,
        )

    def upload_mirrored_resource(self, mirrored_resource: modeldb.MirroredResource) -> None:
        self.s3_client().upload_file(
            mirrored_resource.get_path_in_file_system(), settings.S3_BUCKET, mirrored_resource.md5_sum
        )

    def read_mirrored_resource(self, mirrored_resource: modeldb.MirroredResource) -> StreamingBody:
        response = self.s3_client().get_object(Bucket=settings.S3_BUCKET, Key=mirrored_resource.md5_sum)
        return response["Body"]

    def s3_file_exists(self, mirrored_resource: modeldb.MirroredResource) -> bool:
        http_code, content_length = self.s3_file_head(mirrored_resource)
        return http_code == 200 and int(mirrored_resource.size) == int(content_length)

    def s3_file_head(self, mirrored_resource: modeldb.MirroredResource) -> Tuple:
        s3 = self.s3_client()

        try:
            ret = s3.head_object(Bucket=settings.S3_BUCKET, Key=mirrored_resource.md5_sum)["ResponseMetadata"]
            return ret["HTTPStatusCode"], ret["HTTPHeaders"]["content-length"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return ("404", 0)
            else:
                raise  # Some other error (permissions, etc.)


def fail_if_target_bucket_does_not_exist() -> None:
    s3 = S3Database().s3_client()
    buckets = [i["Name"] for i in s3.list_buckets()["Buckets"]]
    if settings.S3_BUCKET not in buckets:
        raise ValueError(
            f"Bucket {settings.S3_BUCKET} does not exist. Have {buckets}. Create with something like s3cmd mb s3://{settings.S3_BUCKET}."
        )


if not DO_NOT_USE_S3:
    fail_if_target_bucket_does_not_exist()
