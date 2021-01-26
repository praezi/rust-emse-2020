# Präzi: From Package-based to Call-based Dependency Networks

The replication package containts:

- Scripts for generating call-based dependency networks
- Analysis scripts for producing results of the [paper](https://arxiv.org/abs/2101.09563)
- Datasets 



## Process Call Graphs for CDN generation
There are two options for generating a CDN, the first being a statically
generated CDN using the resolved versions available in the call graph, and the
second, annotes call graphs further for dynamically-created CDNs.


### Generate a one-time static CDN

``` sh
# Annontate and prune (i.e., remove std calls) call graphs 
./ufify/run.sh

# Create a CDN and PDN 
./gen/run.sh

```
### Preperation for dynamic CDNs

``` sh
./api-pair-extract/run.sh
```

# Running Analysis Scripts

## Datasets

### 2020-02-14

- Package-based Dependency Network: [PDN.json](https://surfdrive.surf.nl/files/index.php/s/q9TfmYVlvLpprsn)
- Call-based Dependency Network: [CDN.json]()
