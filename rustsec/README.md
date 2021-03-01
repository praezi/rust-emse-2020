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
  "macro_calls": [],
  "function_calls": []
}

```


### The `type_hierarchy.json` file

#### Structure

``` json
{
  "types": [],
  "traits": [],
  "impls": [],
}

```
