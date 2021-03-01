# Creating package-level call graphs from package-dependency call graphs

Preparatory work to create an HTTPS endpoint for serving call graphs to RustSec
and organizations interested in analyzing readily-available call graphs.

The set of scripts splits a package-dependency call graph into several
independent package call graphs. The test script checks that type of information is
available for Trait Object calls. As the script cannot distinguish between
functions declared in modules, C function, or not, it can spit out this
information for manual verification.

## Run

``` sh
python3 extract-rustcg.py <path>
python3 merge-rustcg.py <path>
python3 test-rustcg.py <path>
```

## How did we split package-dependency call graphs?

<img width="440" alt="Screenshot 2021-02-26 at 16 52 13" src="https://user-images.githubusercontent.com/2521475/109322844-0ff0f380-7853-11eb-8041-b105d6fcfc83.png">

The figure above illustrates three types of function calls: two cross-package calls and one internal function call.

### Cross-package calls
We can expect two types of cross-package calls, (1) a statically-, dynamically-, or macro-dispatched call that targets a function or macro residing in a dependency, and (2) a trait object call in a dependency targeting a function implementation in the package under analysis (e.g., `Pkg v1.0` ). Due to code generation, it is possible to see statically-dispatched calls constructed like (2). 

For both these cases, we retain such calls in `Pkg v1.0` and remove the call in `Dep v0.1`. Keeping (2) call is still debatable, however, we think it is highly likely that a user would at-least pass its own implementation and have it invoked through a trait function in the dependency function.

To mark these calls as needing linking and resolution, we create placeholder functions in `Pkg v1.0` by removing the `package_version` in the file:

``` json
{
   "id":14,
   "package_name":"bitwrap",
   "package_version":"0.5.9",
   "crate_name":"bitwrap",
   "relative_def_id":"bitwrap::{{impl}}[3]::unpack[0]",
   "is_externally_visible":true,
   "num_lines":8,
   "source_location":"src/lib.rs:81:5: 88:6"
}
```

to 

``` json
{
   "id":14,
   "package_name":"bitwrap",
   "package_version": null,
   "crate_name":"bitwrap",
   "relative_def_id":"bitwrap::{{impl}}[3]::unpack[0]",
   "is_externally_visible":true,
   "num_lines":8,
   "source_location":"src/lib.rs:81:5: 88:6"
}
```

Whenever a function or macro has a `package_version: null`, the function needs to be replaced by a concrete function in another `callgraph.json`. It is important to note that the `num_lines` and `source_location` should be ignored in the placeholder function. This information will be set to `null` in a new version. To mark a function call as unresolved, we add another property to mark if the call is resolved or unresolved using a boolean flag:

``` json
"function_calls": [
  ["src_id", "dst_id", true]
],

"macro_calls": [
  ["src_id", "dst_id"]
]
```

to

``` json
"function_calls": [
  ["src_id", "dst_id", true, false]
],

"macro_calls": [
  ["src_id", "dst_id", false]
]
```

Here, the calls are marked as `false` and need to be resolved. 

### Internal function calls and standard library calls

Functions remains unchanged. The only notable change is in the call edge:

``` json
"function_calls": [
  ["src_id", "dst_id", true]
],

"macro_calls": [
  ["src_id", "dst_id"]
]
```

to

``` json
"function_calls": [
  ["src_id", "dst_id", true, true]
],

"macro_calls": [
  ["src_id", "dst_id", true]
]
```
Here, `true` in the last list element implies that the edge is concrete and resolved. 
