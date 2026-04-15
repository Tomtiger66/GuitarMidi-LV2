#!/bin/bash
set -e
SOURCE_DIR="/data2/training_subset_acoustic/"
TARGET_DIR="training_subset/training_subset_acoustic"
USEDRECORDS_FILE="usedrecords-acoustic.txt"
REMOVE_SOURCE_FILES=false # Set to true if you want to move instead of copy
REMOVE_TARGET_FILES=false # Set to true if you want to delete files from target after copying (use with caution!)
RETAIN_TARGET_FILES_PERCENTAGE=0 # Percentage of files to retain in target when REMOVE_TARGET_FILES is true (0-100)
NUM_FILES_TO_COPY=10000 #5690 #20000

./copy_trainingsubset.sh "$SOURCE_DIR" "$TARGET_DIR" "$USEDRECORDS_FILE" "$REMOVE_SOURCE_FILES" "$REMOVE_TARGET_FILES" "$RETAIN_TARGET_FILES_PERCENTAGE" "$NUM_FILES_TO_COPY"