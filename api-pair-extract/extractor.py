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
Extract entrypoints (APIs) and exitpoints of rustcg-produced call graphs.
Function names are normalized with type information to make it versionless for
package resolution. 


Example:
    python3 api-pair-extract/extractor.py callgraph.json type_hierarchy.json Cargo.lock


On Lima:
    time find . -name callgraph.json -printf '%h\n' | parallel 'cd {}; python3 api-pair-extract/extractor.py callgraph.json type_hierarchy.json Cargo.lock /datasets/praezi/stitching; [[ $? -ne 0 ]] && echo {}' 2>&1 | tee ../versionless.log 
For empty call graphs, run this:
    time find . -name callgraph.json -printf '%h\n' | awk -F "/" '{print "mkdir -p /datasets/praezi/stitching/"$2"/"$3}' | parallel


"""

import json
import sys
import re
import base64
import subprocess
import os
import fcntl
import time
import uuid

import toml


patternClosure = re.compile(r"::{{closure}}[[0-9]*]")
patternImpl = re.compile(r"::{{impl}}[[0-9]*]")
patternBracket = re.compile(r"\[[A-Z|a-z|0-9]*\]")



with open(sys.argv[1]) as cg_file:
    cg = json.load(cg_file)

with open(sys.argv[2]) as ty_file:
    tyhir = json.load(ty_file)
    _types = {}
    _types_defid = {}
    _traits = {}
    _traits_defid = {}
    _impls = {}

    for ty in tyhir['types']:
        _types[ty['id']] = ty
        if ty['relative_def_id'] is not None:
            _types_defid[ty['relative_def_id']] = ty
    for tr in tyhir['traits']:
        _traits[tr['id']] = tr
        if tr['relative_def_id'] is not None:
            _traits_defid[tr['relative_def_id']] = tr
    for im in tyhir['impls']:
        if im['relative_def_id'] is not None:
            _impls[im['relative_def_id']] = im



def process_pkgs():
    _versions = {}
    _successors = {}
    _dependents = {}

    with open(sys.argv[3], 'r') as fp:
        lf_dict = toml.loads(fp.read())

        for crate in lf_dict['package']:
            if crate['name'] not in _versions:
                #NB: We only need lookup for unique nodes.
                _versions[crate['name']] = crate['version']
        
        visited = set()

        for crate in lf_dict['package']:
            if 'dependencies' in crate:
                for dep in crate['dependencies']:
                    src = "{}::{}".format(crate['name'],crate['version'])

                    if " " in dep:
                        dep_arr = dep.split(" ")
                        dst = "{}::{}".format(dep_arr[0], dep_arr[1])
                        if (src,dst) not in visited:
                            visited.add((src,dst))
                            yield(src,dst)
                    else:
                        ver = _versions[dep]
                        dst = "{}::{}".format(dep, ver)
                        if (src,dst) not in visited:
                            visited.add((src,dst))
                            yield(src,dst)
        
_mappings_crate_fns = {}
_base64fns = {}

def mine_and_normalize_fns(fn):
    if fn['package_name'] is not None and fn['package_version'] is not None:
        key = "{}::{}".format(fn['package_name'],fn['package_version']) 
        if key not in _mappings_crate_fns:
            _mappings_crate_fns[key] = list()
        fn['relative_def_id'] = patternClosure.sub("", fn['relative_def_id'])
        segs = fn['relative_def_id'].split("::") 
        fn_name = patternBracket.sub("",segs[-1]) 
        defid_item = "::".join(segs[:-1]) 

        if "{{impl}}" not in defid_item:
            if defid_item in _types_defid:
                fn_str = "{} {}".format(_types_defid[defid_item]['string_id'],fn_name).encode('ascii')
                base64_bytes = base64.b64encode(fn_str)
                _mappings_crate_fns[key].append(base64_bytes.decode('ascii'))
                _base64fns[fn['id']] = base64_bytes.decode('ascii') 
           
            elif defid_item in _traits_defid:
                trait = patternBracket.sub("",_traits_defid[defid_item]['relative_def_id'])
                fn_str = "{} {}".format(trait,fn_name).encode('ascii')
                base64_bytes = base64.b64encode(fn_str)
                _mappings_crate_fns[key].append(base64_bytes.decode('ascii'))
                _base64fns[fn['id']] = base64_bytes.decode('ascii')  
            else:
                fn_str = "{} {}".format(patternBracket.sub("",defid_item),fn_name).encode('ascii')
                base64_bytes = base64.b64encode(fn_str)
                _mappings_crate_fns[key].append(base64_bytes.decode('ascii'))
                _base64fns[fn['id']] = base64_bytes.decode('ascii') 
        else:
            _impl = patternImpl.findall(defid_item)[-1]
            idx = defid_item.rfind(_impl) + len(_impl)
            _impl_defid = defid_item[0:idx]

            structs = []
            traits = []
            implz = []
            if _impl_defid in _impls:
                implz.append(_impls[_impl_defid])

            while implz:
                impl = implz.pop()
                if impl['type_id'] is not None: 
                    structs.append(_types[impl['type_id']]['string_id'])
                if impl['trait_id'] is not None:
                    _raw = _traits[impl['trait_id']]['relative_def_id']
                    if "{{impl}}" in _raw:
                        _impl = patternImpl.findall(_raw)[-1]
                        idx = _raw.rfind(_impl) + len(_impl)
                        _impl_defid = _raw[0:idx]
                        if _impl_defid in _impls:
                            implz.append(_impls[_impl_defid])    
                    else:
                        traits.append(patternBracket.sub("",_raw))

            traits.sort()
            structs.sort()
            fn_str = "{} {} {}".format(" ".join(traits)," ".join(structs),fn_name).encode('ascii')
            base64_bytes = base64.b64encode(fn_str)
            _mappings_crate_fns[key].append(base64_bytes.decode('ascii'))
            _base64fns[fn['id']] = base64_bytes.decode('ascii') 

_mappings_id_nodes = {}

for fn in cg['functions']:
    mine_and_normalize_fns(fn)
    _mappings_id_nodes[fn['id']] = fn

for macro in cg['macros']:
    mine_and_normalize_fns(macro)
    _mappings_id_nodes[macro['id']] = macro
    

####
##### Process edge data
###

pkg_edges = set([(s,t) for (s,t) in process_pkgs()])

def is_stdlib(source):
    return source['package_name'] is None 

def valid_dep_combo(source,target):
    src = "{}::{}".format(source['package_name'],source['package_version'])
    tgt = "{}::{}".format(target['package_name'],target['package_version'])
    return (src,tgt) in pkg_edges

def id(source,target):
    src = "{}::{}".format(source['package_name'],source['package_version'])
    tgt = "{}::{}".format(target['package_name'],target['package_version'])
    return src == tgt

internal_package_edges = {}
cross_pkg_edges = {}

def extract_edge_data(edge):
    source_id = edge[0]
    target_id = edge[1]
    source_node = _mappings_id_nodes[source_id]
    target_node = _mappings_id_nodes[target_id]

    src_ = "{}::{}".format(source_node['package_name'],source_node['package_version'])
    target_ = target_node['package_name']

    if not is_stdlib(source_node) and not is_stdlib(target_node) and valid_dep_combo(source_node,target_node):

        if (src_, _base64fns[source_id]) not in cross_pkg_edges:
            cross_pkg_edges[(src_,_base64fns[source_id])] = set()
        try:
            if edge[2] == True:   #static
                cross_pkg_edges[(src_,_base64fns[source_id])].add((target_,_base64fns[target_id],"S"))
            else:                 #dynamic
                cross_pkg_edges[(src_,_base64fns[source_id])].add((target_,_base64fns[target_id],"D"))                
        except:                   #macro
                cross_pkg_edges[(src_,_base64fns[source_id])].add((target_,_base64fns[target_id],"M"))         

    if id(source_node,target_node):
        if (src_, _base64fns[source_id]) not in internal_package_edges:
            internal_package_edges[(src_,_base64fns[source_id])] = set() 
        internal_package_edges[(src_,_base64fns[source_id])].add((src_,_base64fns[target_id]))


for edge in cg['function_calls']:
    extract_edge_data(edge)


for edge in cg['macro_calls']:
    extract_edge_data(edge)


###
#### Find all connecting paths between client fns and dep functions
###

reverse_internal_edges = {}

for (s,ts) in internal_package_edges.items():
    for t in ts:
        if t not in reverse_internal_edges:
            reverse_internal_edges[t] = set()
        reverse_internal_edges[t].add(s)

def reach(travel_dict, x, visited=None):
    if visited is None:
        visited = set() 
    visited.add(x)

    for y in travel_dict.get(x, []):
        if y not in visited:
            yield y
            for z in reach(travel_dict, y, visited):
                yield z

###
#### Find entry-exit pairs 
###
paths = set()

for (s,ts) in cross_pkg_edges.items():
    for t in ts:
        paths.add((s,t))
    for y in reach(reverse_internal_edges,s): ## find connected internal ones to this one!
        for t in ts:
            paths.add((y,t))


unique = uuid.uuid4() 

###
#### Dump entrypoints to disk
###

for (krate,fns) in _mappings_crate_fns.items():
    name,ver = krate.split("::")
    if fns:
        crate_folder = "{}/{}/{}".format(sys.argv[4],name,ver)
        os.makedirs(crate_folder, exist_ok=True)

        filename = "{}/entrypoints-{}.txt".format(crate_folder,unique)
        with open(filename,"w+") as f:
            f.writelines(s + '\n' for s in fns)
        os.chmod(filename, 0o777)
###
#### Dump exitpoints and paths
###

for s in set([s for (s,t) in pkg_edges]):
    name,ver = s.split("::")    
    crate_folder = "{}/{}/{}".format(sys.argv[4],name,ver)


    ## Paths
    _paths = [(k[1],t[0],t[1],t[2])  for (k,t) in paths if k[0] == s]
    if _paths:
        filename = "{}/paths-{}.txt".format(crate_folder,unique)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename,"w+") as f:
            f.writelines(",".join(p) + '\n' for p in _paths)
        os.chmod(filename, 0o777)

    ## Exitpoints
    keys = [(k,fn) for (k,fn) in cross_pkg_edges.keys() if k == s]
    _deps = {}
    for k in keys:
        for (t,_fn,dispatch) in cross_pkg_edges[k]:
            if t not in _deps:
                _deps[t] = {"S": [], "D": [], "M": []}
            _deps[t][dispatch].append(_fn)

    for t in _deps.keys():
        filename = "{}/exitpoints/{}/static-{}.txt".format(crate_folder,t,unique)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename,"w+") as f:
            f.writelines(fn + '\n' for fn in _deps[t]['S'])
        os.chmod(filename, 0o777)

        filename = "{}/exitpoints/{}/cha-{}.txt".format(crate_folder,t,unique)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename,"w+") as f:
            f.writelines(fn + '\n' for fn in _deps[t]['D'])
        os.chmod(filename, 0o777)

        filename = "{}/exitpoints/{}/macro-{}.txt".format(crate_folder,t,unique)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename,"w+") as f:
            f.writelines(fn + '\n' for fn in _deps[t]['M'])
        os.chmod(filename, 0o777)