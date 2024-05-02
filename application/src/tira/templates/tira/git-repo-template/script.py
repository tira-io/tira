import argparse

def parse_args():
    parser = argparse.ArgumentParser(prog='script')
    parser.add_argument('-i', '--input', required=True, help='the input to the script.')
    parser.add_argument('-o', '--output', required=True, help='the output of the script.')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    print(f'This is a demo, I ignore the passed input {args.input} and write some content into the output file {args.output}.')
    with open(args.output + '/predictions.jsonl', 'w') as f:
        f.write('hello world')
    print('Done. I wrote "hello world" to {args.output}/predictions.jsonl.')
