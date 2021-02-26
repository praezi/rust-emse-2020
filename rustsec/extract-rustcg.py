#!/usr/bin/python
# -*- coding: utf-8 -*-
# MIT License

# Copyright (c) 2021 Joseph Hejderup

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

# -*- coding: utf-8 -*-

""" 
   Run: python3 extract-rustcg.py callgraph.json type_hierarchy.json Cargo.lock 
"""

import copy
import json
import sys
import re
import os
import uuid

import toml

regex = r".+{{impl}}\[\d+\]"

# Data structures

## pkg_name::pkg_ver -> [dep1_name::dep1_ver,..,]

subtrees = {}

# Load raw cg

with open(sys.argv[1]) as cg_file:
    cg = json.load(cg_file)

# Load type hierarchy information

with open(sys.argv[2]) as cg_file:
    type_hir = json.load(cg_file)

# Extract dependency subtrees in the Cargo.lock file

with open(sys.argv[3], 'r') as fp:
    lockfile = toml.loads(fp.read())

   # Lookup table for dependencies without a version
   # A dependency without a version implies that there exists one specific of it.
   #

    _ver_table = {}
    for pkg in lockfile['package']:
        if pkg['name'] not in _ver_table:
            _ver_table[pkg['name']] = pkg['version']

    for pkg in lockfile['package']:
        crate_name = '{}::{}'.format(pkg['name'], pkg['version'])
        if crate_name not in subtrees:
            subtrees[crate_name] = set()

        if 'dependencies' in pkg:
            for dep in pkg['dependencies']:
                if ' ' in dep:
                    try:
                        dep_seg = dep.split(' ')
                        subtrees[crate_name].add('{}::{}'.format(dep_seg[0],
                                dep_seg[1]))
                    except:
                        print("Error:" + dep)
                else:
                    dep_name = dep
                    dep_ver = _ver_table[dep_name]
                    subtrees[crate_name].add('{}::{}'.format(dep_name,
                            dep_ver))


# create reverse subtree

rev_subtree = {}
for (k,vs) in subtrees.items():
   for v in vs:
      if v not in rev_subtree:
         rev_subtree[v] = list()
      rev_subtree[v].append(k)


# Group call graph data by package

packages = {}
_lookup_nodes = {}


## Process node data

def proc_node(fn, key):
    _lookup_nodes[fn['id']] = fn

    if fn['package_name'] is not None and fn['package_version'] \
        is not None:
        pkg_key = '{}::{}'.format(fn['package_name'],
                                  fn['package_version'])
        if pkg_key not in packages:
            packages[pkg_key] = {}
        if key not in packages[pkg_key]:
            packages[pkg_key][key] = list()
        packages[pkg_key][key].append(fn)


for fn in cg['functions']:
    proc_node(fn, 'functions')

for macro in cg['macros']:
    proc_node(macro, 'macros')


## Process edge data

def proc_edge(call, key_call, key_fn):
    src_fn = _lookup_nodes[call[0]]
    dst_fn = _lookup_nodes[call[1]]

    src_key = '{}::{}'.format(src_fn['package_name'],
                              src_fn['package_version'])
    dst_key = '{}::{}'.format(dst_fn['package_name'],
                              dst_fn['package_version'])

    if key_call not in packages[src_key]:
        packages[src_key][key_call] = list()


   # is a dep relation?

    if dst_key in subtrees[src_key]:
        dep_fn = copy.deepcopy(dst_fn)
        dep_fn['package_version'] = None  # remove version (make it unresolved)

        if key_fn not in packages[src_key]:
            packages[src_key][key_fn] = list()

        packages[src_key][key_fn].append(dep_fn)

        dep_call = copy.deepcopy(call)
        dep_call.append(False)  # unresolved function call

        packages[src_key][key_call].append(dep_call)
        return

   # is an internal call?

    if src_key == dst_key:
        internal_call = copy.deepcopy(call)
        internal_call.append(True)  # resolved function call
        packages[src_key][key_call].append(internal_call)
        return

   # is a std lib call?

    if 'None::None' == dst_key and 'None::None' != src_key:
        std_fn = copy.deepcopy(dst_fn)

        if key_fn not in packages[src_key]:
            packages[src_key][key_fn] = list()
        packages[src_key][key_fn].append(std_fn)

        std_call = copy.deepcopy(call)
        std_call.append(True)  # resolved function call
        packages[src_key][key_call].append(std_call)
        return

   # is std-to-std call?

    if 'None::None' == dst_key and 'None::None' == src_key:
        return   # skip

   # is a reverse dep call or transitive call? (virtual calls)
    if src_key in rev_subtree and dst_key in rev_subtree[src_key]:
      dep_fn = copy.deepcopy(src_fn)
      dep_fn['package_version'] = None  # remove version (make it unresolved)
      packages[dst_key][key_fn].append(dep_fn)

      dep_call = copy.deepcopy(call)
      dep_call.append(False)  # unresolved function call
      
      if key_call not in packages[dst_key]:
          packages[dst_key][key_call] = list()

      if key_fn not in packages[dst_key]:
          packages[dst_key][key_fn] = list()      
      packages[dst_key][key_call].append(dep_call)
      return


for call in cg['function_calls']:
    proc_edge(call, 'function_calls', 'functions')

for call in cg['macro_calls']:
    proc_edge(call, 'macro_calls', 'macros')

# lookup table for type information

_lookup_def_id = {}
_lookup_id_def = {}

for ty in type_hir['types']:
    _lookup_def_id[ty['relative_def_id']] = ty
    _lookup_id_def[ty['id']] = ty

