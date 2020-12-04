#!/usr/bin/env python
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Nikolay Kolyada
"""

from concurrent import futures
import grpc
# from grpc import aio
import logging
from logging.config import fileConfig
import subprocess
import re

from proto import tira_host_pb2, tira_host_pb2_grpc


test_output = """
[ERROR] /mnt/nfs/tira/data/virtual-machine-templates not found, stored in _CONFIG_FILE_tira_vm_dir! 
[INFO]  Settings: debug=true, unittests=true
[DEBUG] Each needed tool (ssh sed) is installed.
[INFO]  tira version: 0481adf4042be4039e67611a2dd6c80b
[DEBUG] Parsed arguments: 
# arguments = ['vm-info', 'nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit']
# script args=['nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit']
cmd='vm_info'
script='vm-info'
args='nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit'
minarg_count=1
has_minarg_count=true

[DEBUG] Each needed tool (VBoxManage timeout) is installed.
[INFO]  Information about local vm nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit...
Name:                        nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit
Groups:                      /
Guest OS:                    Ubuntu (64-bit)
UUID:                        51f2cc3f-7f31-4d32-920f-920d2d8129a3
Config file:                 /home/tira/VirtualBox VMs/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit.vbox
Snapshot folder:             /home/tira/VirtualBox VMs/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit/Snapshots
Log folder:                  /home/tira/VirtualBox VMs/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit/Logs
Hardware UUID:               51f2cc3f-7f31-4d32-920f-920d2d8129a3
Memory size                  8096MB
Page Fusion:                 disabled
VRAM size:                   16MB
CPU exec cap:                100%
HPET:                        disabled
CPUProfile:                  host
Chipset:                     piix3
Firmware:                    BIOS
Number of CPUs:              2
PAE:                         disabled
Long Mode:                   enabled
Triple Fault Reset:          disabled
APIC:                        enabled
X2APIC:                      enabled
Nested VT-x/AMD-V:           disabled
CPUID Portability Level:     0
CPUID overrides:             None
Boot menu mode:              message and menu
Boot Device 1:               Floppy
Boot Device 2:               DVD
Boot Device 3:               HardDisk
Boot Device 4:               Not Assigned
ACPI:                        enabled
IOAPIC:                      enabled
BIOS APIC mode:              APIC
Time offset:                 0ms
RTC:                         UTC
Hardware Virtualization:     enabled
Nested Paging:               enabled
Large Pages:                 disabled
VT-x VPID:                   enabled
VT-x Unrestricted Exec.:     enabled
Paravirt. Provider:          Default
Effective Paravirt. Prov.:   KVM
State:                       running (since 2020-12-03T17:58:49.588000000)
Graphics Controller:         VBoxVGA
Monitor count:               1
3D Acceleration:             disabled
2D Video Acceleration:       disabled
Teleporter Enabled:          disabled
Teleporter Port:             0
Teleporter Address:          
Teleporter Password:         
Tracing Enabled:             disabled
Allow Tracing to Access VM:  disabled
Tracing Configuration:       
Autostart Enabled:           disabled
Autostart Delay:             0
Default Frontend:            
VM process priority:         default
Storage Controller Name (0):            IDE
Storage Controller Type (0):            PIIX4
Storage Controller Instance Number (0): 0
Storage Controller Max Port Count (0):  2
Storage Controller Port Count (0):      2
Storage Controller Bootable (0):        on
Storage Controller Name (1):            SATA
Storage Controller Type (1):            IntelAhci
Storage Controller Instance Number (1): 0
Storage Controller Max Port Count (1):  30
Storage Controller Port Count (1):      1
Storage Controller Bootable (1):        on
IDE (1, 0): Empty
SATA (0, 0): /home/tira/VirtualBox VMs/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit/tira-ubuntu-18-04-4-desktop-64bit-disk001.vmdk (UUID: fc7a9ab7-d127-4373-82b3-f3e15de4082a)
NIC 1:                       MAC: 0800276D6423, Attachment: Host-only Interface 'vboxnet4', Cable connected: on, Trace: off (file: none), Type: 82540EM, Reported speed: 0 Mbps, Boot priority: 0, Promisc Policy: deny, Bandwidth group: none
NIC 2:                       disabled
NIC 3:                       disabled
NIC 4:                       disabled
NIC 5:                       disabled
NIC 6:                       disabled
NIC 7:                       disabled
NIC 8:                       disabled
Pointing Device:             USB Tablet
Keyboard Device:             PS/2 Keyboard
UART 1:                      disabled
UART 2:                      disabled
UART 3:                      disabled
UART 4:                      disabled
LPT 1:                       disabled
LPT 2:                       disabled
Audio:                       enabled (Driver: ALSA, Controller: AC97, Codec: AD1980)
Audio playback:              enabled
Audio capture:               disabled
Clipboard Mode:              disabled
Drag and drop Mode:          disabled
Session name:                headless
Video mode:                  1024x768x32 at 0,0 enabled
VRDE:                        enabled (Address 0.0.0.0, Ports 55504, MultiConn: off, ReuseSingleConn: off, Authentication type: external)
VRDE port:                   55504
Video redirection:           disabled
VRDE property               : TCP/Ports  = "55504"
VRDE property               : TCP/Address = <not set>
VRDE property               : VideoChannel/Enabled = <not set>
VRDE property               : VideoChannel/Quality = <not set>
VRDE property               : VideoChannel/DownscaleProtection = <not set>
VRDE property               : Client/DisableDisplay = <not set>
VRDE property               : Client/DisableInput = <not set>
VRDE property               : Client/DisableAudio = <not set>
VRDE property               : Client/DisableUSB = <not set>
VRDE property               : Client/DisableClipboard = <not set>
VRDE property               : Client/DisableUpstreamAudio = <not set>
VRDE property               : Client/DisableRDPDR = <not set>
VRDE property               : H3DRedirect/Enabled = <not set>
VRDE property               : Security/Method = <not set>
VRDE property               : Security/ServerCertificate = <not set>
VRDE property               : Security/ServerPrivateKey = <not set>
VRDE property               : Security/CACertificate = <not set>
VRDE property               : Audio/RateCorrectionMode = <not set>
VRDE property               : Audio/LogPath = <not set>
OHCI USB:                    enabled
EHCI USB:                    enabled
xHCI USB:                    disabled

