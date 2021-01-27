"""
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
   
   Extract toolchain information from docs.rs
   Deps pip3 install requests beautifulsoup4s
   Run: python3 scrap.py <crate_name> <crate_version>   
"""
import sys

import requests
from bs4 import BeautifulSoup

assert len(sys.argv) == 3

URL  = "https://docs.rs/crate/{}/{}/builds".format(sys.argv[1], sys.argv[2])
page = requests.get(URL)

soup = BeautifulSoup(page.content, 'html.parser')

toolchains = soup.find_all('a', class_='release')

def isSuccess(clazz):
    if clazz == "fa fa-check":
        return True
    else:
        return False


for tc in toolchains:
    row = tc.find('div',class_='pure-g')

    status_class = row.find('i')['class']
    status = ' '.join(status_class)

    compiler_elem = row.find('div', class_='pure-u-1 pure-u-sm-10-24')
    build_date_elem = row.find('div', class_='pure-u-1 pure-u-sm-3-24 date')
    
    csv_entry = "{},{},{},{},{}".format(sys.argv[1], sys.argv[2],isSuccess(status),compiler_elem.text,build_date_elem.text)
    print(csv_entry)

