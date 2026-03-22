#!/bin/bash

# This script copies a limited number of random tfrecords from the source dir /data/training_subset/ on the slow spinning rust hdd
# to the target dir ./training_subset on the fast nvme

SOURCE_DIR="/data/training_subset/"
TARGET_DIR="training_subset"

mkdir -p $TARGET_DIR

NUM_FILES_TO_COPY=8100

FILES=$(find ${SOURCE_DIR} -iname "*.tfrecord")

TMP=$(mktemp)

for file in $FILES
do
    echo "$file" >> $TMP
done

SHUF_FILES=$(shuf $TMP)

COUNT=0

for file in $SHUF_FILES 
do
    #rsync -a --info=progress2 $file $TARGET_DIR/
    COUNT=$(($COUNT+1))
    if [ $COUNT -gt $NUM_FILES_TO_COPY ]; then
        echo "finished"
        break
    else
        echo "Copying file $COUNT"
        rsync -a --info=progress2 $file $TARGET_DIR/
    fi
done
