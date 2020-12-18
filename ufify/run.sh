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

#!/bin/bash

## 1. Annonate all call graphs 
cd $DIR_CG_CORPUS
time find . -name callgraph.json -printf '%h\n' | parallel 'cd {}; python3 ufify-rustcg.py callgraph.json; [[ $? -ne 0 ]] && echo {}' 2>&1 | tee annotation.log 

## 2. Create a file `pdn_all_nodes.txt` listing all PDN nodes (~ 8min)
time find . -type f -name pdn_nodes.txt | parallel 'echo "" >> {}'
time find . -type f -name pdn_nodes.txt  -exec cat {} + >> ../cdn/2020-02-14/pdn_all_nodes.txt 
sed -i '/^$/d' ../cdn/2020-02-14/pdn_all_nodes.txt

## 3. Create a file `cdn_all_nodes.txt` listing all CDN nodes (~12min)
time find . -type f -name cdn_nodes.txt | parallel 'echo "" >> {}'
time find . -type f -name cdn_nodes.txt  -exec cat {} + >> ../cdn/2020-02-14/cdn_all_nodes.txt 
sed -i '/^$/d' ../cdn/2020-02-14/cdn_all_nodes.txt


## 4. Create a file `pdn_all_edges.txt` listing all unique PDN edges (~7min)
time find . -type f -name pdn_edges.txt | parallel 'echo "" >> {}'
time find . -type f -name pdn_edges.txt  -exec cat {} + >> ../cdn/2020-02-14/pdn_all_edges.txt 
sed -i '/^$/d' ../cdn/2020-02-14/pdn_all_edges.txt

## 5. Create a file `cdb_all_edges.txt` listing all unique CDN edges (~91min)
time find . -type f -name cdn_edges.txt | parallel 'echo "" >> {}'
time find . -type f -name cdn_edges.txt  -exec cat {} + >> ../cdn/2020-02-14/cdn_all_edges.txt 
sed -i '/^$/d' ../cdn/2020-02-14/cdn_all_edges.txt

