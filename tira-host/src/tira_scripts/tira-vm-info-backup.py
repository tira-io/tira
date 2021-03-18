#!/usr/bin/env python3
import os
import sys
from itertools import groupby
import logging
import argparse
import glob

logging.basicConfig(level=logging.DEBUG)
########################################
TIRA_PATH='/mnt/ceph/tira'
########################################
DATA_PATH=TIRA_PATH+'/data'
MODEL_PATH=TIRA_PATH+'/model'
STATE_PATH=TIRA_PATH+'/state'
BACKUP_PATH=TIRA_PATH+'/backup'
########################################
RUNS_PATH=DATA_PATH+'/runs'
########################################
USERS_PATH=MODEL_PATH+'/users'
SOFTWARES_PATH=MODEL_PATH+'/softwares'
VMS_PATH=MODEL_PATH+'/virtual-machines'
########################################
SUBMISSIONS_PATH=STATE_PATH+'/softwares'
########################################

def is_mounted_ceph():
    return os.path.ismount(TIRA_PATH)

def save_user_credentials(username):
    logging.info('Saving user credentials from users.prototext')
    l = []
    list_of_users = []
    with open(f'{USERS_PATH}/users.prototext') as f:
        for key,group in groupby(f, lambda line: line.startswith('users')):
            if not key:
                group = list(group)
                l.append(group)
    for user in l:            
        a = user[:-1]
        a = [field.strip() for field in a]
        a = [thing.split(':') for thing in a]
        a = {thing[0]:thing[1].strip() for thing in a if len(thing)==2}
        a = {k:v.replace('"', "") for k,v in a.items()}
        list_of_users.append(a)
    print([user for user in list_of_users if user['userName']==f'{username}'][0])

def save_virtual_machine_prototext(username):
    logging.info(f'Saving VM prototext for user {username}')
    vm_prototext = f'{VMS_PATH}/{username}.prototext'
    print(vm_prototext)

def save_user_runs(username):
    logging.info(f'Saving run directories of user {username}')
    run_directories = glob.glob(f'{RUNS_PATH}/*/{username}')
    for d in run_directories:
        print(d)
        print(os.listdir(d))
        print(d.split('/')[-2])

def save_user_softwares_prototext(username):
    logging.info(f'Saving software/prototext.files for user {username}')
    software_directories = glob.glob(f'{SOFTWARES_PATH}/*/{username}')
    to_save = [d[-2] for d in [d.split('/') for d in software_directories]]    
    print([os.listdir(d)[0] for d in software_directories])
    print(to_save)

def save_user_softwares_submissions(username):
    logging.info(f'Saving software submissions for user {username}')
    software_directories = f'{SUBMISSIONS_PATH}/{username}'
    print(os.listdir(software_directories))



def main(username):
    if not is_mounted_ceph():
        logging.error('Please make sure Ceph is mounted')
        sys.exit(0)
    destination_folder = f'{BACKUP_PATH}/{username}'
    if not os.path.exists(destination_folder):
        logging.info(f'Now creating {destination_folder}')
        os.makedirs(destination_folder, exist_ok=True)
    logging.info(f'Now backing up metadata to folder {destination_folder}')
    save_user_credentials(username)
    print("********************************************")
    save_virtual_machine_prototext(username)
    print("********************************************")
    save_user_runs(username)
    print("********************************************")
    save_user_softwares_prototext(username)
    print("********************************************")
    save_user_softwares_submissions(username)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username")
    args = parser.parse_args()
    args = vars(args)
    main(**args)