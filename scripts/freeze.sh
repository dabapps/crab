#!/usr/bin/env bash

set -e

pyinstaller --clean -F ./crab.py -n crab
