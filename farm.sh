#!/bin/bash

# The name or path of your program and pass any arguments to it
PROGRAM="python3 -u farm.py"

# Capture additional arguments passed to the script and pass them to the program
ARGS="$@"

# Infinite loop to keep restarting the program
while true; do
    echo "Starting the farming with args: $ARGS..."
    
    # Run the program with the arguments
    $PROGRAM $ARGS

    # Wait a moment before restarting (optional)
    sleep 2

    echo "Program exited. Restarting..."
done
