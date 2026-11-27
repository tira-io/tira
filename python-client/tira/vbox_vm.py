#!/usr/bin/env python
"""
tira-cli vbox: create, start, and stop VirtualBox virtual machine images.

This module is fully self-contained: it only depends on the Python standard
library and the `VBoxManage` command line tool that ships with VirtualBox.
It can be wired into the main `tira-cli` by calling `setup_vbox_command`
with an `argparse` subparser, or it can be used as a standalone script:

    python -m tira.vbox_vm create --name tira-worker --iso ./ubuntu.iso
    python -m tira.vbox_vm start --name tira-worker
    python -m tira.vbox_vm stop --name tira-worker
"""

import argparse
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("tira.vbox_vm")

VBOXMANAGE_BIN = "VBoxManage"

DEFAULT_OS_TYPE = "Ubuntu_64"
DEFAULT_MEMORY_MB = 4096
DEFAULT_CPUS = 2
DEFAULT_DISK_MB = 40960
DEFAULT_VRAM_MB = 16


class VBoxCommandError(RuntimeError):
    """Raised when a VBoxManage invocation fails."""


def _require_vboxmanage() -> str:
    """Locate the VBoxManage executable or fail with a helpful message."""
    binary = shutil.which(VBOXMANAGE_BIN)
    if not binary:
        raise VBoxCommandError(
            "Could not find 'VBoxManage' on PATH. Please install VirtualBox "
            "(https://www.virtualbox.org/) and make sure VBoxManage is available."
        )
    return binary


