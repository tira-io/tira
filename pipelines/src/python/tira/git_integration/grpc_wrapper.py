from datetime import timedelta
from failsafe import Failsafe, RetryPolicy, Backoff
import asyncio

retry_policy = RetryPolicy(
    allowed_retries=5,
    backoff=Backoff(delay=timedelta(seconds=15), max_delay=timedelta(seconds=300), jitter=False),
    on_retry=lambda: print("Something failed. I retry...")
)

def grpc_client(args):
    print('load GRPC client...')
    import sys
    sys.path.append('/tira-git/src/tira_host')
    from grpc_client import TiraHostClient

    ret = TiraHostClient(args.tira_application_host, args.tira_application_grpc_port)
    print('GRPC client is loaded.')
    
    return ret


def confirm_run_eval(args):
    asyncio.get_event_loop().run_until_complete(
        Failsafe(retry_policy=retry_policy).run(lambda: confirm_run_eval_async(args))
    )


async def confirm_run_eval_async(args):
    client = grpc_client(args)
    
    print(client.confirm_run_eval(vm_id=args.input_run_vm_id, dataset_id=args.dataset_id, run_id=args.run_id, transaction_id=args.transaction_id))


def confirm_run_execute(args):
    asyncio.get_event_loop().run_until_complete(
        Failsafe(retry_policy=retry_policy).run(lambda: confirm_run_execute_async(args))
    )


async def confirm_run_execute_async(args):
    client = grpc_client(args)

    print(client.confirm_run_execute(vm_id=args.input_run_vm_id, dataset_id=args.dataset_id, run_id=args.run_id, transaction_id=args.transaction_id))


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Make some grpc calls')
    parser.add_argument('--tira_application_host', type=str, default='betaweb001.medien.uni-weimar.de')
    parser.add_argument('--tira_application_grpc_port', type=str, default='31553')
    
    parser.add_argument('--input_run_vm_id', type=str, required=True)
    parser.add_argument('--dataset_id', type=str, required=True)
    parser.add_argument('--run_id', type=str, required=True)
    parser.add_argument('--transaction_id', type=str, required=True)
    
    parser.add_argument('--task', type=str, choices=['confirm-run-eval', 'confirm-run-execute'], default=None, required=True)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    
    if args.task == 'confirm-run-eval':
        confirm_run_eval(args)
    elif args.task == 'confirm-run-execute':
        confirm_run_execute(args)

    # k -n services-tira port-forward tira-application-grpc-6d6f767945-hjqnr 50052
    # docker run --net=host --rm -ti --entrypoint python3 webis/tira-git-pipelines:0.0.2 /tira/application/src/tira/git_integration/grpc_wrapper.py --input_run_vm_id princess-knight --dataset_id del-me-20220813-training --run_id 2022-08-20-13-36-23 --transaction_id 1 --task confirm-run-execute --tira_application_host 127.0.0.1 --tira_application_grpc_port 50052

