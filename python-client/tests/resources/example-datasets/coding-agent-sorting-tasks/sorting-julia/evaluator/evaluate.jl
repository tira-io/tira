#!/usr/bin/env julia
# Minimal evaluator for the sorting-julia task.
#
# Compares a predictions file against a truths file and reports exact-match accuracy: the
# fraction of instances for which the submitted "sorted" array exactly equals the
# "expected_sorted" array from the truths file. A score of 1.0 is best (all predictions
# correct) and 0.0 is worst (no predictions correct).
#
# Only uses Julia's standard library; JSON lines are parsed with a small regex-based parser
# tailored to this task's fixed schema (a flat object with a string "id" field and one
# integer-array field).
#
# --predictions and --truths may each be either a *.jsonl file directly, or a directory that
# contains exactly one *.jsonl file.
#
# Usage:
#     # Print the result as JSON to stdout.
#     julia evaluate.jl --predictions predictions.jsonl --truths truths.jsonl
#
#     # Write the result as TIRA's evaluation.prototext instead.
#     julia evaluate.jl --predictions predictions.jsonl --truths truths.jsonl --output out-dir

function resolve_jsonl(path::AbstractString)
    if isdir(path)
        matches = filter(f -> endswith(f, ".jsonl"), readdir(path))
        if length(matches) != 1
            error("Expected exactly one *.jsonl file in $path, found $matches.")
        end
        return joinpath(path, matches[1])
    end
    return path
end

function load_jsonl(path::AbstractString, array_field::AbstractString)
    id_pattern = r"\"id\"\s*:\s*\"([^\"]*)\""
    array_pattern = Regex("\"" * array_field * "\"\\s*:\\s*\\[([^\\]]*)\\]")
    records = Dict{String,Vector{Int}}()

    for line in eachline(resolve_jsonl(path))
        line = strip(line)
        isempty(line) && continue

        id_match = match(id_pattern, line)
        array_match = match(array_pattern, line)
        if id_match === nothing || array_match === nothing
            error("Could not parse line: $line")
        end

        id = id_match.captures[1]
        raw = strip(array_match.captures[1])
        values = isempty(raw) ? Int[] : [parse(Int, strip(v)) for v in split(raw, ",")]
        records[id] = values
    end

    return records
end

function to_prototext(key::AbstractString, value)
    title = replace(replace(key, "-" => " "), "_" => " ")
    title_cased = join([uppercasefirst(w) for w in split(title, " ") if !isempty(w)], " ")
    return "measure{\n  key: \"$title_cased\"\n  value: \"$value\"\n}\n"
end

function parse_args(argv::Vector{String})
    options = Dict{String,String}()
    i = 1
    while i <= length(argv) - 1
        if argv[i] == "--predictions"
            options["predictions"] = argv[i+1]
        elseif argv[i] == "--truths"
            options["truths"] = argv[i+1]
        elseif argv[i] == "--output"
            options["output"] = argv[i+1]
        end
        i += 1
    end
    return options
end

function main()
    options = parse_args(ARGS)
    if !haskey(options, "predictions") || !haskey(options, "truths")
        println(stderr, "Usage: julia evaluate.jl --predictions <predictions.jsonl> --truths <truths.jsonl> [--output <dir>]")
        exit(1)
    end

    truths = load_jsonl(options["truths"], "expected_sorted")
    predictions = load_jsonl(options["predictions"], "sorted")

    correct = 0
    for (id, expected) in truths
        if get(predictions, id, nothing) == expected
            correct += 1
        end
    end

    accuracy = isempty(truths) ? 0.0 : correct / length(truths)

    if haskey(options, "output")
        mkpath(options["output"])
        open(joinpath(options["output"], "evaluation.prototext"), "w") do f
            write(f, to_prototext("exact-match-accuracy", accuracy))
        end
    else
        println("{\"exact-match-accuracy\": $accuracy}")
    end
end

main()
