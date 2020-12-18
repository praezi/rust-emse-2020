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
# -*- coding: utf-8 -*-
""" 
   Builds a PDN/CDN for new releases at a timestamp t. The resolution mechanism is based on using the latest available version at time t. Practically, the resolution is different but we use this assumption.
   Run: python3 evolysis-rustcg.py timestamp
"""
import sys
import json
import base64
import os 
import glob
import fnmatch
import collections

from ctypes import cdll, c_bool, c_void_p, cast, c_char_p, c_int32
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta


import pandas as pd
import numpy as np
import networkx as nx


####
##### SETUP RUST VERSION RESOLVER
####

RUST = cdll.LoadLibrary("target/release/libsemver_ffi.so")

RUST.is_match.argtypes = (c_void_p,c_void_p)
RUST.is_match.restype = c_bool
RUST.cmp.argtypes = (c_void_p,c_void_p)
RUST.cmp.restype = c_int32

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K


####
##### Blacklist
####

### js code: 
###   var ab = Array.from(document.getElementsByClassName("ember-view _name_s6xett")).map(x => '"' + x.innerText.trim() + '"').join(",")
###   console.log(ab)

### pages: https://crates.io/categories/os::windows-apis?sort=alpha
windows = set([
    "amsi","autopilot","cfile","clipboard-win","com","comedy","d3d12","detours","detours-sys", \
    "dhc","dl_api","druid-shell","druid-win-shell","elbow-grease","embed-resource","eventlog","fd-lock","fenestroj","filetime_win", \
    "guid_win","hcs-rs","iui","junction","lawrencium","lock_keys","lpwstr","mail_slot","mem_file","mscorlib-safe", \
    "mscorlib_safe_derive","mscorlib-sys","ntapi","nt_native","nt_version","nvim_windows_remote","oaidl","palaver","proxyconf","raw_sync", \
    "serial-windows","shared_memory","shared_memory_derive","stop-thread","system_shutdown","thin_main_loop","tlhelp32","uds_windows","ui-sys","verona", \
    "virtdisk-rs","vmsavedstatedump_rs","w32-error","wallpaper-windows-user32","wepoll-binding","wepoll-sys","wepoll-sys-stjepang","wexit","wfd","wil", \
    "wild","win32console","win32job","win32_notification","winapi","winapi-easy","winapi_forked_icmpapi","winapi-util","winbluetooth","win-crypto-ng", \
    "windows-acl","windows-dll","windows-dll-codegen","windows-permissions","windows-service","winhandle","winlog","win-msg-name","winpty-sys","winreg", \
    "winutils-rs","win-win","wio","wmi","wstr"])

# pages: https://crates.io/categories/os::macos-apis 
macos = set([
    "core-foundation","security-framework","security-framework-sys","darwin-libproc-sys","darwin-libproc","druid-shell","palaver","system-configuration-sys","system-configuration","pfctl", \
    "autopilot","ui-sys","iui","system_shutdown","ash-molten","fd-lock","fse_dump","nightlight","xcrun","passkit", \
    "core_bluetooth","core-services","filedesc","iron-oxide","addy","objrs","ds_store","objrs_frameworks_foundation","ptrauth-sys","apply-user-defaults", \
    "objrs_frameworks_app_kit","objrs_frameworks_core_graphics","objrs_frameworks_metal","objrs_frameworks_metal_kit","ituneslibrary-sys","lock_keys","coreutils_core","cacao","elbow-grease","cargo-cider", \
    "posix-socket"])


## 
## find . -type f -exec cat {} \; | jq .deps[].target | sort | uniq > ../targets.txt
targets = set(["x86_64-unknown-linux-gnu","x86_64-unknown-linux-musl","i686-unknown-linux-gnu","i586-unknown-linux-gnu", \
    "cfg(unix)", "cfg(target_os = \"linux\")", "cfg(target_family = \"unix\")", "cfg(not(windows))", \
    "cfg(not(target_arch = \"wasm32\"))", "cfg(not(target_env = \"msvc\"))", "cfg(not(target_os = \"emscripten\"))", \
    "cfg(not(target_os = \"macos\"))", "cfg(not(target_os = \"unknown\"))", "cfg(not(target_os = \"windows\"))", \
    "cfg(any(unix, macos))", "cfg(any(target_os = \"linux\", target_os = \"android\"))", \
    "cfg(any(target_os = \"linux\", target_os = \"dragonfly\", target_os = \"freebsd\"))", \
    "cfg(any(target_os = \"linux\", target_os = \"dragonfly\", target_os = \"freebsd\", target_os = \"openbsd\"))", \
    "cfg(all(unix, not(any(target_os = \"emscripten\", target_os = \"unknown\"))))", "cfg(all(unix, not(target_os = \"emscripten\")))", \
    "cfg(all(unix, not(target_os = \"macos\")))","cfg(all(unix, not(target_os = \"redox\")))"
    ])
