#!/bin/bash

[ ! -d .venv ] && {
    echo -n 'Enter prompt prefix: '
    read prompt

    python3 -m virtualenv --prompt "[${prompt}] " .venv
}

. .venv/bin/activate
