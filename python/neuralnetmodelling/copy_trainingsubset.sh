#!/bin/bash

SOURCE_DIR="/data/training_subset/"
TARGET_DIR="training_subset"
USEDRECORDS_FILE="usedrecords.txt"
mkdir -p "$TARGET_DIR"

NUM_FILES_TO_COPY=5690 #20000

# Create usedrecords file if it doesn't exist
touch "$USEDRECORDS_FILE"

# Create temp files
TMP_EXCLUDE=$(mktemp)
TMP_SELECTED=$(mktemp)

# Strip comments/blanks and get basenames to exclude
while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    basename "$line"
done < "$USEDRECORDS_FILE" > "$TMP_EXCLUDE"

# Find all files, filter out excluded ones, shuffle, pick N, save to temp file
find "$SOURCE_DIR" -type f | \
    awk -F/ -v excludefile="$TMP_EXCLUDE" '
        BEGIN { while ((getline line < excludefile) > 0) exclude[line]=1 }
        !($NF in exclude)
    ' | \
    shuf | \
    head -n "$NUM_FILES_TO_COPY" > "$TMP_SELECTED"

# Check if we actually found files to copy
FILE_COUNT=$(wc -l < "$TMP_SELECTED")
echo "Selected $FILE_COUNT files to copy."

if [ "$FILE_COUNT" -gt 0 ]; then
    echo "Starting bulk copy to $TARGET_DIR..."
    
    # OPTION 1: xargs with cp (Extremely fast, utilizing multiple threads)
    # xargs -a "$TMP_SELECTED" -P 4 -I {} cp {} "$TARGET_DIR/"
    
    # OPTION 2: rsync with a single call. 
    # Note: --files-from preserves paths by default. We cd into SOURCE_DIR 
    # and strip the SOURCE_DIR prefix from the list to copy them flat.
    sed "s|^$SOURCE_DIR/*||" "$TMP_SELECTED" > "${TMP_SELECTED}_relative"
    rsync -a --info=progress2 --files-from="${TMP_SELECTED}_relative" "$SOURCE_DIR" "$TARGET_DIR/"
    
    # Append all successfully copied files to used records in one operation
    cat "$TMP_SELECTED" >> "$USEDRECORDS_FILE"
    echo "Finished copying $FILE_COUNT files and updated $USEDRECORDS_FILE"
else
    echo "No new files to copy."
fi

# Cleanup
rm -f "$TMP_EXCLUDE" "$TMP_SELECTED" "${TMP_SELECTED}_relative"
