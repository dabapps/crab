#!/usr/bin/env bash

set -e

pyinstaller --clean -F ./crab/cli.py -n crab