####
##### CREATE LOOKUP TABLES
####

#### Release table with timestamps
##   name -> [(ts,v),()]
_releases = {}
#### Docs.rs build table
## name::ver -> true | false
_docsrs  = {}

#### Dependency Table
## name::ver -> ["(d1,r1),..,etc"]
_dependencies = {}

#### Features Table
_features = {}


with open("releases.csv") as f:
    for line in f:
        ts, _name, _ver = line.rstrip().replace('\\"', "").strip('"').split(",")

        if _name not in _releases:
            _releases[_name] = set()
        
        _releases[_name].add((_ver,ts))

with open("docsrs.csv") as ft:
    for line in ft:
        _name,_ver,_status,_c,_d,_y = line.rstrip().split(",")
        crate_key = "{}::{}".format(_name, _ver)
        if _status == "True":
            _docsrs[crate_key]  = True
        else:
            _docsrs[crate_key] = False


def valid_dep(d):
    return 'kind' in d \
            and (d['kind'] == 'normal' or d['kind'] == 'build') \
                and (d['target'] == None or d['target'] in targets) 
            
for path in Path("crates.io-index").glob('**/*'):
    if path.is_file() and "config.json" not in path.name and "crates.io-index/.git/" not in str(path):
        with path.open() as idx_fh:
            for raw_entry in idx_fh.readlines():
                entry = json.loads(raw_entry)
                if entry['name'] not in windows and entry['name'] not in macos: #do not process macos/windows packages
                    crate_key = "{}::{}".format(entry['name'],entry['vers'])
                    if crate_key not in _features:
                        _features[crate_key] = entry['features']
                    if crate_key not in _dependencies:
                        _dependencies[crate_key] = list()
                        for d in entry['deps']:
                            if valid_dep(d):
                                if 'package' in d:
                                    d_name = d['package']
                                else:
                                    d_name = d['name']
                                if d_name not in windows and d_name not in macos: #remove macos/windows packages in deps
                                    _dependencies[crate_key].append((d_name, d['req'],d['features'], d['optional'], d['default_features']))

####
##### Parse time interval
####
ts = sys.argv[1]
ts_year,ts_month = ts.split("-")
ts_day=15 #latest day of the index is 14th Feb 2020

# A valid release is with in t and t-1 
dt_max = datetime(int(ts_year),int(ts_month),int(ts_day))
dt_min = dt_max - relativedelta(months=1)

####
###### Generate snapshots for the three variables
####

def parse_ts(ts):
    try:
        return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f+00:00')
    except:
        return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S+00:00')

def is_docsrs_valid(p,v):
    return _docsrs.get("{}::{}".format(p,v),False) 

def is_praezi_valid(p,v):
    return os.path.isdir("/datasets/praezi/stitching/{}/{}/".format(p,v))

# name -> [v1,v2,v3,..]
_docsrs_snapshot= {}
_praezi_snapshot = {}
_index_snapshot = {}

for (p,vs) in _releases.items():
    for (v,v_ts) in vs:
        v_dt = parse_ts(v_ts)
        # is this a version for dependencies?
        if v_dt.date() <= dt_max.date():
            # index (no checks)
            if p not in _index_snapshot:
                _index_snapshot[p] = set()
            _index_snapshot[p].add(v)
            # docsrs
            if is_docsrs_valid(p,v):
                if p not in _docsrs_snapshot:
                    _docsrs_snapshot[p] = set()
                _docsrs_snapshot[p].add(v)
            # praezi
            if is_praezi_valid(p,v):
                if p not in _praezi_snapshot:
                    _praezi_snapshot[p] = set()
                _praezi_snapshot[p].add(v)

# ####
# ###### Calculate Package-level Closure 
# ####

def is_valid_dep(d_name, d_optional, enabled_optionals):
    if d_optional == False:
        return True
    else:
        return d_name in set(enabled_optionals)

def flatten_features(keys, dict):
    flatten = []
    for key in keys: 
        if key in dict:
            flatten = flatten + flatten_features(dict[key], dict)
        else:
            flatten.append(key)
    return flatten


