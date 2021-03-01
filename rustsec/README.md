## Getting started
We have opened a [public endpoint](https://lima.ewi.tudelft.nl/cratesio) serving call graphs of crates from [crates.io](https://crates/io). The available call graphs date back to February 2020; newer versions are currently not available. Below, we provide initial documentation on the data, its format, and how to use the accompanying type information with a call graph.

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
  - declared or generated function belonging to the package.
  - placeholder function that needs to be resolved to a declared or generated function in another crate.
  - function in `rustc` (e.g., `core`, `alloc`, or `std`)

##### `"macros": []`
A list of macros. A macro is:
  - a defined macro belonging to the crate.
  - placeholder macro that needs to be resolved to a declared macro in another crate.
  - macro from `rustc` (e.g., `core`, `alloc`, or `std`)



##### `"function_calls": []`
A list of calls between functions. A call is _statically_ or _dynamically_ dispatched, and _resolved_ or _unresolved_. A call that is _unresolved_ indicates that it is dependent on a function from an external crate.



##### `"macro_calls": []`
A list of macro invocations. A call is _resolved_ or _unresolved_. A call that is _unresolved_ indicates that it is dependent on a macro from an external crate.

### CG Node - Format
A call graph node is either a `function` or a `macro` item. The common format is the following:

``` json
{
  "id": "Int",
  "package_name": "String",
  "package_version": "String",
  "crate_name": "String",
  "relative_def_id": "String",
  "is_externally_visible": "Bool",
  "num_lines": "Int",
  "source_location": "String",
}
```

##### `"id"`
A unique identifier of the item within the file. We use the `id` to reference the source and target of function calls.

##### `"package_name"`
A name of the crate on [crates.io](https://crates.io). If there is a `null` value, the function or macro belongs to a standard crate of `rustc`.

##### `"package_version"`
A valid release of the crate on [crates.io](https://crates.io). If there is a `null` value present, the function is a placeholder function and needs to be resolved to a declared or generated function in another crate. 

##### `"crate_name"`
The name of the crate used within the source code.

##### `"relative_def_id"`
A relative or logical path leading to either a declared/generated function or macro. The `relative_def_id` can be used to query information in the `type_hierarchy.json` file.

##### `"is_externally_visible"`
The visability of the item. If `true`, the item is visible outside of its crate.

##### `"num_lines`
LOC of a function or macro.

##### `"source_location`
Absolute path to the declared function or macro in the source code if available. 

*NB: The source path contains a path used during compilation and is not harmonized.*

### CG Node - Example 
We use the [`wayland-client v0.25.0`](https://lima.ewi.tudelft.nl/cratesio/wayland-client/0.25.0/callgraph.json) call graph to exemplify the three types of functions or macros present in call graphs:

**Internal (a function with complete package qualifiers)**

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

### CG Node - Steps to replace a placeholder function/macro with a function/macro from another crate.
We will reuse the placeholder example above to illustrate the process:

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

1. Look-up the resolved version in the `Cargo.lock` file of the crate under analysis. Example: the resolved version is `0.23.4`
2. Download the call graph of the crate and the resolved version. Example: [`wayland-commons v0.23.4`](https://lima.ewi.tudelft.nl/cratesio/wayland-commons/0.23.4/callgraph.json)
3. Extract the `relative_def_id` of the placeholder function and lookup a matching function or macro in the downloaded call graph. Example:

``` json
{
  "id": 22,
  "package_name": "wayland-commons",
  "package_version": "0.23.4",
  "crate_name": "wayland_commons",
  "relative_def_id": "wayland_commons::map[0]::{{impl}}[1]::is_interface[0]",
  "is_externally_visible": true,
  "num_lines": 4,
  "source_location": "src/map.rs:69:5: 72:6"
}
```
4. Verify that the `is_externally_visible` is still `true`.


**Q: What if there are more matches for `relative_def_id`?**

There are two possibilities. Due to the non-normalization of `source_location`, we may have duplicates of the same function or macro. You can verify this by comparing the `source_location` between the matches. In the other case, there are several anonymous functions with identical relative paths. They can be distinguished by comparing the `source_location` field. 

### CG Edge
A CG edge is a list adhering the following format:

``` json
"function_calls": [
  ["src_id", "dst_id", "Bool(1)", "Bool(2)"]
],

"macro_calls": [
  ["src_id", "dst_id", "Bool(2)"]
]
```

An edge in `funcion_calls` has an additional list element. This extra element is to mark if an edge is dynamically or statically dispatched call. 

##### `"src_id"`
the `id` of the caller function.

##### `"dst_id"`
the `id` of the callee function.

##### `"Bool(1)"`
If an edge is statically or dynamically dispatched. If `true`, a statically dispatched call. If `false`, dynamically dispatched call.

##### `"Bool(2)"`
If an edge is resolved or unresolved. If `false`, the edge is unresolved and either the item in the `src_id` or `dst_id` needs to be replaced or linked to a function/macro in another crate. 


### The `type_hierarchy.json` file
File containing information on structs, traits, and trait implementations of a crate.

#### Structure

``` json
{
  "types": [],
  "traits": [],
  "impls": [],
}

```

##### `"types": []`
A list of data types. A type is:
  - Custom type (i.e., [`Struct`](https://doc.rust-lang.org/rust-by-example/custom_types/structs.html))
  - [Primitives](https://doc.rust-lang.org/rust-by-example/primitives.html)
  - Generics 

##### `"traits": []`
A list of [Traits](https://doc.rust-lang.org/rust-by-example/trait.html).

##### `"impls": []`
A list of Trait Implementations.

### Data Type - Format
A data type can be a custom type, primitive, or generic, and are specified using the following format:

``` json
{
  "id": "Int",
  "string_id": "String",
  "package_name": "String",
  "package_version": "String",
  "relative_def_id": "String",
}
```
##### `"id"`
A unique identifier of the item within the file. 

##### `"string_id"`
Simple name of the type without relative path information.

##### `"package_name"`
Name of the crate on [crates.io](https://crates.io). If there is a `null` value, the type belongs to a standard crate of `rustc`.

##### `"package_version"`
A valid release of the crate on [crates.io](https://crates.io). If there is a `null` value present, the custom type information needs to be replaced by one from a resolved version. Follow the steps [here](README.md#cg-node---steps-to-replace-a-placeholder-function-with-a-concrete-function)

##### `"relative_def_id"`
A relative or logical path leading to declared `Struct`. If there is a `null` value, it is a primitive or generic type. 

### Data Type - Lookup up a type using a `relative_def_id` from a CG Node.

In the [wayland-client v0.25.0](https://lima.ewi.tudelft.nl/cratesio/wayland-client/0.25.0/callgraph.json) callgraph, we have the following function we would like to look up the type information for:

```json
{
  "id": 2537,
  "package_name": "wayland-client",
  "package_version": "0.25.0",
  "crate_name": "wayland_client",
  "relative_def_id": "wayland_client::imp[0]::Dispatcher[0]::dispatch[0]",
  "is_externally_visible": true,
  "num_lines": 0,
  "source_location": null
}
```
1. Remove the function-portion of the `relative_def_id`. Example: `wayland_client::imp[0]::Dispatcher[0]`
2. Query under `types` section in the `type_hierarchy.json` file.
3. If a match, we retrieve the following item:

``` json
{
  "id": 74,
  "string_id": "dyn Dispatcher",
  "package_name": "wayland-client",
  "package_version": "0.25.0",
  "relative_def_id": "wayland_client::imp[0]::Dispatcher[0]"
}
```
The `string_id` indicates the name as `dyn Dispatcher`.

**Q: Why could I not find type information from a `relative_def_id`?**

- The function is part of a module and does not belong to a particular `Struct`.
- The function is an `unsafe` function that links to a function in a C library.
- Missing information from the rust std crates (if you are trying to look up something that belongs to `rustc`)

### Trait - Format

``` json
{
  "id": "Int",
  "package_name": "String",
  "package_version": "String",
  "relative_def_id": "String",
}
```
##### `"id"`
A unique identifier of the item within the file. 

##### `"package_name"`
Name of the crate on [crates.io](https://crates.io). If there is a `null` value, the type belongs to a standard crate of `rustc`.

##### `"package_version"`
A valid release on [crates.io](https://crates.io). If there is a `null` value present, the trait needs to be replaced by one from a resolved version. Follow the steps [here](README.md#cg-node---steps-to-replace-a-placeholder-function-with-a-concrete-function)

##### `"relative_def_id"`
A relative or logical path leading to declared `Trait`.

### Impl - Format

``` json
{
  "id": "Int",
  "type_id": "Int",
  "trait_id": "Int",
  "package_name": "String",
  "package_version": "String",
  "relative_def_id": "String",
}

```
##### `"id"`
A unique identifier of the item within the file. 

##### `"type_id"`
`id` reference to the type in `types: []`.

##### `"trait_id"`
`id` reference to the type in `traits: []`. 

##### `"package_name"`
Name of the crate on [crates.io](https://crates.io). If there is a `null` value, the type belongs to a standard crate of `rustc`.

##### `"package_version"`
A valid release on [crates.io](https://crates.io). If there is a `null` value present, the trait needs to be replaced by one from a resolved version. Follow the steps [here](README.md#cg-node---steps-to-replace-a-placeholder-function-with-a-concrete-function)

##### `"relative_def_id"`
A relative or logical path leading to declared `Trait`.

### Impl - How to findout if a function in `callgraph.json` is an implementation of a Trait function?

1. Needs to have an `{{impl}}` in the `relative_def_id` path such as the following example:

``` json
{
  "id": 22,
  "package_name": "wayland-commons",
  "package_version": "0.23.4",
  "crate_name": "wayland_commons",
  "relative_def_id": "wayland_commons::map[0]::{{impl}}[1]::is_interface[0]",
  "is_externally_visible": true,
  "num_lines": 4,
  "source_location": "src/map.rs:69:5: 72:6"
}
```
2. Split the the `relative_def_id` at the `{{impl}}` portion. Example:

`wayland_commons::map[0]::{{impl}}[1]::is_interface[0] --> wayland_commons::map[0]::{{impl}}[1]` 

3. Retrieve the implementation in the `impls` section of the `type_hierarchy.json` file. Example:

```json
{
  "id": 199,
  "type_id": 73,
  "trait_id": null,
  "package_name": "wayland-commons",
  "package_version": "0.23.4",
  "relative_def_id": "wayland_commons::map[0]::{{impl}}[1]"
}
```

Here, we find that the `trait_id` is `null`. In other cases, the `type_id` can also be `null`. Due to the use of generics, we are sometimes unable to resolve and piece out type information reliably. 

4. From the retrieved item, we can lookup it's `Struct` and/or `Trait` if available. 

Looking up the `type_id`, we find the name of this Struct is [`Object`](https://docs.rs/wayland-commons/0.23.4/wayland_commons/map/struct.Object.html).

```json
{
  "id": 73,
  "string_id": "Object",
  "package_name": "wayland-commons",
  "package_version": "0.23.4",
  "relative_def_id": "wayland_commons::map[0]::Object[0]"
}
```
