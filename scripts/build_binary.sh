#!/usr/bin/env bash

set -e

export PATH=env/bin:${PATH}

pyinstaller --clean -F ./crab/cli.py -n crab
