""" This file contains (interface-)functions and callbacks that run commands on the TIRA backend.
 Commands return True when the request was accepted, otherwise False """


def create_vm(hostname: str, vm_id: str, ova: str):
    """ create vm with the given details. """
    #TODO implement
    print('execute', hostname, vm_id, ova)
    return True


def modify_vm(hostname: str, vm_id: str, memory: int, cpu: int):
    """ set memory and core count (cpu) of the given vm to the given values """
    # TODO implement
    pass


def add_storage(hostname: str, vm_id: str, storage_type: str, amount: int):
    """ set storage of the given vm to the given values
    @param vm_id: id of the vm to modify
    @param storage_type: either 'hdd' or 'sftp'
    @param amount: GB of storage to add
    """
    pass


def archive_vm(hostname: str, vm_id: str):
    # TODO needs more parameters: prefix, backup-location
    pass