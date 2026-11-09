"""Hash a local resource without executing or uploading it."""
import argparse
import hashlib
import json
from pathlib import Path

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file',type=Path)
    args=parser.parse_args()
    if not args.file.is_file(): parser.error('Expected an existing regular file')
    digest=hashlib.sha256()
    with args.file.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
    print(json.dumps({'file':args.file.name,'bytes':args.file.stat().st_size,'sha256':digest.hexdigest()}))
