# rust-emse-2020
Replication Package 


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

## Analysis Base