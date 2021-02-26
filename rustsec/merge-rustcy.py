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
   Run: python3 extract-rustcg.py <path_package_dir>
   Example: python3 extract-rustcg.py /mnt/fasten/cratesio/wayland-client/0.25.0
"""

import json
import sys
import glob
import itertools
import os

package_dir = sys.argv[1]

# list of cgs
cgs = list()

# list of tyhir
tyhirs = list()

# load all call graphs
for cg_path in glob.glob('{}/callgraph-*.json'.format(package_dir)):
    cgs.append(cg_path)

# load all type hierarchies
for typhir_path in glob.glob('{}/type_hierarchy-*.json'.format(package_dir)):
    tyhirs.append(typhir_path)



# pop one cg as the seed cg
merged_cg_path = cgs.pop()

with open(merged_cg_path) as cg_file:
    merged_cg = json.load(cg_file)

if 'macros' not in merged_cg:
    merged_cg['macros'] = list()

if 'functions' not in merged_cg:
    merged_cg['functions'] = list()

if 'function_calls' not in merged_cg:
    merged_cg['function_calls'] = list()

if 'macro_calls' not in merged_cg:
    merged_cg['macro_calls'] = list()


# mappings of old to new ids
old2new = {}

# mappings path_def to new ids
pathdef2id_macro = {}
pathdef2id_fns = {}

# id_counter
idc = 1

for item in merged_cg['functions']:
    # link relative_def_id to new idc

    #relative_def_id is sometimes not unique. This happens when for example a
    #function and a macro has the same name. To distirngush, we use the file
    #path and its position in the file as a way to distingush.
    if 'source_location' in item and item['source_location'] is not None: 
        pathdef2id_fns[item['relative_def_id'] + item['source_location']] = idc    
    else:
        pathdef2id_fns[item['relative_def_id']] = idc  
    # map old id to the new id
    old2new[item['id']] = idc
    # replace the old id with the new one
    item['id'] = idc
    # increment counter        
    idc += 1

for item in merged_cg.get('macros',list()):
    # link relative_def_id to new idc

    #relative_def_id is sometimes not unique. This happens when for example a
    #function and a macro has the same name. To distirngush, we use the file
    #path and its position in the file as a way to distingush.
    if 'source_location' in item and item['source_location'] is not None:
        pathdef2id_macro[item['relative_def_id'] + item['source_location']] = idc  
    else:
        pathdef2id_macro[item['relative_def_id']] = idc   
    # map old id to the new id
    old2new[item['id']] = idc
    # replace the old id with the new one
    item['id'] = idc
    # increment counter      
    idc += 1

# re-map edges

def edge_remap(edge):
    edge[0] = old2new[edge[0]]
    edge[1] = old2new[edge[1]]


for e in merged_cg.get('function_calls',list()):
    edge_remap(e)

for e in merged_cg.get('macro_calls',list()):
    edge_remap(e)

# helper functinos to remove duplicates in list of objects and list of lists

def unique_list_of_list(k):
    k.sort()
    return list(k for k,_ in itertools.groupby(k))

def unique_list(l):
    return [dict(t) for t in {tuple(d.items()) for d in l}]

# remove duplicate edges (should have done before at the split stage!)

if 'function_calls' in merged_cg:
    merged_cg['function_calls'] = unique_list_of_list(merged_cg.get('function_calls'))

if 'macro_calls' in merged_cg:
    merged_cg['macro_calls'] = unique_list_of_list(merged_cg.get('macro_calls'))


before_cg_str = "[{}] Before --- number of functions: {}, macros: {}, function_edges: {}, macro_edges: {}".format(package_dir,len(merged_cg['functions']),len(merged_cg.get('macros',list())),len(merged_cg['function_calls']),len(merged_cg.get('macro_calls',list())))

# integrate calls from other call graphs
while cgs:
#    print("Remaining cgs: {}".format(len(cgs)))
    # load a new cg from the pool of cgs
    cg_path = cgs.pop()
    with open(cg_path) as cg_file:
        cg = json.load(cg_file)

    # reset mapping of old to new ids that ios needed for edge rewrite
    old2new = {}

    for item in cg.get('functions',list()):
        def_id = item['relative_def_id']
        if 'source_location' in item and item['source_location'] is not None:
            def_id = item['relative_def_id'] + item['source_location']
        #does this item already exist in the merged cg ?    
        if def_id in pathdef2id_fns: 
            old2new[item['id']] = pathdef2id_fns[def_id]
        else: #no, it does not, add it to the list
            pathdef2id_fns[def_id] = idc
            old2new[item['id']] = idc
            item['id'] = idc
            idc += 1
            merged_cg['functions'].append(item)

    for item in cg.get('macros',list()):
        def_id = item['relative_def_id']
        if 'source_location' in item and item['source_location'] is not None:
            def_id = item['relative_def_id'] + item['source_location']
        #does this item already exist in the merged cg ?  
        if def_id in pathdef2id_macro:
            old2new[item['id']] = pathdef2id_macro[def_id]
        else: #no, it does not, add it to the list
            pathdef2id_macro[def_id] = idc
            old2new[item['id']] = idc
            item['id'] = idc
            idc += 1
            merged_cg['macros'].append(item)
    
    # remap ids in call edges and add it to the list of calls
    for e in cg.get('function_calls',list()):
        edge_remap(e)
        merged_cg['function_calls'].append(e)

    for e in cg.get('macro_calls',list()):
        edge_remap(e)
        merged_cg['macro_calls'].append(e)
    
    # remove duplicate entries where available 

    if 'functions' in merged_cg:
        merged_cg['functions'] = unique_list(merged_cg.get('functions'))

    if 'macros' in merged_cg:
        merged_cg['macros'] = unique_list(merged_cg.get('macros'))

    if 'function_calls' in merged_cg:
        merged_cg['function_calls'] = unique_list_of_list(merged_cg.get('function_calls'))

    if 'macro_calls' in merged_cg:
        merged_cg['macro_calls'] = unique_list_of_list(merged_cg.get('macro_calls'))
    
    cg = {}


after_cg_str = "[{}] After --- number of functions: {}, macros: {}, function_edges: {}, macro_edges: {}".format(package_dir,len(merged_cg['functions']),len(merged_cg.get('macros',list())),len(merged_cg['function_calls']),len(merged_cg.get('macro_calls',list())))


# save the merged callgraph

filename = '{}/callgraph.json'.format(package_dir)
os.makedirs(os.path.dirname(filename), exist_ok=True)

with open(filename,'w+') as outfile:
    json.dump(merged_cg,outfile)

merged_cg = {}
##############################################################################################
#### TYPE INFORMATION MERGE
##############################################################################################


if len(tyhirs) < 1:
    print(before_cg_str + '\n' + after_cg_str)
    sys.exit()


merged_tyhir_path = tyhirs.pop() 

with open(merged_tyhir_path) as ty_file:
    merged_tyhir = json.load(ty_file)

# ensure the merged file has all properties

if 'types' not in merged_tyhir:
    merged_tyhir['types'] = list()

if 'traits' not in merged_tyhir:
    merged_tyhir['traits'] = list()

if 'impls' not in merged_tyhir:
    merged_tyhir['impls'] = list()

# map old to new ids
old2new = {}

# def_id -> new_id
pathdef2id_types = {}
pathdef2id_traits = {}
pathdef2id_impls = {}
# int,float,generic, etc -> new_id
primitive2id_types = {}

# id_counter
idc = 1

###
#### Before processing implementations, traits and types needs to be processed first.
###

for item in merged_tyhir.get('types',list()):
    # the relative_def_id can be identical across different packages. To ensure
    # their uniquiness, we combine both the relative_def_id with the
    # package_name if avaialable. When it is not available, the type belongs to
    # the standard library.
    if item['relative_def_id'] is not None:
        def_id = item['relative_def_id']
        if item['package_name'] is not None:
            def_id = item['package_name'] + item['relative_def_id']
        # link relative_def_id to new idc
        pathdef2id_types[def_id] = idc
        # link old index value to new one
        old2new[item['id']] = idc
        # replace with a new one
        item['id'] = idc
        # increment counter        
        idc += 1
    # when there isnt a relative_def_id, it is a primitive type
    # a primitive type is represented under the string_id
    # NB: generic types are also represented here!
    elif item['relative_def_id'] is None:
        def_id = item['string_id']
        if item['package_name'] is not None:
            def_id = item['package_name'] + item['string_id']        
        primitive2id_types[def_id] = idc 
        old2new[item['id']] = idc
        # replace with a new one
        item['id'] = idc
        # increment counter        
        idc += 1     

for item in merged_tyhir.get('traits',list()):
    # the relative_def_id can be identical across different packages. To ensure
    # their uniquiness, we combine both the relative_def_id with the
    # package_name if avaialable. When it is not available, the trait belongs to
    # the standard library.    
    if item['relative_def_id'] is not None:
        def_id = item['relative_def_id']
        if item['package_name'] is not None:
            def_id = item['package_name'] + item['relative_def_id']
        # link relative_def_id to new idc
        pathdef2id_traits[def_id] = idc
        # link old index value to new one
        old2new[item['id']] = idc
        # replace with a new one
        item['id'] = idc
        # increment counter        
        idc += 1
    else:
        raise Exception("trait without realative_def_id!")        
   
for item in merged_tyhir.get('impls',list()):
    # although the impl id is not important, we still add a unique one
    if item['relative_def_id'] is not None:
        def_id = item['relative_def_id']
        if item['package_name'] is not None:
            def_id = item['package_name'] + item['relative_def_id']
        # link relative_def_id to new idc
        pathdef2id_impls[def_id] = idc
        # link old index value to new one
        old2new[item['id']] = idc
        # replace with a new one
        item['id'] = idc
        # increment counter        
        idc += 1

        # process refs
        if item['type_id'] is not None:
            item['type_id'] = old2new[item['type_id']]
        if item['trait_id'] is not None:            
            item['trait_id'] = old2new[item['trait_id']]
    else:
        raise Exception("impl without realative_def_id!")     

before_ty_str = "[{}] Before --- number of types: {}, traits: {}, impls: {}".format(package_dir,len(merged_tyhir['types']),len(merged_tyhir['traits']),len(merged_tyhir['impls']))

while tyhirs:
#    print("Remaining tyhir: {}".format(len(tyhirs))) 
    # load a new tyhur from the pool of typ hirs
    ty_path = tyhirs.pop()
    with open(ty_path) as ty_file:
        ty = json.load(ty_file)

    # reset mapping of old to new ids
    old2new = {}

    for item in ty.get('types',list()):

        if item['relative_def_id'] is not None:
            def_id = item['relative_def_id']
            if item['package_name'] is not None:
                def_id = item['package_name'] + item['relative_def_id']
            
            # does the type already exist in the merged tyhir?
            if def_id in pathdef2id_types:
                # get the existing id and add a mapping 
                old2new[item['id']] = pathdef2id_types[def_id]
            else: # does not exist, then lets add it 
                # link relative_def_id to new idc
                pathdef2id_types[def_id] = idc
                # link old id to new one
                old2new[item['id']] = idc
                # replace with a new one
                item['id'] = idc
                # increment counter        
                idc += 1        
                merged_tyhir['types'].append(item)   
        elif item['string_id'] is not None: # not a relative def, then it is a simple type
            def_id = item['string_id']
            if item['package_name'] is not None:
                def_id = item['package_name'] + item['string_id']            

            if def_id in primitive2id_types:
                 old2new[item['id']] = primitive2id_types[def_id]
            else:
                # link relative_def_id to new idc
                primitive2id_types[def_id] = idc
                # link old id to the new one
                old2new[item['id']] = idc
                # replace with a new one
                item['id'] = idc
                # increment counter        
                idc += 1        
                merged_tyhir['types'].append(item)   
        else:
             raise Exception("we got an odd type here!")                      
        
    for item in ty.get('traits',list()):
        if item['relative_def_id'] is not None: 
            def_id = item['relative_def_id']
            if item['package_name'] is not None:
                def_id = item['package_name'] + item['relative_def_id']
                
            if def_id in pathdef2id_traits:
                old2new[item['id']] = pathdef2id_traits[def_id]
            else:
                pathdef2id_traits[def_id] = idc
                old2new[item['id']] = idc
                item['id'] = idc     
                idc += 1        
                merged_tyhir['traits'].append(item)    
        else:
            raise Exception("trait without a relative_def_id!")   

    for item in ty.get('impls',list()):
        if item['relative_def_id'] is not None:
            def_id = item['relative_def_id']
            if item['package_name'] is not None:
                def_id = item['package_name'] + item['relative_def_id']

            if def_id in pathdef2id_impls:
                 old2new[item['id']] = pathdef2id_impls[def_id]
            else:
                pathdef2id_impls[def_id] = idc
                old2new[item['id']] = idc
                item['id'] = idc
                idc += 1     

                if item['type_id'] is not None:
                    item['type_id'] = old2new[item['type_id']]
                if item['trait_id'] is not None:            
                    item['trait_id'] = old2new[item['trait_id']]                    
                merged_tyhir['impls'].append(item)    
        else:
            raise Exception("impl without a relative_def_id!")   

filename = '{}/type_hierarchy.json'.format(package_dir)
os.makedirs(os.path.dirname(filename), exist_ok=True)

with open(filename,'w+') as outfile:
    json.dump(merged_tyhir,outfile)

after_ty_str = "[{}] After --- number of types: {}, traits: {}, impls: {}".format(package_dir,len(merged_tyhir['types']),len(merged_tyhir['traits']),len(merged_tyhir['impls']))

print(before_cg_str + '\n' + after_cg_str + '\n' + before_ty_str + '\n' + after_ty_str)
