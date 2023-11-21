#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <URL>"
    exit 1
fi

# Get the URL from the command line argument
url=$1

# Extract the filename from the URL
filename=$(basename "$url")
folder=$(basename "$filename" .zip)

# Download the chromedriver zip folder
echo "Downloading $filename..."
wget "$url"

# Check if the download was successful
if [ $? -eq 0 ]; then
    echo "Download successful."
else
    echo "Download failed. Please check the URL and try again."
    exit 1
fi

# Unzip the downloaded chromedriver folder
echo "Extracting $filename..."
unzip "$filename"

# Check if the unzip was successful
if [ $? -eq 0 ]; then
    echo "Extraction successful. Extracted files are in the current directory."
else
    echo "Extraction failed. Please make sure the downloaded file is a valid zip archive."
    exit 1
fi

# Move chromedriver executable to /usr/bin using sudo
echo "Moving chromedriver executable to /usr/bin..."
sudo mv $folder/chromedriver /usr/bin/

# Check if the move was successful
if [ $? -eq 0 ]; then
    echo "Chromedriver executable moved to /usr/bin successfully."
else
    echo "Failed to move chromedriver executable. Please check permissions and try again."
    exit 1
fi

# Clean up - remove the downloaded zip file and extracted folder
echo "Cleaning up..."
rm "$filename"
rm -rf $folder

echo "Installation completed successfully."
