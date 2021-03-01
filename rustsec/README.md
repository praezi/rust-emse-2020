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

### Function



### The `type_hierarchy.json` file

#### Structure

``` json
{
  "types": [],
  "traits": [],
  "impls": [],
}

```
