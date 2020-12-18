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
Generates a JSON CDN from CDN text files in previous steps. To generate the JSON
file, the script takes as input the following files:

 - cdn_all_nodes_sorted.txt
 - cdn_all_edges_sorted.txt

The script assumes that there are no missing nodes.

Example:
    python3 generate-json-cdn.py <nodes_file.txt> <edges_file.txt> <output_filename>.json
"""
import sys
import json 

_mapping_node_name_id = {}
_mapping_nodes = {}

_mapping_edges_cha_i = {}
_mapping_edges_cha_d = {}
_mapping_edges_cha_u = {}

_mapping_edges_static_i = {}
_mapping_edges_static_d = {}
_mapping_edges_static_u = {}


_mapping_edges_macro_i = {}
_mapping_edges_macro_d = {}
_mapping_edges_macro_u = {}

id = 0


###
#### POPULATE NODES
###

with open(sys.argv[1]) as cdn_node_file:
    for raw_node in cdn_node_file:
        node = raw_node.rstrip()
        node_meta = raw_node.rstrip().split(",")
        node_name = node_meta[0]
        node_attr = node_meta[1]
        node_loc = node_meta[2]
        node_type = node_meta[3]

        if node_name not in _mapping_node_name_id:
            _mapping_node_name_id[node_name] = id
            _mapping_nodes[id] = {"def_id" : node_name, "acc": node_attr, "loc": node_loc, "type": node_type}
            id = id + 1

failed = set()
with open(sys.argv[2]) as cdn_edges_file:
    for raw_edge in cdn_edges_file:
        if raw_edge.rstrip():
            edge = raw_edge.rstrip().split(' ')
            try:
                source_id = _mapping_node_name_id[edge[0]]
                target_id = _mapping_node_name_id[edge[1]]

                if 'I' in edge[3]:
                    # https://github.com/ktrianta/rust-callgraphs/blob/master/src/analysis/src/callgraph.rs#L81 False => virtual dispatch
                    if 'False' == edge[2]:
                        if source_id not in _mapping_edges_cha_i:
                            _mapping_edges_cha_i[source_id] = set()
                        _mapping_edges_cha_i[source_id].add(target_id)
                    elif 'True' == edge[2]:
                        if source_id not in _mapping_edges_static_i:
                            _mapping_edges_static_i[source_id] = set()
                        _mapping_edges_static_i[source_id].add(target_id)
                    elif 'M' == edge[2]:
                        if source_id not in _mapping_edges_macro_i:
                            _mapping_edges_macro_i[source_id] = set()
                        _mapping_edges_macro_i[source_id].add(target_id)
                elif 'D' == edge[3]:
                    # https://github.com/ktrianta/rust-callgraphs/blob/master/src/analysis/src/callgraph.rs#L81 False => virtual dispatch
                    if 'False' == edge[2]:
                        if source_id not in _mapping_edges_cha_d:
                            _mapping_edges_cha_d[source_id] = set()
                        _mapping_edges_cha_d[source_id].add(target_id)
                    elif 'True' == edge[2]:
                        if source_id not in _mapping_edges_static_d:
                            _mapping_edges_static_d[source_id] = set()
                        _mapping_edges_static_d[source_id].add(target_id)
                    elif 'M' == edge[2]:
                        if source_id not in _mapping_edges_macro_d:
                            _mapping_edges_macro_d[source_id] = set()
                        _mapping_edges_macro_d[source_id].add(target_id)
                elif 'U' == edge[3]:
                    # https://github.com/ktrianta/rust-callgraphs/blob/master/src/analysis/src/callgraph.rs#L81 False => virtual dispatch
                    if 'False' == edge[2]:
                        if source_id not in _mapping_edges_cha_u:
                            _mapping_edges_cha_u[source_id] = set()
                        _mapping_edges_cha_u[source_id].add(target_id)
                    elif 'True' == edge[2]:
                        if source_id not in _mapping_edges_static_u:
                            _mapping_edges_static_u[source_id] = set()
                        _mapping_edges_static_u[source_id].add(target_id)
                    elif 'M' == edge[2]:
                        if source_id not in _mapping_edges_macro_u:
                            _mapping_edges_macro_u[source_id] = set()
                        _mapping_edges_macro_u[source_id].add(target_id)                
            except Exception:
                failed.add(raw_edge.rstrip())

print("[{}] Populated all nodes and edges in python dicts!".format(sys.argv[0]))

###
#### JSON PROCESSING
###
data = {}
data['nodes'] = []

data['static_calls_i'] = []
data['static_calls_d'] = []
data['static_calls_u'] = []


data['cha_calls_i'] = []
data['cha_calls_d'] = []
data['cha_calls_u'] = []


data['macro_calls_i'] = []
data['macro_calls_d'] = []
data['macro_calls_u'] = []

for key,value in _mapping_nodes.items():
    data['nodes'].append({
        'id': key,
        'attr': value,
    })
###
### STATIC
###
for key,value in _mapping_edges_static_i.items():
    data['static_calls_i'].append({
        'src': key,
        'tgts': list(value)
    })

for key,value in _mapping_edges_static_d.items():
    data['static_calls_d'].append({
        'src': key,
        'tgts': list(value)
    })

for key,value in _mapping_edges_static_u.items():
    data['static_calls_u'].append({
        'src': key,
        'tgts': list(value)
    })

###
### CHA
###
for key,value in _mapping_edges_cha_i.items():
    data['cha_calls_i'].append({
        'src': key,
        'tgts': list(value)
    })
for key,value in _mapping_edges_cha_d.items():
    data['cha_calls_d'].append({
        'src': key,
        'tgts': list(value)
    })
for key,value in _mapping_edges_cha_u.items():
    data['cha_calls_u'].append({
        'src': key,
        'tgts': list(value)
    })

###
### Macro
###
for key,value in _mapping_edges_macro_i.items():
    data['macro_calls_i'].append({
        'src': key,
        'tgts': list(value)
    })

for key,value in _mapping_edges_macro_d.items():
    data['macro_calls_d'].append({
        'src': key,
        'tgts': list(value)
    })

for key,value in _mapping_edges_macro_u.items():
    data['macro_calls_u'].append({
        'src': key,
        'tgts': list(value)
    })

print("[{}] Created JSON entries, dumping data to {}".format(sys.argv[0], sys.argv[3]))

with open("{}.json".format(sys.argv[3]),"w") as outfile:
     json.dump(data, outfile)

if len(failed) > 0:
    with open("{}.failed".format(sys.argv[3]),"w") as outfile:
        outfile.writelines(failed)
