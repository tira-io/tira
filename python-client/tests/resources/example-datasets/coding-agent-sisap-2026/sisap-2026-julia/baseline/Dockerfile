FROM julia:1.10.10

ENV JULIA_DEPOT_PATH=/opt/julia-depot
RUN julia -e 'using Pkg; Pkg.add([PackageSpec(name="HDF5", version="0.17"), PackageSpec(name="JSON"), PackageSpec(name="InvertedFiles"), PackageSpec(name="SimilaritySearch", version="0.14"), PackageSpec(name="StatsBase")]); using HDF5, JSON, InvertedFiles, SimilaritySearch, StatsBase' \
    && chmod -R a+rwX /opt/julia-depot

COPY sisap2026.jl /sisap2026.jl
