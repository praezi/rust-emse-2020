## Getting started
We have opened a [public endpoint](https://lima.ewi.tudelft.nl/cratesio) serving call graphs of crates available from [crates.io](https://crates/io). The available call graphs date back to February 2020; newer versions are currently not available. Below, we provide initial documentation on the data, its format, and how to use the accompanying type information with a call graph.

The call graphs were produced using [ktrianta/rust-callgraphs](https://github.com/ktrianta/rust-callgraphs).

### The `callgraph.json` file
File containing a call graph of a crate version including edges to cross-package functions.


#### Structure

``` json
{
  "functions": [],
  "macros": [],
  "function_calls": [],
  "macro_calls": [],
}

```

##### `"functions": []`
A list of functions. A function is:
  - concrete function belonging to the package.
  - placeholder function that needs to be resolved to a concrete function in another package.
  - function in `rustc` (e.g., `core`, `alloc`, or `std`)

##### `"macros": []`
A list of macros. A macro is:
  - a defined macro belonging to the package.
  - placeholder macro that needs to be resolved to a concrete macro in another package.
  - macro in `rustc` (e.g., `core`, `alloc`, or `std`)



##### `"function_calls": []`
A list of calls between function entities. A call is _statically_ or _dynamically_ dispatched, and _resolved_ or _unresolved_. A call that is _unresolved_ indicates that it is dependent on a function from an external package.



##### `"macro_calls": []`
A list of macro invocations. A call is _resolved_ or _unresolved_. A call that is _unresolved_ indicates that it is dependent on a macro from an external package.

### CG Node - Format
A call graph node is either a `function` and `macro` item. The common format is the following:

``` json
{
  "id": Int,
  "package_name": String,
  "package_version": String,
  "crate_name": String,
  "relative_def_id": String,
  "is_externally_visible": Bool,
  "num_lines": Int,
  "source_location": String,
}
```

##### `"id"`
A unique identifier of the item within the file. We use the `id` to reference the source and target of function calls.

##### `"package_name"`
A crate's published name identifier on [crates.io](https://crates.io). If there is a `null` value, the function or macro belongs to a standard crate of `rustc`.

##### `"package_version"`
A valid release on [crates.io](https://crates.io). If there is a `null` value present, the function is a placeholder function and needs to be resolved to a concrete function. 

##### `"crate_name"`
The name of the crate is used internally within the source code.

##### `"relative_def_id"`
A relative or logical path leading to either a declared/generated function or macro. The `relative_def_id` can be used to query information in the `type_hierarchy.json` file.

##### `"is_externally_visible"`
Indicate whether the function is visible outside its package and can accept a cross-package call.

##### `"num_lines`
LOC of a function or macro

##### `"source_location`
Absolute path to the declared function or macro in the source code if available. 
*NB:* The source path contains a path used during compilation and is not harmonized.

### CG Node - Example 
We use the [`wayland-client v0.25.0`](https://lima.ewi.tudelft.nl/cratesio/wayland-client/0.25.0/callgraph.json) call graph to exemplify the three types of functions or macros present in call graphs:

**Internal**

``` json
{
  "id": 556,
  "package_name": "wayland-client",
  "package_version": "0.25.0",
  "crate_name": "wayland_client",
  "relative_def_id": "wayland_client::protocol[0]::wl_data_offer[0]::{{impl}}[1]::since[0]",
  "is_externally_visible": true,
  "num_lines": 1,
  "source_location": "/opt/rustwide/target/debug/build/wayland-client-50cb100bb9fe6d9c/out/wayland_api.rs:1:74992: 1:75191"
}
```

**Placeholder (a function that needs to be resolved)** 
``` json
{
  "id": 653,
  "package_name": "wayland-commons",
  "package_version": null,
  "crate_name": "wayland_commons",
  "relative_def_id": "wayland_commons::map[0]::{{impl}}[1]::is_interface[0]",
  "is_externally_visible": true,
  "num_lines": 4,
  "source_location": "/opt/rustwide/cargo-home/registry/src/github.com-1ecc6299db9ec823/wayland-commons-0.25.0/src/map.rs:70:5: 73:6"
}
```

*NB: the `num_lines` and `source_location` should be ignored.*

**Standard library**

``` json
{
  "id": 796,
  "package_name": null,
  "package_version": null,
  "crate_name": "core",
  "relative_def_id": "core::cell[0]::{{impl}}[20]::borrow_mut[0]",
  "is_externally_visible": true,
  "num_lines": 0,
  "source_location": null
}
```

### CG Node - Steps to replace a place holder function with a concrete function.






### The `type_hierarchy.json` file

#### Structure

``` json
{
  "types": [],
  "traits": [],
  "impls": [],
}

```
