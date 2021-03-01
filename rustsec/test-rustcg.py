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
   Run: python3 test-rustcg.py callgraph.json type_hierarchy.json
"""

import json 
import sys
import re

regex = r".+{{impl}}\[\d+\]"

# Load raw cg

with open(sys.argv[1] + "/callgraph.json") as cg_file:
    cg = json.load(cg_file)

# Load type hierarchy information
try:
    with open(sys.argv[1] + "/type_hierarchy.json") as cg_file:
        type_hir = json.load(cg_file)
except:
    with open(sys.argv[1] + "/type_hierarchy.json", 'w+') as ty_file:
        empty = {}
        empty['types'] = list()
        empty['traits'] = list()
        empty['impls'] = list()
        json.dump(empty,ty_file)
    sys.exit(0)


# Lookup table for types

# lookup table for type information

_lookup_def_id = {}
_lookup_id_def = {}

for ty in type_hir.get('types',list()):
    def_id = ty['relative_def_id']
    if ty['package_name'] is not None:
        def_id = ty['package_name']  + ty['relative_def_id']
    
    _lookup_def_id[def_id] = ty
    _lookup_id_def[ty['id']] = ty

for tr in type_hir.get('traits',list()):
    def_id = tr['relative_def_id']
    if tr['package_name'] is not None:
        def_id = tr['package_name']  + tr['relative_def_id']
    _lookup_def_id[def_id] = tr
    _lookup_id_def[tr['id']] = tr

for impl in type_hir.get('impls',list()):
    def_id = impl['relative_def_id']
    if impl['package_name'] is not None:
        def_id = impl['package_name']  + impl['relative_def_id']
    
    _lookup_def_id[def_id] = impl   
    _lookup_id_def[impl['id']] = impl

# check if def_id is in the type information

std = set(["core","std","alloc","proc_macro","test","rustc_span","getopts"])

def check_type(def_id, package_name=None):

      # There are three declerations we look into
      # 1. declared in a struct
      # 2. implementation of a struct
      # 3. declared in a module (like a static fn)

    if '{{impl}}' in def_id:  # trait impl
        for match in re.findall(regex, def_id):
            try:
                if package_name is not None:
                    match = package_name + match
                _lookup_def_id[match]
            except:
                if match.split("::")[0] not in std:
                    raise Exception("Missing trait implementation in the call graph!")
    else:
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
   Run: python3 test-rustcg.py callgraph.json type_hierarchy.json
"""

import json 
import sys
import re

regex = r".+{{impl}}\[\d+\]"

# Load raw cg

with open(sys.argv[1] + "/callgraph.json") as cg_file:
    cg = json.load(cg_file)

# Load type hierarchy information
try:
    with open(sys.argv[1] + "/type_hierarchy.json") as cg_file:
        type_hir = json.load(cg_file)
except:
    with open(sys.argv[1] + "/type_hierarchy.json", 'w+') as ty_file:
        empty = {}
        empty['types'] = list()
        empty['traits'] = list()
        empty['impls'] = list()
        json.dump(empty,ty_file)
    sys.exit(0)


# Lookup table for types

# lookup table for type information

_lookup_def_id = {}
_lookup_id_def = {}

for ty in type_hir.get('types',list()):
    def_id = ty['relative_def_id']
    if ty['package_name'] is not None:
        def_id = ty['package_name']  + ty['relative_def_id']
    
    _lookup_def_id[def_id] = ty
    _lookup_id_def[ty['id']] = ty

for tr in type_hir.get('traits',list()):
    def_id = tr['relative_def_id']
    if tr['package_name'] is not None:
        def_id = tr['package_name']  + tr['relative_def_id']
    _lookup_def_id[def_id] = tr
    _lookup_id_def[tr['id']] = tr

for impl in type_hir.get('impls',list()):
    def_id = impl['relative_def_id']
    if impl['package_name'] is not None:
        def_id = impl['package_name']  + impl['relative_def_id']
    
    _lookup_def_id[def_id] = impl   
    _lookup_id_def[impl['id']] = impl

# check if def_id is in the type information

std = set(["core","std","alloc","proc_macro","test","rustc_span","getopts"])

def check_type(def_id, package_name=None):

      # There are three declerations we look into
      # 1. declared in a struct
      # 2. implementation of a struct
      # 3. declared in a module (like a static fn)

    if '{{impl}}' in def_id:  # trait impl
        for match in re.findall(regex, def_id):
            try:
                if package_name is not None:
                    match = package_name + match
                _lookup_def_id[match]
            except:
                if match.split("::")[0] not in std:
                    raise Exception("Missing trait implementation in the call graph!")
    else:
        try:
            if package_name is not None:
                 def_id = package_name + def_id
            _lookup_def_id[def_id]

            def_segs = def_id.split("::")
            def_segs.pop()
            def_id = "::".join(def_segs)
            if package_name is not None:
                def_id = package_name + def_id
            _lookup_def_id[def_id]
        except:
            try:
                def_segs = def_id.split("::")
                def_segs.pop()
                def_id = "::".join(def_segs)
                _lookup_def_id[def_id]             
            except:
                pass # we cannot fully validate this

for fn in cg.get('functions', list()):
    def_id = fn['relative_def_id']
    if 'package_name' in fn and fn['package_name'] is not None:
        check_type(def_id, fn['package_name'])
    else:
        check_type(def_id)       

for m in cg.get('macros', list()):
    def_id = m['relative_def_id']
    if 'package_name' in m and m['package_name'] is not None:
        check_type(def_id, m['package_name'])
    else:
        check_type(def_id)       


for fn in cg.get('functions', list()):
    def_id = fn['relative_def_id']
    if 'package_name' in fn and fn['package_name'] is not None:
        check_type(def_id, fn['package_name'])
    else:
        check_type(def_id)       

for m in cg.get('macros', list()):
    def_id = m['relative_def_id']
    if 'package_name' in m and m['package_name'] is not None:
        check_type(def_id, m['package_name'])
    else:
        check_type(def_id) 