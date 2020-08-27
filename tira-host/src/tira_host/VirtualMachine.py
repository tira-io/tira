#!/usr/bin/env python
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Nikolay Kolyada
"""

import virtualbox

class VirtualMachine:
    Running, Stopped, Sandboxed, Busy, Failed = range(0, 5)

    def __init__(self, name, image):
        self.name = name
        self.image = image
        if self.create(name, image):
            self.status = self.Running
        else:
            self.status = self.Failed

    def backup(self):
        # - check if vm is registered
        # - check if sandboxed, unsandbox
        # - stop vm
        # - vboxmanage export
        pass

    def create(self, name, image):
        pass

    def delete(self):
        pass

    def get_info(self):
        pass

    def sandbox(self):
        pass

    def shutdown(self):
        pass

    def snapshot(self):
        pass

    def start(self):
        pass

    def stop(self):
        # VBoxManage controlvm "$vmname" poweroff
        pass

    def unsandbox(self):
        pass
