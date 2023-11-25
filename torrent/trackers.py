from pathlib import Path

file_path = Path(__file__).parent / 'trackers.txt'
with open(file_path, 'r') as file:
    trackers = list(map(lambda line: line.strip(), file.readlines()))