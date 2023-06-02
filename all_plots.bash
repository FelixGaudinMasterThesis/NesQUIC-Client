#!/bin/bash
folder="$1"

mkdir -p "$folder/graphs"

python3 plotting/plot.py $folder rtts_cdf
python3 plotting/plot.py $folder rtts_evolution
python3 plotting/plot.py $folder smoothed_rtts_evolution
python3 plotting/plot.py $folder comp_table
python3 plotting/plot.py $folder complet