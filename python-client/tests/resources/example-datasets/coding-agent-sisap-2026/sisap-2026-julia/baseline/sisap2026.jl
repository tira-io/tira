# Baseline of the SISAP 2026 Indexing Challenge (tasks 1, 2, and 3) in Julia.
# Adapted from https://github.com/sisap-challenges/sisap2026-julia-example (MIT license, see LICENSE).
#
# Usage:
#   julia -t auto sisap2026.jl --input <file.h5> --task-description <config.json> --output <dir>
using LinearAlgebra, HDF5, JSON, StatsBase, SparseArrays
using SimilaritySearch, SimilaritySearch.Dist
using InvertedFiles
using SimilaritySearch.Special.Sparse

function save_results(knns::Matrix, meta, resfile::AbstractString)
    mkpath(dirname(resfile))
    h5open(resfile, "w") do f
        # Julia stores column-major: (k, n) here is (n, k) for h5py. Identifiers are 1-based, as in the ground truth.
        f["knns"] = Int32[x.id for x in knns]
        f["dists"] = Float32[x.dist for x in knns]
        A = attributes(f)
        for key in ["algo", "buildtime", "optimtime", "querytime", "params", "searchparams", "size", "task", "dataset"]
            A[key] = meta[key]
        end
    end
end

function pretty_params(params)
    params = replace(params, r"\s+"ism => " ")
    params = replace(params, "Float32" => "")
    params = replace(params, "minrecall" => "")
    params = replace(params, ":" => "")
    params = replace(params, "f0" => "")
    params = replace(params, r"\s+"ism => " ")
    params = replace(params, " tol " => " ")
    replace(params, r"\s+$"ism => "")
end

function load_sparse_matrix(file, group_path)
    h5open(file, "r") do f
        g = f[group_path]
        nzval = Float32.(read(g["data"]))
        colval = Int32.(read(g["indices"])) .+ 1 # 1-based indexing
        rowptr = Int32.(read(g["indptr"])) .+ 1
        m, n = read(attributes(g)["shape"])
        Sparse.SparseDatabase(SparseMatrixCSC(n, m, rowptr, colval, nzval))
    end
end

# Removes the self-reference of each object (the first k+1 neighbors of an all-knn graph contain the object itself)
function without_self_loops(knns, k)
    ret = similar(knns, k, size(knns, 2))
    for i in axes(knns, 2)
        column = [x for x in @view(knns[:, i]) if x.id != i]
        ret[:, i] = column[1:k]
    end
    ret
end

function run_task1(file, cfg)
    k = cfg["k"]
    X = h5open(f -> read(f[cfg["data"]]), file, "r")
    db = StrideMatrixDatabase(X)
    optim = MinRecall(0.9)
    neighborhood = Neighborhood(; filter=SatNeighborhood(), neardup=0.05f0, logbase=1.3f0)
    ctx = SearchGraphContext(;
        hyperparameters_callback=OptimizeParameters(optim),
        hints_callback=RandomHints(logbase=1.1),
        neighborhood,
    )

    G = SearchGraph(; db, dist=Dist.NormCosine())
    meta = Dict{String,Any}("algo" => "ABS", "params" => pretty_params(string("SearchGraph ", optim, "; ", neighborhood)))
    meta["buildtime"] = @elapsed G = index!(G, ctx)
    meta["optimtime"] = @elapsed optimize_index!(G, ctx, MinRecall(0.9), ksearch=k + 1)
    meta["querytime"] = @elapsed knns = allknn(G, ctx, k + 1)
    meta["searchparams"] = "task1 algorithm"
    meta["size"] = length(db)
    [(without_self_loops(knns, k), meta)]
end

function run_task2(file, cfg)
    k = cfg["k"]
    X, Q = h5open(file, "r") do f
        read(f[cfg["data"]]), read(f[cfg["queries"]])
    end
    db, queries = StrideMatrixDatabase(Float16.(X)), StrideMatrixDatabase(Float16.(Q))
    S = ExhaustiveSearch(; dist=Dist.CastF32.NormCosine(), db)
    meta = Dict("algo" => "ExhaustiveSearch", "params" => "f16-Cos", "buildtime" => 0.0, "optimtime" => 0.0)
    meta["querytime"] = @elapsed knns = searchbatch(S, GenericContext(), queries, k)
    meta["searchparams"] = ""
    meta["size"] = length(db)
    [(knns, meta)]
end

function run_task3(file, cfg; logbase=1.1f0, minrecall=0.99f0)
    k = cfg["k"]
    db = load_sparse_matrix(file, cfg["data"])
    queries = load_sparse_matrix(file, cfg["queries"])
    S = SearchGraph(; dist=Sparse.NormCosine(), db)
    ctx = SearchGraphContext(
        neighborhood=Neighborhood(; logbase),
        hyperparameters_callback=OptimizeParameters(MinRecall(minrecall)),
    )
    buildtime = @elapsed index!(S, ctx)

    # one operating point for each search parameter
    ret = []
    B = S.algo[]
    for step in -7:7
        S.algo[] = BeamSearch(; Δ=B.Δ * 1.05^step, B.bsize, B.maxvisits)
        meta = Dict{String,Any}("algo" => "ABS", "params" => pretty_params("b=$logbase r=$minrecall"))
        meta["buildtime"], meta["optimtime"] = buildtime, 0.0
        meta["querytime"] = @elapsed knns = searchbatch(S, ctx, queries, k)
        meta["searchparams"] = string(S.algo[])
        meta["size"] = length(db)
        push!(ret, (knns, meta))
    end
    ret
end

const TASKS = Dict("task1" => run_task1, "task2" => run_task2, "task3" => run_task3)

function main(args)
    options = Dict(args[i] => args[i+1] for i in 1:2:length(args))
    file, output = options["--input"], options["--output"]
    cfg = JSON.parsefile(options["--task-description"])
    task = cfg["task"]
    @info "running $task on $file" cfg

    for (i, (knns, meta)) in enumerate(TASKS[task](file, cfg))
        meta["task"], meta["dataset"] = task, cfg["dataset_name"]
        @info meta
        save_results(knns, meta, joinpath(output, "results-$i-$(meta["algo"]).h5"))
    end
end

main(ARGS)
