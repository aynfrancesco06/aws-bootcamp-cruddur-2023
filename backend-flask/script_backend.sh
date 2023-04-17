#!/bin/sh

set -x

python3 -m -u flask run --host=0.0.0.0 --port=4567 --no-debug