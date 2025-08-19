from pathlib import Path
from typing import TYPE_CHECKING

from ...check_format import _fmt, fmt_message, lines_if_valid
from ...rest_api_client import Client as RestClient
from ...tira_run import guess_vm_id_of_user

if TYPE_CHECKING:
    from typing import Optional

    from ...tira_client import TiraClient


def __guess_system_details(directory: "Path", system: "Optional[str]") -> "Optional[dict[str, str]]":
    if system is not None:
        return {"tag": system}

    lines = []
    try:
        lines = lines_if_valid(directory, "ir_metadata")
    except ValueError:
        pass

    for line in lines:
        if (
            line
            and "content" in line
            and "tag" in line["content"]
            and line["content"]["tag"]
            and isinstance(line["content"]["tag"], str)
        ):
            ret = {"tag": line["content"]["tag"]}
            if "research goal" in line["content"] and "description" in line["content"]["research goal"]:
                ret["description"] = line["content"]["research goal"]["description"]
            return ret
    return None


def upload_command(dataset: str, directory: Path, dry_run: bool, system: "Optional[str]", **kwargs) -> int:
    client: "TiraClient" = RestClient()
    vm_id = None
    default_task = None
    systeminfo: "Optional[dict[str, str]]" = None
    if client.api_key_is_valid():
        systeminfo = __guess_system_details(directory, system)
        dataset_info = client.get_dataset(dataset=dataset)
        default_task = dataset_info["default_task"]
        vm_id = guess_vm_id_of_user(default_task, client)
        if systeminfo is None:
            print(
                fmt_message(
                    "Please specify the name of your system. Either:"
                    + "\n\n\tIncorporate the tag into your ir-metadata (see https://ir-metadata.org),"
                    + "\n\n\tor, pass --system to tira-cli upload",
                    _fmt.ERROR,
                )
            )
            return 1

    resp = client.upload_run_anonymous(directory, dataset, dry_run, verbose=systeminfo is None and not vm_id)
    if not resp or "uuid" not in resp or not resp["uuid"]:
        return 1

    if systeminfo is None or not vm_id:
        # only anonymous submissions
        return 0
    else:
        print("\nI upload the metadata for the submission...")
        resp = client.claim_ownership(
            resp["uuid"],
            vm_id,
            systeminfo["tag"],
            systeminfo.get("description", "todo: Add a description"),
            default_task,
        )
        if "status" not in resp or "0" != resp["status"]:
            print(fmt_message(f"There was an error with the upload: {resp}.\n\nPlease try again...", _fmt.ERROR))
            return 1
        print(
            "\t"
            + fmt_message(
                f"Done. Your run is available as {systeminfo['tag']} at:\n\thttps://www.tira.io/submit/{default_task}/user/{vm_id}/upload-submission",
                _fmt.OK,
            )
        )
        return 0
