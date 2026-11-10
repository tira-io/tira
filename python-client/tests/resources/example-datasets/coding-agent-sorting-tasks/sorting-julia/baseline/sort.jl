#!/usr/bin/env julia
# Minimal reference baseline for the sorting-julia task.
#
# Reads the single *.jsonl file in --input (fields: id, unsorted) and writes predictions.jsonl to
# --output with each array sorted in ascending order.
#
# Usage:
#     julia sort.jl --input <inputs-dir> --output <output-dir>

function find_jsonl(directory::AbstractString)
    matches = filter(f -> endswith(f, ".jsonl"), readdir(directory))
    if length(matches) != 1
        error("Expected exactly one *.jsonl file in $directory, found $matches.")
    end
    return joinpath(directory, matches[1])
end

function parse_args(argv::Vector{String})
    options = Dict{String,String}()
    i = 1
    while i <= length(argv) - 1
        if argv[i] == "--input"
            options["input"] = argv[i+1]
        elseif argv[i] == "--output"
            options["output"] = argv[i+1]
        end
        i += 1
    end
    return options
end

function main()
    options = parse_args(ARGS)
    if !haskey(options, "input") || !haskey(options, "output")
        println(stderr, "Usage: julia sort.jl --input <dir> --output <dir>")
        exit(1)
    end

    mkpath(options["output"])
    id_pattern = r"\"id\"\s*:\s*\"([^\"]*)\""
    array_pattern = r"\"unsorted\"\s*:\s*\[([^\]]*)\]"

    lines = String[]
    for line in eachline(find_jsonl(options["input"]))
        line = strip(line)
        isempty(line) && continue

        id_match = match(id_pattern, line)
        array_match = match(array_pattern, line)
        if id_match === nothing || array_match === nothing
            continue
        end

        id = id_match.captures[1]
        raw = strip(array_match.captures[1])
        values = isempty(raw) ? Int[] : [parse(Int, strip(v)) for v in split(raw, ",")]
        sort!(values)
        values_str = join(values, ", ")
        push!(lines, "{\"id\": \"$id\", \"sorted\": [$values_str]}")
    end

    open(joinpath(options["output"], "predictions.jsonl"), "w") do f
        write(f, join(lines, "\n") * "\n")
    end
end

main()
