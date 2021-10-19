#!/bin/bash

pip install numpy pandas matplotlib seaborn gooey

realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

realpath "$0"

python3 agilent2heatmap.py
