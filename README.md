# Präzi: From Package-based to Call-based Dependency Networks
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4478981.svg)](https://doi.org/10.5281/zenodo.4478981)
[![arXiv](https://img.shields.io/badge/arXiv-2101.56789-09563.svg)](https://arxiv.org/abs/2101.09563)


The replication package contains:

- Scripts for generating call-based dependency networks
- Scraper for mining toolchain & build status on [Docs.rs](https://docs.rs) 
- Analysis scripts for producing results of the [paper](https://arxiv.org/abs/2101.09563)
- Links to datasets 


## Generating CDNs using [rust-callgraphs](https://github.com/ktrianta/rust-callgraphs) constructed call graphs
There are two options for generating a CDN:

1. Static CDN: a one-time generation that uses the resolved dependency versions available in the call graphs. 
2. Dynamic CDN: on-the-fly generation based on user-provided timestamps. Constructs API-mappings based on entry and exit points of packages.


### Generate a one-time static CDN

``` bash
# Annontate and prune (i.e., remove std calls) call graphs 
./ufify/run.sh

# Create a CDN and PDN 
./gen/run.sh

```
### Preperation for dynamic CDNs

``` bash
./api-pair-extract/run.sh
```

## Working with Call-based Dependency Networks

### Installation Prerequisites

#### Dependencies 

- [Rust toolchain](https://rustup.rs)
- Python 3
- [pandas](https://pandas.pydata.org)
- [numpy](https://numpy.org)
- [networkx](https://networkx.org) 

#### Python bindings to Rust's [semver](https://crates.io/crates/semver) library

1. Generate an FFI-compatible C-ABI library in Rust

``` bash
cd bindings
cargo build --release
```

2. Replace lookup path to the library

After compilation, a generated library (`libsemver_ffi.so`) should be available under the `target` folder:

```
target/release/libsemver_ffi.so
```

Replace the path in [evolysis-rustcg.py](https://github.com/praezi/rust-emse-2020/blob/main/analysis/evolysis-rustcg.py#L52) to match your absolute path.

### On-the-fly generation and analysis

Running the [evolysis-rustcg.py](https://github.com/praezi/rust-emse-2020/blob/main/analysis/evolysis-rustcg.py) will automatically create 3 PDNs (index, docs.rs, RustPräzi) and 1 CDN (RustPräzi).
After generation, you can run analysis such as `num_of_dependency_fns(praezi_fn_closure, "praezi")` and result will be dumped to `out/` folder.

```
python3 -i analysis/evolysis-rustcg.py <timestamp>
```

Example

```
python3 -i analysis/evolysis-rustcg.py 2015-08
```

### Analysis on a Static CDN

The Jupyter Notebook [CDN Analysis.ipynb](https://github.com/praezi/rust-emse-2020/blob/main/analysis/CDN%20Analysis.ipynb) provide examples of how to load a CDN and perform descriptive statistics


## Datasets
The call graph corpus and a statically generated CDN is available at [Zenodo](https://doi.org/10.5281/zenodo.4478981) for download.
