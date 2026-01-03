import os
import json
import re
from collections import defaultdict

def walk_dir(directory):
    stats = {
        'files': defaultdict(int),
        'lines': 0,
        'largest': None,
        'depth': 1
    }
    for root, dirs, files in os.walk(directory):
        stats['depth'] += 1
        for file in files:
            stats['files'][os.path.splitext(file)[1]] += 1
            with open(os.path.join(root, file), 'r') as f:
                stats['lines'] += sum(1 for line in f)
                if os.path.getsize(os.path.join(root, file)) > stats['largest'].get('size', 0):
                    stats['largest'] = {'name': file, 'size': os.path.getsize(os.path.join(root, file))}
    return stats

def main():
    stats = walk_dir('.')
    with open('stats.json', 'w') as f:
        json.dump(stats, f)

if __name__ == '__main__':
    main()