def resolve_features(d_krate,d_features,d_optional,d_default_features, features):
    # Scenario: no optional, no default features, and no default features requested
    enabled_deps = []
    if d_optional == False and d_default_features == False and not d_features:
        return enabled_deps
    # Scenario: default features enabled
    if d_default_features:
        #1. check if there are features for this particulat package and then fetch default features
        if d_krate in features and "default" in features[d_krate]:
            enabled_deps = enabled_deps + list(flatten_features(["default"], features[d_krate]))
    #Scenario: enabled features
    if d_features:
        if d_krate in features:
                    enabled_deps = enabled_deps + list(flatten_features(d_features, features[d_krate]))
    return list(set(enabled_deps))

def resolve(krate, enabled_optionals, dependencies, features, releases, visited=None):
    if visited == None:
        visited = set() 
    visited.add(krate + str(sorted(enabled_optionals)))

    transitve_opts = {}
    for opt in enabled_optionals:
        if "/" in opt:
            dep, feature = opt.split("/")
            if dep not in transitve_opts:
                transitve_opts[dep] = []
            transitve_opts[dep].append(feature)
            
    for (d_name,d_req,d_features,d_optional,d_default_features) in dependencies.get(krate,[]):
        if is_valid_dep(d_name, d_optional, enabled_optionals):
            r = releases[d_name]
            d_vs = [d_ver.encode('ascii') for d_ver in r if RUST.is_match(d_req.encode('ascii'),d_ver.encode('ascii'))]
            d_vs = [d_ver.decode('ascii') for d_ver in sorted(d_vs, key=cmp_to_key(RUST.cmp))]
            if not d_vs:
                raise Exception("Incomplete Dependency Tree")
            d_v = d_vs.pop()
            d_krate = "{}::{}".format(d_name,d_v)
            yield (krate,d_krate)
            enabled_optionals = resolve_features(d_krate,d_features,d_optional,d_default_features, features)
            if d_name in transitve_opts:
                enabled_optionals = enabled_optionals + list(flatten_features(transitve_opts[d_name], features[d_krate])) 
            if d_krate + str(sorted(enabled_optionals)) not in visited:
                for z_krate in resolve(d_krate, enabled_optionals, dependencies,features, releases, visited):
                    yield z_krate

def dep_closure(_snapshot, _dependencies, _features):
    pkgs = {}
    for p,vs in _snapshot.items():
        vs = _snapshot[p]
        vs = [v.encode("ascii") for v in vs]
        vs = [v.decode('ascii') for v in sorted(vs, key=cmp_to_key(RUST.cmp))]

        resolved_tree = []
        while vs:
            v = vs.pop()
            krate = "{}::{}".format(p,v)
            try:
                resolved_tree = list(resolve(krate,[],_dependencies,_features,_snapshot))
            except Exception as e:
                continue
            break #we dont need to continue, we have a resolved release from this package

        if resolved_tree:
            if krate not in pkgs:
                pkgs[krate] = []
            for d in resolved_tree:
                pkgs[krate].append(d)

    return pkgs 

# ####
# ###### Calculate Function-level Closure 
# ####

_cache = {}
def get_entrypoints(krate):
    if krate in _cache:
        return _cache[krate]
    p,v= krate.split("::")
    folder = "/datasets/praezi/stitching/{}/{}".format(p,v)
    entrypoints = set()
    for entry_file in os.listdir(folder):
        if fnmatch.fnmatch(entry_file, 'entrypoints-*.txt'):
            entrypoints = entrypoints.union(set([line.rstrip('\n') for line in open("{}/{}".format(folder,entry_file))]))
    _cache[krate] = entrypoints
    return entrypoints

_paths_cache = {}
def get_paths(krate):
    if krate in _paths_cache:
        return _paths_cache[krate]
    p,v= krate.split("::")
    folder = "/datasets/praezi/stitching/{}/{}".format(p,v)
    paths = {}
    for paths_file in os.listdir(folder):
        if fnmatch.fnmatch(paths_file, 'paths-*.txt'):
            for call in [line.rstrip('\n') for line in open("{}/{}".format(folder,paths_file))]:
                s_fn, t_name, t_fn, t_dispatch = call.split(",")
                if s_fn not in paths:
                    paths[s_fn] = set()
                paths[s_fn].add((t_name,t_fn,t_dispatch))
    _paths_cache[krate] = paths
    return paths

