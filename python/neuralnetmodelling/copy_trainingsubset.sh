#!/bin/bash

SOURCE_DIR="/data/training_subset/"
TARGET_DIR="training_subset"
USEDRECORDS_FILE="usedrecords.txt"
mkdir -p "$TARGET_DIR"

NUM_FILES_TO_COPY=20000 #8100

# Create usedrecords file if it doesn't exist
touch "$USEDRECORDS_FILE"

# Create a temporary file with just the basenames to exclude (strip comments/blanks)
TMP_EXCLUDE=$(mktemp)
while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    basename "$line"
done < "$USEDRECORDS_FILE" > "$TMP_EXCLUDE"

# Find all files, filter out excluded ones, shuffle, pick N
SELECTED=$(find "$SOURCE_DIR" -type f | \
    awk -F/ -v excludefile="$TMP_EXCLUDE" '
        BEGIN { while ((getline line < excludefile) > 0) exclude[line]=1 }
        !($NF in exclude)
    ' | \
    shuf | \
    head -n "$NUM_FILES_TO_COPY")
echo $SELECTED
COUNT=0
while IFS= read -r file; do
    # check if file is not empty string
    [[ -z "$file" ]] && continue
    COUNT=$((COUNT+1))
    echo "Copying file $COUNT/$NUM_FILES_TO_COPY: $file"
    rsync -a --info=progress2 "$file" "$TARGET_DIR/"
    # Append to used records
    echo "$file" >> "$USEDRECORDS_FILE"
done <<< "$SELECTED"

echo "Finished copying $COUNT files"
rm -f "$TMP_EXCLUDE"

