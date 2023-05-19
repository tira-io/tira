# script ensures that all database entries with foreign key input_dataset "none"
# are referencing the dataset primary key "None"

import json

path = "mnt/ceph/tira/state/db-backup/django-db-dump-21-04-2023.json"

# Read the JSON file
with open(path, 'r') as file:
    data = json.load(file)

# Iterate over the entries and modify the "input_dataset" field
for entry in data:
    fields = entry.get('fields', {})
    if fields.get('input_dataset') == 'none':
        fields['input_dataset'] = 'None'

# Write the modified data back to the JSON file
with open(path, 'w') as file:
    json.dump(data, file, indent=4)