def vboxmanage(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a VBoxManage subcommand and return the completed process."""
    binary = _require_vboxmanage()
    cmd = [binary] + args
    logger.debug("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise VBoxCommandError(f"Command failed ({' '.join(cmd)}):\n{proc.stdout}\n{proc.stderr}".strip())
    return proc


def vm_exists(name: str) -> bool:
    proc = vboxmanage(["list", "vms"], check=True)
    return f'"{name}"' in proc.stdout


def vm_is_running(name: str) -> bool:
    proc = vboxmanage(["list", "runningvms"], check=True)
    return f'"{name}"' in proc.stdout


def wait_for_state(name: str, running: bool, timeout: int = 120) -> bool:
    """Poll until the VM reaches the desired running/stopped state or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if vm_is_running(name) == running:
            return True
        time.sleep(2)
    return False


"""
create: build a new VM, attach disks/media, and register required hardware.
"""


def create_vm(
    name: str,
    iso: Optional[str] = None,
    ova: Optional[str] = None,
    os_type: str = DEFAULT_OS_TYPE,
    memory_mb: int = DEFAULT_MEMORY_MB,
    cpus: int = DEFAULT_CPUS,
    disk_mb: int = DEFAULT_DISK_MB,
    vram_mb: int = DEFAULT_VRAM_MB,
    vm_dir: Optional[str] = None,
    force: bool = False,
    provision_script: Optional[str] = None,
    guest_user: Optional[str] = None,
    guest_password: Optional[str] = None,
    boot_and_provision_timeout: int = 600,
) -> None:
    """Create (or import) a VirtualBox VM that can later be used as a reproducible worker image."""
    if vm_exists(name):
        if not force:
            raise VBoxCommandError(f"A VM named '{name}' already exists. Use --force to delete and recreate it.")
        logger.info("Deleting existing VM '%s' because --force was set.", name)
        if vm_is_running(name):
            vboxmanage(["controlvm", name, "poweroff"], check=False)
            wait_for_state(name, running=False, timeout=60)
        vboxmanage(["unregistervm", name, "--delete"], check=True)

    if ova:
        logger.info("Importing OVA appliance '%s' as VM '%s'.", ova, name)
        import_args = ["import", ova, "--vsys", "0", "--vmname", name]
        if vm_dir:
            import_args += ["--basefolder", vm_dir]
        vboxmanage(import_args, check=True)
    else:
        logger.info("Creating new VM '%s' (os type: %s).", name, os_type)
        create_args = ["createvm", "--name", name, "--ostype", os_type, "--register"]
        if vm_dir:
            create_args += ["--basefolder", vm_dir]
        vboxmanage(create_args, check=True)

        vboxmanage(
            [
                "modifyvm",
                name,
                "--memory",
                str(memory_mb),
                "--cpus",
                str(cpus),
                "--vram",
                str(vram_mb),
                "--nic1",
                "nat",
                "--audio",
                "none",
                "--boot1",
                "dvd",
                "--boot2",
                "disk",
            ],
            check=True,
        )

        vboxmanage(["storagectl", name, "--name", "SATA", "--add", "sata", "--controller", "IntelAhci"], check=True)

        info = vboxmanage(["showvminfo", name, "--machinereadable"], check=True).stdout
        vm_folder = None
        for line in info.splitlines():
            if line.startswith("CfgFile="):
                vm_folder = str(Path(line.split("=", 1)[1].strip('"')).parent)
                break
        disk_path = str(Path(vm_folder or ".") / f"{name}.vdi")

        vboxmanage(["createmedium", "disk", "--filename", disk_path, "--size", str(disk_mb)], check=True)
        vboxmanage(
            [
                "storageattach",
                name,
                "--storagectl",
                "SATA",
                "--port",
                "0",
                "--device",
                "0",
                "--type",
                "hdd",
                "--medium",
                disk_path,
            ],
            check=True,
        )

        if iso:
            logger.info("Attaching install media '%s'.", iso)
            vboxmanage(
                [
                    "storageattach",
                    name,
                    "--storagectl",
                    "SATA",
                    "--port",
                    "1",
                    "--device",
                    "0",
                    "--type",
                    "dvddrive",
                    "--medium",
                    iso,
                ],
                check=True,
            )

    logger.info("VM '%s' created successfully.", name)

    if provision_script:
        logger.info(
            "Booting '%s' headless to run the provisioning script. This requires the OS to already be "
            "installed (e.g., via --ova) and Guest Additions to be present.",
            name,
        )
        start_vm(name, headless=True)
        if not wait_for_state(name, running=True, timeout=60):
            raise VBoxCommandError(f"VM '{name}' did not report as running in time for provisioning.")
        _provision_guest(
            name,
            provision_script,
            guest_user=guest_user,
            guest_password=guest_password,
            timeout=boot_and_provision_timeout,
        )
        logger.info("Provisioning finished, powering '%s' back off.", name)
        stop_vm(name, mode="acpipowerbutton")
        wait_for_state(name, running=False, timeout=120)


def _provision_guest(
    name: str,
    provision_script: str,
    guest_user: Optional[str],
    guest_password: Optional[str],
    timeout: int,
) -> None:
    """Copy the provisioning script into the guest and execute it via VBoxManage guestcontrol."""
    if not guest_user or not guest_password:
        raise VBoxCommandError("--guest-user and --guest-password are required together with --provision-script.")

    script_path = Path(provision_script)
    if not script_path.is_file():
        raise VBoxCommandError(f"Provisioning script not found: {provision_script}")

    guest_target = f"/tmp/{script_path.name}"
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            vboxmanage(
                [
                    "guestcontrol",
                    name,
                    "copyto",
                    "--username",
                    guest_user,
                    "--password",
                    guest_password,
                    str(script_path),
                    guest_target,
                ],
                check=True,
            )
            break
        except VBoxCommandError as exc:
            last_error = exc
            time.sleep(5)
    else:
        raise VBoxCommandError(f"Could not reach guest OS to copy the provisioning script: {last_error}")

    vboxmanage(
        [
            "guestcontrol",
            name,
            "run",
            "--username",
            guest_user,
            "--password",
            guest_password,
            "--",
            "chmod",
            "+x",
            guest_target,
        ],
        check=True,
    )
    logger.info("Executing provisioning script inside the guest...")
    vboxmanage(
        [
            "guestcontrol",
            name,
            "run",
            "--username",
            guest_user,
            "--password",
            guest_password,
            "--",
            "/bin/sh",
            guest_target,
        ],
        check=True,
    )


"""
start / stop: control the lifecycle of an existing VM.
"""


def start_vm(name: str, headless: bool = True, wait: bool = False, timeout: int = 120) -> None:
    if not vm_exists(name):
        raise VBoxCommandError(f"VM '{name}' does not exist. Create it first with 'tira-cli vbox create'.")
    if vm_is_running(name):
        logger.info("VM '%s' is already running.", name)
        return

    vm_type = "headless" if headless else "gui"
    logger.info("Starting VM '%s' (%s).", name, vm_type)
    vboxmanage(["startvm", name, "--type", vm_type], check=True)

    if wait:
        if not wait_for_state(name, running=True, timeout=timeout):
            raise VBoxCommandError(f"VM '{name}' did not reach the running state within {timeout}s.")
    logger.info("VM '%s' started.", name)


def stop_vm(name: str, mode: str = "acpipowerbutton", wait: bool = False, timeout: int = 120) -> None:
    if not vm_exists(name):
        raise VBoxCommandError(f"VM '{name}' does not exist.")
    if not vm_is_running(name):
        logger.info("VM '%s' is already stopped.", name)
        return

    logger.info("Stopping VM '%s' (mode: %s).", name, mode)
    vboxmanage(["controlvm", name, mode], check=True)

    if wait:
        if not wait_for_state(name, running=False, timeout=timeout):
            raise VBoxCommandError(f"VM '{name}' did not reach the stopped state within {timeout}s.")
    logger.info("VM '%s' stopped.", name)


"""
argparse wiring: `setup_vbox_command` is the single entry point tira_cli.py needs to import.
"""


def _add_common_logging_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
        help="Increases the output verbosity. Default is INFO. Can be repeated for more verbose output.",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Disables logging.")


def _cmd_create(args: argparse.Namespace) -> int:
    try:
        create_vm(
            name=args.name,
            iso=args.iso,
            ova=args.ova,
            os_type=args.os_type,
            memory_mb=args.memory,
            cpus=args.cpus,
            disk_mb=args.disk_size,
            vram_mb=args.vram,
            vm_dir=args.vm_dir,
            force=args.force,
            provision_script=args.provision_script,
            guest_user=args.guest_user,
            guest_password=args.guest_password,
            boot_and_provision_timeout=args.provision_timeout,
        )
    except VBoxCommandError as exc:
        logging.critical(str(exc))
        return 1
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    try:
        start_vm(args.name, headless=not args.gui, wait=args.wait, timeout=args.timeout)
    except VBoxCommandError as exc:
        logging.critical(str(exc))
        return 1
    return 0


def _cmd_stop(args: argparse.Namespace) -> int:
    mode = "savestate" if args.save_state else ("poweroff" if args.force else "acpipowerbutton")
    try:
        stop_vm(args.name, mode=mode, wait=args.wait, timeout=args.timeout)
    except VBoxCommandError as exc:
        logging.critical(str(exc))
        return 1
    return 0


def setup_vbox_command(parser: argparse.ArgumentParser) -> None:
    """Register the `vbox` command and its `create`/`start`/`stop` subcommands on `parser`."""
    subparsers = parser.add_subparsers(dest="vbox-sub-command", required=True)

    create_parser = subparsers.add_parser(
        "create", help="Create a VirtualBox VM image with the required software installed."
    )
    create_parser.add_argument("--name", required=True, help="Name of the VirtualBox VM to create.")
    create_parser.add_argument("--iso", help="Path to an OS installation ISO to attach as install media.")
    create_parser.add_argument(
        "--ova", help="Path to an existing .ova/.ovf appliance to import instead of creating a blank VM."
    )
    create_parser.add_argument("--os-type", default=DEFAULT_OS_TYPE, help="VBoxManage ostype (default: %(default)s).")
    create_parser.add_argument(
        "--memory", type=int, default=DEFAULT_MEMORY_MB, help="RAM in MB (default: %(default)s)."
    )
    create_parser.add_argument(
        "--cpus", type=int, default=DEFAULT_CPUS, help="Number of virtual CPUs (default: %(default)s)."
    )
    create_parser.add_argument(
        "--disk-size", type=int, default=DEFAULT_DISK_MB, help="Virtual disk size in MB (default: %(default)s)."
    )
    create_parser.add_argument(
        "--vram", type=int, default=DEFAULT_VRAM_MB, help="Video RAM in MB (default: %(default)s)."
    )
    create_parser.add_argument("--vm-dir", help="Base folder in which the VM should be created/imported.")
    create_parser.add_argument(
        "--force", action="store_true", help="Delete and recreate the VM if one with the same name already exists."
    )
    create_parser.add_argument(
        "--provision-script",
        help="Path to a shell script that is copied into the guest and executed to install required software. "
        "Requires the OS to already be installed (e.g., via --ova) and Guest Additions to be present.",
    )
    create_parser.add_argument("--guest-user", help="Guest OS username used to run --provision-script.")
    create_parser.add_argument("--guest-password", help="Guest OS password used to run --provision-script.")
    create_parser.add_argument(
        "--provision-timeout",
        type=int,
        default=600,
        help="Seconds to wait for the guest OS to become reachable for provisioning (default: %(default)s).",
    )
    _add_common_logging_args(create_parser)
    create_parser.set_defaults(executable=_cmd_create)

    start_parser = subparsers.add_parser("start", help="Start a previously created VirtualBox VM.")
    start_parser.add_argument("--name", required=True, help="Name of the VirtualBox VM to start.")
    start_parser.add_argument("--gui", action="store_true", help="Start with a GUI window instead of headless.")
    start_parser.add_argument("--wait", action="store_true", help="Wait until the VM reports as running.")
    start_parser.add_argument(
        "--timeout", type=int, default=120, help="Seconds to wait for --wait (default: %(default)s)."
    )
    _add_common_logging_args(start_parser)
    start_parser.set_defaults(executable=_cmd_start)

    stop_parser = subparsers.add_parser("stop", help="Stop a running VirtualBox VM.")
    stop_parser.add_argument("--name", required=True, help="Name of the VirtualBox VM to stop.")
    stop_group = stop_parser.add_mutually_exclusive_group()
    stop_group.add_argument(
        "--force", action="store_true", help="Hard power off the VM instead of a graceful ACPI shutdown."
    )
    stop_group.add_argument("--save-state", action="store_true", help="Save the VM's state instead of shutting down.")
    stop_parser.add_argument("--wait", action="store_true", help="Wait until the VM reports as stopped.")
    stop_parser.add_argument(
        "--timeout", type=int, default=120, help="Seconds to wait for --wait (default: %(default)s)."
    )
    _add_common_logging_args(stop_parser)
    stop_parser.set_defaults(executable=_cmd_stop)


def _standalone_main() -> int:
    parser = argparse.ArgumentParser(prog="tira-cli vbox", description=__doc__)
    setup_vbox_command(parser)
    args = parser.parse_args()

    if getattr(args, "quiet", False):
        logging.disable()
    else:
        verbosity_levels = [logging.CRITICAL, logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        verbosity = verbosity_levels[min(3 + getattr(args, "verbose", 0), len(verbosity_levels) - 1)]
        logging.basicConfig(level=verbosity)

    return args.executable(args)


if __name__ == "__main__":
    sys.exit(_standalone_main())
