#!/bin/bash

# Path to the simulator script
ARGV_1="$1"
SIMULATOR="sim/${ARGV_1}.py"

# Directories
MAP_DIR="trials"
LOG_DIR="logs/$ARGV_1"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Loop through all .bin map files and run them in parallel
for MAP_FILE in "$MAP_DIR"/*.bin; do
    # do three times
    for i in {1..3}; do
        BASENAME=$(basename "$MAP_FILE" .bin)
        LOG_FILE="$LOG_DIR/${BASENAME}_$i.log"
        
        echo "Running $MAP_FILE -> $LOG_FILE"

        # Run the simulator in background, redirecting stdout to log
        python "$SIMULATOR" -f "$MAP_FILE" > "$LOG_FILE"
    done
done

# echo "All simulations started in parallel."

wait
echo "All simulations completed."