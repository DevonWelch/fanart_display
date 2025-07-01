#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Script directory: $SCRIPT_DIR"
for file in $SCRIPT_DIR/../fanart/*; do
  echo "Processing $file"
  # if file is jpg, jpeg or png
    if [[ $file == *.jpg || $file == *.jpeg || $file == *.png ]]; then
        echo "Processing $file"
        # convert "$file" -scale 10% -blur 0x2.5 -resize 1000% "blurred/${file%.jpg}.jpg"
        # convert "$file" -scale 10% -blur 0x2.5 -resize 1000% "blurred/${file%.jpeg}.jpg"
        # convert "$file" -scale 10% -blur 0x2.5 -resize 1000% "blurred/${file%.png}.png"
        # converty and save in the blurred directory
        # xpath=${file%/*} 
        xbase=${file##*/}
        # xfext=${xbase##*.}
        xpref=${xbase%.*}
        dest_path="$SCRIPT_DIR/../fanart/blurred/${xpref##*/}"
        # if it doesn't exist already, convert it
        echo "$dest_path"
        if [ ! -f "$dest_path" ]; then
            echo "convert -scale 10% -blur 0x2.5 -resize 1000% "$file" "$dest_path""
            convert -scale 10% -blur 0x2.5 -resize 1000% "$file" "$dest_path"
        fi
    fi
done

# convert -scale 10% -blur 0x2.5 -resize 1000% sample.jpg blurred_fast.jpg