def resolve_with_cg(krate, krate_eps, enabled_optionals, dependencies, features, releases, visited=None):
    # Add to visited 
    if visited == None:
        visited = set() 
    visited.add(krate + str(sorted(enabled_optionals)))
    # Inspect if we have enabled options for dependencies
    transitve_opts = {}
    for opt in enabled_optionals:
        if "/" in opt:
            dep, feature = opt.split("/")
            if dep not in transitve_opts:
                transitve_opts[dep] = []
            transitve_opts[dep].append(feature)
    
    # Fetch call paths for this package version
    krate_paths = get_paths(krate)
            
    for (d_name,d_req,d_features,d_optional,d_default_features) in dependencies.get(krate,[]):
        if is_valid_dep(d_name, d_optional, enabled_optionals):
            if d_name not in releases:
                raise Exception("Missing Call Graphs for package: " + d_name)
            r = releases[d_name]
            d_vs = [d_ver.encode('ascii') for d_ver in r if RUST.is_match(d_req.encode('ascii'),d_ver.encode('ascii'))]
            d_vs = [d_ver.decode('ascii') for d_ver in sorted(d_vs, key=cmp_to_key(RUST.cmp))]
            if not d_vs:
                raise Exception("No call graphs available for package: " + d_name)
            d_v = d_vs.pop()
            d_krate = "{}::{}".format(d_name,d_v)
            d_eps = set()
            d_calls = set()
            for e in krate_eps:
                if e not in krate_paths:
                    continue
                for call in krate_paths[e]:
                    t_name, t_fn, t_dispatch = call
                    if t_name == d_name:
                        d_eps.add(t_fn)
                        d_calls.add((krate, e, t_name, d_v, t_fn, t_dispatch))
            for call in d_calls:
                yield call
            if d_eps: #check if there are calls to check in the dep
                # Resolve features
                enabled_optionals = resolve_features(d_krate,d_features,d_optional,d_default_features, features)
                if d_name in transitve_opts:
                    enabled_optionals = enabled_optionals + list(flatten_features(transitve_opts[d_name], features[d_krate])) 
                if d_krate + str(sorted(enabled_optionals)) not in visited:
                    for z_krate in resolve_with_cg(d_krate, d_eps, enabled_optionals, dependencies,features, releases, visited):
                        yield z_krate

def dep_fn_closure(_snapshot, _dependencies, _features):
    pkgs = {}
    for p,vs in _snapshot.items():
        vs = _snapshot[p]
        vs = [v.encode("ascii") for v in vs]
        vs = [v.decode('ascii') for v in sorted(vs, key=cmp_to_key(RUST.cmp))]

        resolved_tree = []
        while vs:
            v = vs.pop()
            krate = "{}::{}".format(p,v)
            krate_eps = get_entrypoints(krate)
            try:
                resolved_tree = list(resolve_with_cg(krate,krate_eps,[],_dependencies,_features,_snapshot))
            except Exception as e:
                continue
            break #we dont need to continue, we have a resolved release from this package

        if resolved_tree:
            pkgs[krate] = resolved_tree
    return pkgs 

def fn2pkgclosure(_closure):
    _pkg_edges = {}
    for k,fns in _closure.items():
        _pkg_edges[k] = set([(src_krate,"{}::{}".format(d_name, d_ver)) for (src_krate, s_fn, d_name, d_ver, t_fn, t_dispatch) in fns]) 
    return _pkg_edges


def num_of_deps(_closure, name):
    _pd_dict_t = {}
    _pd_dict_d = {}
    
    for k,ds in _closure.items():
        ds_t = set([t.split("::")[0] for (s,t) in ds])
        if ds_t: 
            _pd_dict_t[k] = len(ds_t)
        ds_d = set([t.split("::")[0] for (s,t) in ds if s == k])
        if ds_d:
            _pd_dict_d[k] = len(ds_d)
    
    pd_d = pd.Series(_pd_dict_d)
    pd_t = pd.Series(_pd_dict_t) 

    pd_d.to_csv("out2/{}-{}-d.csv".format(sys.argv[1],name))
    pd_t.to_csv("out2/{}-{}-t.csv".format(sys.argv[1],name))

    return {"d": pd_d, "t": pd_t}

