# MIT License

# Copyright (c) 2020 Joseph Hejderup

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/env python3
"""
Generates a JSON PDN from partial PDN text files in previous steps. To generate the JSON
file, the script takes as input the following files:

 - pdn_all_nodes.txt
 - pdn_all_edges.txt

Missing nodes in the edge dataset are reported in <output_filename>.failed

Example:
    python3 generate-json-pdn.py <nodes_file.txt> <edges_file.txt> <output_filename>.json
"""
import sys
import json 

_mapping_node_name_id = {}
_mapping_edges = {}
id = 0


###
#### POPULATE NODES
###


with open(sys.argv[1]) as cdn_node_file:
    for raw_node in cdn_node_file:
        node = raw_node.rstrip()
        if node not in _mapping_node_name_id:
            _mapping_node_name_id[node] = id
            id = id + 1


failed = set()
with open(sys.argv[2]) as cdn_edges_file:
    for raw_edge in cdn_edges_file:
        if raw_edge.rstrip():
            edge = raw_edge.rstrip().split(' ')
            try:
                source_id = _mapping_node_name_id[edge[0]]
                target_id = _mapping_node_name_id[edge[1]]
                if source_id not in _mapping_edges:
                    _mapping_edges[source_id] = set()
                _mapping_edges[source_id].add(target_id)
            except Exception:
                failed.add(raw_edge.rstrip())

print("[{}] Populated all nodes and edges in python dicts!".format(sys.argv[0]))

###
#### JSON PROCESSING
###

data = {}
data['nodes'] = []
data['edges'] = []

for key,value in _mapping_node_name_id.items():
    data['nodes'].append({
        'name': key,
        'id': value,
    })

for key,value in _mapping_edges.items():
    data['edges'].append({
        'src': key,
        'tgts': list(value)
    })

print("[{}] Created JSON entries, dumping data to {}".format(sys.argv[0], sys.argv[3]))

with open("{}.json".format(sys.argv[3]),"w") as outfile:
     json.dump(data, outfile)

if len(failed) > 0:
    with open("{}.failed".format(sys.argv[3]),"w") as outfile:
        outfile.writelines(failed)