for tr in type_hir['traits']:
    _lookup_def_id[tr['relative_def_id']] = tr
    _lookup_id_def[tr['id']] = tr

for impl in type_hir['impls']:
    _lookup_def_id[impl['relative_def_id']] = impl
    _lookup_id_def[impl['id']] = impl

# group by type information per package

package_types = {}  # pkg::ver -> {types, impls, traits}


def extract_types(def_id, pkg_ver):

      # There are three declerations we look into
      # 1. declared in a struct
      # 2. implementation of a struct
      # 3. declared in a module (like a static fn)

    if '{{impl}}' in def_id:  # trait impl
        for match in re.findall(regex, def_id):
            try:
                impl = copy.deepcopy(_lookup_def_id[match])

                if pkg_ver not in package_types:
                    package_types[pkg_ver] = {}
                if 'types' not in package_types[pkg_ver]:
                    package_types[pkg_ver]['types'] = list()
                if 'impls' not in package_types[pkg_ver]:
                    package_types[pkg_ver]['impls'] = list()
                if 'traits' not in package_types[pkg_ver]:
                    package_types[pkg_ver]['traits'] = list()

                if impl['package_name'] != None:
                    if impl['package_name'] not in pkg_ver:
                        impl['package_version'] = None

                package_types[pkg_ver]['impls'].append(copy.deepcopy(impl))

                if impl['type_id'] != None:
                    ty = _lookup_id_def[impl['type_id']]
                    if ty['package_name'] != None: 
                        if ty['package_name'] not in pkg_ver:
                            ty['package_version'] = None
                    package_types[pkg_ver]['types'].append(copy.deepcopy(ty))

                if impl['trait_id'] != None:
                    tr = _lookup_id_def[impl['trait_id']]

                    if tr['package_name'] != None: 
                        if tr['package_name'] not in pkg_ver:
                            tr['package_version'] = None                   
                    package_types[pkg_ver]['traits'].append(copy.deepcopy(tr))
            except:
                pass # no impl details of std crates (TODO)
        return
    else:
        try:
            ty = _lookup_def_id[def_id]  # method in struct
            if pkg_ver not in package_types:
                package_types[pkg_ver] = {}
            if 'types' not in package_types[pkg_ver]:
                package_types[pkg_ver]['types'] = list()
            if ty['package_name'] != None: 
                if ty['package_name'] not in pkg_ver:
                    ty['package_version'] = None              
            package_types[pkg_ver]['types'].append(copy.deepcopy(ty))
            return
        except:
            return   # function in module (no type information)


for (pkg, cg) in packages.items():
    for fn in cg.get('functions', list()):
        def_id = fn['relative_def_id']
        extract_types(def_id, pkg)

    for m in cg.get('macros', list()):
        def_id = m['relative_def_id']
        extract_types(def_id, pkg)


# prune prefix in `relative_def_id`

def prune_prefix_crate_name(def_id):
      def_id_seg = def_id.split("::")
      crate_name = def_id_seg[0].split("[")[0]
      def_id_seg[0] = crate_name
      return "::".join(def_id_seg)


for (pkg, cg) in packages.items():
    for fn in cg.get('functions', list()):
        fn['relative_def_id'] =  prune_prefix_crate_name(fn['relative_def_id'])

    for m in cg.get('macros', list()):
       m['relative_def_id'] =  prune_prefix_crate_name(m['relative_def_id'])

for (pkg, pty) in package_types.items():
      for ty in pty.get('types',list()):
         if ty['relative_def_id'] != None: #primitive types do not have a relative_def_id
            ty['relative_def_id'] =  prune_prefix_crate_name(ty['relative_def_id'])
      for tr in pty.get('traits',list()):    
         if tr['relative_def_id'] != None:
             tr['relative_def_id'] =  prune_prefix_crate_name(tr['relative_def_id'])
      for impl in pty.get('impls',list()):  
         if impl['relative_def_id'] != None:        
            impl['relative_def_id'] =  prune_prefix_crate_name(impl['relative_def_id'])


# remove duplicates in lists

def unique_list(l):
    return [dict(t) for t in {tuple(d.items()) for d in l}]

for (pkg, cg) in packages.items():

   if 'functions' in cg:
      cg['functions'] = unique_list(cg.get('functions'))

   if 'macros' in cg:
      cg['macros'] = unique_list(cg.get('macros'))

for (pkg, tyhir) in package_types.items():

   if 'types' in tyhir:
      tyhir['types'] = unique_list(tyhir.get('types'))

   if 'traits' in tyhir:
      tyhir['traits'] = unique_list(tyhir.get('traits'))

   if 'impls' in tyhir:
      tyhir['impls'] = unique_list(tyhir.get('impls'))


# dump to disk 

for (pkg, cg) in packages.items():
   uuid_str = uuid.uuid4()
   pkg_name, pkg_ver = pkg.split("::")
   filename = '/mnt/fasten/cratesio/{}/{}/callgraph-{}.json'.format(pkg_name,pkg_ver,uuid_str)
   os.makedirs(os.path.dirname(filename), exist_ok=True)
   with open(filename,'w+') as outfile:
      json.dump(cg,outfile)

   if pkg in package_types:
    tyhir = package_types[pkg] 
    filename = '/mnt/fasten/cratesio/{}/{}/type_hierarchy-{}.json'.format(pkg_name,pkg_ver,uuid_str)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename,'w+') as outfile:
        json.dump(tyhir,outfile)    