def num_of_dependents(_closure,name):
    ## Create reverse dependency relations
    node_list = []
    edge_list = []
    visited_node = set()
    id_lookup = {}

    ## Populate nodes
    id = 0
    for s,ts in _closure.items():
        if s not in visited_node:
            visited_node.add(s)
            id_lookup[s] = id
            node_list.append((id,{"name": s.split("::")[0], "ver": s.split("::")[1]}))
            id += 1
    
        for (t_s,t_t) in ts:
            if t_s not in visited_node:
                visited_node.add(t_s)
                id_lookup[t_s] = id
                node_list.append((id,{"name": t_s.split("::")[0], "ver": t_s.split("::")[1]}))
                id += 1         

            if t_t not in visited_node:
                visited_node.add(t_t)
                id_lookup[t_t] = id
                node_list.append((id,{"name": t_t.split("::")[0], "ver": t_t.split("::")[1]}))
                id += 1    
      
    ## Populate edges
    for _,ts in _closure.items():
        for (t_s,t_t) in ts:
            edge_list.append((id_lookup[t_s], id_lookup[t_t]))

    G = nx.DiGraph()
    G.add_nodes_from(node_list)
    G.add_edges_from(edge_list)
    G = G.reverse(copy=True)

    _pd_dict_d  = {}
    _pd_dict_t = {}
    ## num of direct dependents
    for n in G.nodes():
        #direct
        _pd_dict_d[G.nodes[n]['name'] + "::" + G.nodes[n]['ver']] = G.out_degree(n)
        #transitive
        all_nh = sum([G.number_of_edges(u,v) for (u,v) in nx.bfs_edges(G, source=n)])
        trans_nh = all_nh - G.out_degree(n) 
        _pd_dict_t[G.nodes[n]['name'] + "::" + G.nodes[n]['ver']] = trans_nh 
        # all_nh = [z for y in G.neighbors(n) for z in G.neighbors(y)]
        # all_nh = set(all_nh) - set([n]) - set(G.neighbors(n))
     #   _pd_dict_t[G.nodes[n]['name'] + "::" + G.nodes[n]['ver']] = len(all_nh)
    
    pd_d = pd.Series(_pd_dict_d)
    pd_t = pd.Series(_pd_dict_t) 

    pd_d.to_csv("out2/{}-{}-dependents-dr.csv".format(sys.argv[1],name))
    pd_t.to_csv("out2/{}-{}-dependents-tr.csv".format(sys.argv[1],name))    
    
def num_of_depfns(_fn_closure, name):
    _pd_dict_t = {}
    _pd_dict_d = {}
    
    for k,fns in _fn_closure.items():
        ds_t = set([t_fn for (src_krate, s_fn, d_name, d_ver, t_fn, t_dispatch) in fns])
        if ds_t: 
            _pd_dict_t[k] = len(ds_t)
        ds_d = set([t_fn for (src_krate, s_fn, d_name, d_ver, t_fn, t_dispatch) in fns if src_krate == k])
        if ds_d:
            _pd_dict_d[k] = len(ds_d)
    
    pd_d = pd.Series(_pd_dict_d)
    pd_t = pd.Series(_pd_dict_t) 

    pd_d.to_csv("out2/{}-{}-fn-d.csv".format(sys.argv[1],name))
    pd_t.to_csv("out2/{}-{}-fn-t.csv".format(sys.argv[1],name))

    return {"d": pd_d, "t": pd_t}


def overlapping_depfn(_fn_closure, name):
    _dict_overlap = {}
    for k,fns in _fn_closure.items():
        visited = set()
        selected = []
        for (_, _, d_name, d_ver, t_fn, _) in fns:
            d_krate = "{}::{}::{}".format(d_name,d_ver,t_fn)
            if d_krate in visited:
                continue
            else:
                visited.add(d_krate)
                selected.append(t_fn)
        _dict_overlap[k] = len([fn for fn, count in collections.Counter(selected).items() if count > 1])
    
    pd_d = pd.Series(_dict_overlap)
    pd_d.to_csv("out2/{}-{}-overlap-fn.csv".format(sys.argv[1],name))
    
    return pd_d


def num_of_overlap(_closure,name):
    _pd_dict_overlap = {}
    
    for k,ds in _closure.items():
        ds = [t.split("::")[0] for (s,t) in ds]
        _pd_dict_overlap[k] = len([d for d, count in collections.Counter(ds).items() if count > 1]) 

    pd_d = pd.Series(_pd_dict_overlap)
    pd_d.to_csv("out2/{}-{}-overlap.csv".format(sys.argv[1],name))

    return pd_d

# ####
# ###### Create Networks 
# #####

# Calculate Dependency Closure (package level)
index_closure = dep_closure(_index_snapshot,_dependencies,_features)
docsrs_closure = dep_closure(_docsrs_snapshot,_dependencies,_features)

# Calculate Dependency Closure (function level)
praezi_fn_closure = dep_fn_closure(_praezi_snapshot,_dependencies,_features)
praezi_pkg_closure = fn2pkgclosure(praezi_fn_closure)