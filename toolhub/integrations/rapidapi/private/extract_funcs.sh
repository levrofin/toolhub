#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <unpacked-data.zip-dir>"
    exit 1
fi

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ast-grep scan -r ast-grep.yaml "$1" --json=stream | python generate_functions_json.py /dev/stdin > 'function_infos.json'
