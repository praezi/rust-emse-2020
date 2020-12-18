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
Converts rustcg identifiers into universal function identifiers (UFI) for
creation of CDNs and PDNs. To construct a UFI, we remove the first segment in
`relative_def_id` and prepend the identifier with crate name and version. The
output generates the following files:

 - cdn_nodes.txt: all function and macro identifiers in simple UFI format
 - pdn_nodes.txt: package nodes inferred from all funtions and macros
 - cdn_edges.txt: function edges in UFI format
 - pdn_edges.txt: package dependency relations 

Function calls within packages are removed in pdn_edges.txt

Example:
    python3 ufify-rustcg.py callgraph.json ./jlib/0.2.0


On Lima:
    time find . -name callgraph.json -printf '%h\n' | parallel 'cd {}; python3 /home/jhejderup/praezi/ufify-rustcg.py callgraph.json {}; [[ $? -ne 0 ]] && echo {}' 2>&1 | tee ../ufify.log 
"""

import sys
import json
import os

crate_under_analysis = sys.argv[2].split("/")
crate_name = crate_under_analysis[1]
crate_version = crate_under_analysis[2]


def is_head_crate(source):
    return source['package_name'] == crate_name and source['package_version'] == crate_version

def is_crate_call(source, target):
    return is_head_crate(source) or is_head_crate(target)

def internal_crate_call(source,target):
    return is_head_crate(source) and is_head_crate(target)

def dependency_crate_call(source,target):
    return is_head_crate(source) and not is_head_crate(target)

def dependent_crate_call(source,target):
    return not is_head_crate(source) and is_head_crate(target)

def is_autogen_fn(node):
    return "_IMPL_DESERIALIZE_FOR_" in node['relative_def_id'] or "_IMPL_SERIALIZE_FOR_" in node['relative_def_id']  

with open(sys.argv[1]) as cg_file:
    data = json.load(cg_file)
    
    _mappings_id_nodes = {}
    _mappings_id_pdn = {}
    _mappings_id_ufi = {}

    ##
    ### Read function nodes
    ##
    for fn_node in data['functions']:
        _mappings_id_nodes[fn_node['id']] = fn_node
        ## PDN Nodes
        _mappings_id_pdn[fn_node['id']] = "{0}::{1}".format(fn_node['package_name'],fn_node['package_version'])
        ## CDN Nodes
        path = fn_node['relative_def_id'].split("::")
        path.pop(0)
        _mappings_id_ufi[fn_node['id']] = "{0}::{1}::{2},{3},{4},fn".format(fn_node['package_name'],fn_node['package_version'],"::".join(path),fn_node['is_externally_visible'], fn_node['num_lines'])

    ##
    ### Read macro nodes
    ##
    for macro_node in data['macros']:
        _mappings_id_nodes[macro_node['id']] = macro_node
        ## PDN Nodes
        _mappings_id_pdn[macro_node['id']] = "{0}::{1}".format(macro_node['package_name'],macro_node['package_version'])
        ## CDN Nodes
        path = macro_node['relative_def_id'].split("::")
        path.pop(0)
        _mappings_id_ufi[macro_node['id']] = "{0}::{1}::{2},{3},{4},m".format(macro_node['package_name'],macro_node['package_version'],"::".join(path),macro_node['is_externally_visible'], macro_node['num_lines'])
    
    
    pdn_edges = set()
    cdn_edges = set() #NB: Should be set!
    invalid_edges = set()
    
    ##
    ### Read function calls
    ##
    for edge in data['function_calls']:

        source_id = edge[0]
        target_id = edge[1]
        source_node = _mappings_id_nodes[source_id]
        target_node = _mappings_id_nodes[target_id]

        if source_node['package_name'] is not None and target_node['package_name'] is not None:
            if is_crate_call(source_node,target_node):
                if not internal_crate_call(source_node,target_node) and dependency_crate_call(source_node,target_node):
                    pdn_edges.add("{0} {1}".format(
                        _mappings_id_pdn[source_id], 
                        _mappings_id_pdn[target_id]))
                
                if internal_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} {2} I".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0],
                        edge[2]))
                elif dependency_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} {2} D".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0],
                        edge[2]))
                elif dependent_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} {2} U".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0],
                        edge[2]))
                else:
                    invalid_edges.add("{0} {1} {2}".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0],
                        edge[2]))

            else:
                invalid_edges.add("{0} {1} {2}".format(
                    _mappings_id_ufi[source_id].split(",")[0], 
                    _mappings_id_ufi[target_id].split(",")[0],
                    edge[2]))
                
    ##
    ### Read macro calls(https://github.com/ktrianta/rust-callgraphs/blob/master/src/analysis/src/callgraph.rs#L28, no bool)
    ##
    for edge in data['macro_calls']:

        source_id = edge[0]
        target_id = edge[1]
        source_node = _mappings_id_nodes[source_id]
        target_node = _mappings_id_nodes[target_id]

        if source_node['package_name'] is not None and target_node['package_name'] is not None:
            if is_crate_call(source_node,target_node):
                if not internal_crate_call(source_node,target_node) and dependency_crate_call(source_node,target_node):
                    pdn_edges.add("{0} {1}".format(
                        _mappings_id_pdn[source_id], 
                        _mappings_id_pdn[target_id]))
                
                if internal_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} M I".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0]))
                elif dependency_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} M D".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0]))
                elif dependent_crate_call(source_node,target_node):
                    cdn_edges.add("{0} {1} M U".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0]))
                else:
                    invalid_edges.add("{0} {1} M".format(
                        _mappings_id_ufi[source_id].split(",")[0], 
                        _mappings_id_ufi[target_id].split(",")[0]))
            else:
                invalid_edges.add("{0} {1} M".format(
                    _mappings_id_ufi[source_id].split(",")[0], 
                    _mappings_id_ufi[target_id].split(",")[0]))
        
    ##
    ### Dump everything to files
    ##

    os.makedirs("cdn_meta", exist_ok=True)

    with open("cdn_meta/pdn_nodes.txt", "w") as outfile:
        vs = set(filter(lambda x: x != 'None::None',_mappings_id_pdn.values()))
        outfile.writelines(s + '\n' for s in vs)

    with open("cdn_meta/pdn_edges.txt", "w") as outfile:
        outfile.writelines(s + '\n' for s in pdn_edges)
    
    with open("cdn_meta/cdn_nodes.txt", "w") as outfile:
        vs = set(filter(lambda x: not x.startswith('None::None'),_mappings_id_ufi.values()))
        outfile.writelines(s + '\n' for s in vs)
        
    with open("cdn_meta/cdn_edges.txt", "w") as outfile:
        outfile.writelines(s + '\n' for s in cdn_edges)

    with open("cdn_meta/invalid_edges.txt", "w") as outfile:
        outfile.writelines(s + '\n' for s in invalid_edges)
