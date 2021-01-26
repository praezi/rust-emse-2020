# Präzi: From Package-based to Call-based Dependency Networks

The replication package containts:

- Scripts for generating call-based dependency networks
- Analysis scripts for producing results of the [paper](https://arxiv.org/abs/2101.09563)
- Links to datasets 


## Generating CDNs using [rust-callgraphs](https://github.com/ktrianta/rust-callgraphs) constructed call graphs
There are two options for generating a CDN:

1. Static CDN: one-time generation that uses the resolved dependency versions available in the call graphs. 
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

## Analysis

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


## Datasets

### 2020-02-14

- Package-based Dependency Network: [PDN.json](https://surfdrive.surf.nl/files/index.php/s/q9TfmYVlvLpprsn)
- Call-based Dependency Network: [CDN.json](https://surfdrive.surf.nl/files/index.php/s/Iq76O0Tx1iVeye0) (10 GB)