USB Device Filters:

<none>

Available remote USB devices:

<none>

Currently Attached USB Devices:

<none>

Bandwidth groups:  <none>

Shared folders:

Name: 'training-datasets', Host path: '/mnt/nfs/tira/data/datasets/training-datasets' (machine mapping), readonly, auto-mount

VRDE Connection:             not active
Clients so far:              0

Capturing:                   not active
Capture audio:               not active
Capture screens:             0
Capture file:                /home/tira/VirtualBox VMs/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit/nik-test-u18-04-tira-ubuntu-18-04-desktop-64bit.webm
Capture dimensions:          1024x768
Capture rate:                512kbps
Capture FPS:                 25kbps
Capture options:             ac_enabled=false

Guest:

Configured memory balloon size: 0MB
OS type:                     Linux26_64
Additions run level:         2
Additions version:           6.1.10_Ubuntu r138449

Guest Facilities:

Facility "VirtualBox Base Driver": active/running (last update: 2020/12/03 17:59:17 UTC)
Facility "VirtualBox System Service": active/running (last update: 2020/12/03 17:59:31 UTC)
Facility "Seamless Mode": not active (last update: 2020/12/03 17:59:17 UTC)
Facility "Graphics Mode": active/running (last update: 2020/12/03 18:00:09 UTC)


"""

def run_tira_script(script_name, *args):
    p = subprocess.Popen("tira " + script_name + " " + " ".join([a for a in args]), shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    response = tira_host_pb2.Response(output=output)
    return response


def run_shell_command(command_string):
    p = subprocess.Popen(command_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.communicate()[0].decode('utf-8')
    response = tira_host_pb2.Response(output=output)
    return response


class TiraHostService(tira_host_pb2_grpc.TiraHostService):
    def test(self, input, context):
        return tira_host_pb2.Output(text="Server received: " + input.text)

    def shell_command(self, command):
        return run_shell_command(command)

    def vm_backup(self, request, context):
        return run_tira_script("vm-backup", request.vmName)

    # todo: for all methods, return status of the command, save the output of the tira command to the file
    def vm_create(self, request, context):
        return run_tira_script("vm-create", request.ovaFile, request.userName)

    def vm_delete(self, request, context):
        return run_tira_script("vm-delete", request.vmName)

    def vm_info(self, request, context):
        response = run_tira_script("vm-info", request.vmName)
        response_vm_info = tira_host_pb2.ResponseVmInfo()
        for line in response.output.split("\n"):
            if line.startswith("Guest OS:"):
                response_vm_info.guestOs = line.split(": ")[1].strip()
            elif line.startswith("Memory size"):
                response_vm_info.memorySize = line.split()[2].strip()
            elif line.startswith("Number of CPUs:"):
                response_vm_info.numberOfCpus = line.split(": ")[1].strip()
            elif line.startswith("State:"):
                response_vm_info.state = re.sub(".\\d+\\)", ")", line.split(": ")[1].strip())

        return response_vm_info

    def vm_list(self, request, context):
        return run_tira_script("vm-list")

    def vm_sandbox(self, request, context):
        return run_tira_script("vm-sandbox", request.vmName)

    def vm_shutdown(self, request, context):
        return run_tira_script("vm-shutdown", request.vmName)

    def vm_snapshot(self, request, context):
        return run_tira_script("vm-snapshot", request.vmName)

    def vm_start(self, request, context):
        return run_tira_script("vm-start", request.vmName)

    def vm_stop(self, request, context):
        return run_tira_script("vm-stop", request.vmName)

    def vm_unsandbox(self, request, context):
        return run_tira_script("vm-unsandbox", request.vmName)

    def run_execute(self, request, context):
        return run_tira_script("run-execute", request.submissionFile, request.inputDatasetName, request.inputRunPath,
                               request.outputDirName, request.sandboxed, request.optionalParameters);

    # async def run_execute(self, request, context):
    #     return run_tira_script("run-execute", request.submissionFile, request.inputDatasetName, request.inputRunPath,
    #                                       request.outputDirName, request.sandboxed, request.optionalParameters);


def serve():
    logger = logging.getLogger()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    server.start()
    logging.info("Starting tira-host server on %s", listen_addr)
    server.wait_for_termination()


# async def serve_async():
#     server = aio.server()
#     tira_host_pb2_grpc.add_TiraHostServiceServicer_to_server(TiraHostService(), server)
#     listen_addr = '[::]:50051'
#     server.add_insecure_port(listen_addr)
#     logging.info("Starting server on %s", listen_addr)
#     await server.start()
#     await server.wait_for_termination()


if __name__ == '__main__':
    fileConfig('../conf/logging_config.ini')
    serve()
    # asyncio.run(serve_async())
