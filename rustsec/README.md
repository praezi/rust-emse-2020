# Creating package-level call graphs from package-dependency call graphs

Preparatory work to create an HTTPS endpoint for serving call graphs to RustSec
and organizations interested in analyzing readily-available call graphs.

The set of scripts splits a package-dependency call graph into several
independent package call graphs. The test script checks that type information is
availalbe for Trait Object calls. As the script cannot distingush between
functions declared in modules, C function, or not, it can spit out this
information for manual verification.

## Run

``` sh
python3 extract-rustcg.py <path>
python3 merge-rustcg.py <path>
python3 test-rustcg.py <path>
```