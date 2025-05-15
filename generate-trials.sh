#!/bin/bash

# Path to the map generator script
MAP_GENERATOR="map-generator.py"

# Fixed number of obstacles
OBSTACLES=128

# Trials configurations
GRID_SIZES=(20 35 50)
ROBOT_COUNTS=(2 5 10)
VICTIM_COUNTS=(10 25 40)

# Make sure the output directory exists
mkdir -p trials

# Loop through all combinations
for GRID in "${GRID_SIZES[@]}"; do
    for ROBOTS in "${ROBOT_COUNTS[@]}"; do
        for VICTIMS in "${VICTIM_COUNTS[@]}"; do
            FILENAME="${ROBOTS}_${VICTIMS}_${GRID}.bin"
            echo "Generating $FILENAME..."
            python3 "$MAP_GENERATOR" -s "$GRID" -o "$OBSTACLES" -v "$VICTIMS" -b "$ROBOTS" -f "trials/$FILENAME"
        done
    done
done

echo "All map files have been generated in the 'trials' folder."
