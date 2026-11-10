import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Minimal evaluator for the sorting-java task.
 *
 * Compares a predictions file against a truths file and reports exact-match accuracy: the
 * fraction of instances for which the submitted "sorted" array exactly equals the
 * "expected_sorted" array from the truths file. A score of 1.0 is best (all predictions
 * correct) and 0.0 is worst (no predictions correct).
 *
 * Only depends on the JDK standard library; JSON lines are parsed with a small regex-based
 * parser tailored to this task's fixed schema (a flat object with a string "id" field and one
 * integer-array field).
 *
 * --predictions and --truths may each be either a *.jsonl file directly, or a directory that
 * contains exactly one *.jsonl file.
 *
 * Usage:
 *     javac Evaluate.java
 *
 *     # Print the result as JSON to stdout.
 *     java Evaluate --predictions predictions.jsonl --truths truths.jsonl
 *
 *     # Write the result as TIRA's evaluation.prototext instead.
 *     java Evaluate --predictions predictions.jsonl --truths truths.jsonl --output out-dir
 */
public class Evaluate {
    private static final Pattern ID_PATTERN = Pattern.compile("\"id\"\\s*:\\s*\"([^\"]*)\"");

    private static String resolveJsonl(String path) throws IOException {
        File f = new File(path);
        if (f.isDirectory()) {
            File[] matches = f.listFiles((dir, name) -> name.endsWith(".jsonl"));
            if (matches == null || matches.length != 1) {
                throw new IOException("Expected exactly one *.jsonl file in " + path);
            }
            return matches[0].getPath();
        }
        return path;
    }

    private static Map<String, List<Integer>> loadJsonl(String path, String arrayField) throws IOException {
        Pattern arrayPattern = Pattern.compile("\"" + arrayField + "\"\\s*:\\s*\\[([^\\]]*)\\]");
        Map<String, List<Integer>> records = new LinkedHashMap<>();

        for (String line : Files.readAllLines(Paths.get(resolveJsonl(path)))) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }

            Matcher idMatcher = ID_PATTERN.matcher(line);
            Matcher arrayMatcher = arrayPattern.matcher(line);
            if (!idMatcher.find() || !arrayMatcher.find()) {
                throw new IllegalArgumentException("Could not parse line: " + line);
            }

            String id = idMatcher.group(1);
            String raw = arrayMatcher.group(1).trim();
            List<Integer> values = new ArrayList<>();
            if (!raw.isEmpty()) {
                for (String part : raw.split(",")) {
                    values.add(Integer.parseInt(part.trim()));
                }
            }
            records.put(id, values);
        }

        return records;
    }

    private static String toPrototext(String key, double value) {
        String title = key.replace("-", " ").replace("_", " ");
        StringBuilder titleCased = new StringBuilder();
        for (String word : title.split(" ")) {
            if (!word.isEmpty()) {
                titleCased.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1)).append(" ");
            }
        }
        return "measure{\n  key: \"" + titleCased.toString().trim() + "\"\n  value: \"" + value + "\"\n}\n";
    }

    public static void main(String[] args) throws IOException {
        String predictionsPath = null;
        String truthsPath = null;
        String outputPath = null;

        for (int i = 0; i < args.length - 1; i++) {
            if (args[i].equals("--predictions")) {
                predictionsPath = args[i + 1];
            } else if (args[i].equals("--truths")) {
                truthsPath = args[i + 1];
            } else if (args[i].equals("--output")) {
                outputPath = args[i + 1];
            }
        }

        if (predictionsPath == null || truthsPath == null) {
            System.err.println("Usage: java Evaluate --predictions <predictions.jsonl> --truths <truths.jsonl> [--output <dir>]");
            System.exit(1);
            return;
        }

        Map<String, List<Integer>> truths = loadJsonl(truthsPath, "expected_sorted");
        Map<String, List<Integer>> predictions = loadJsonl(predictionsPath, "sorted");

        int correct = 0;
        for (Map.Entry<String, List<Integer>> entry : truths.entrySet()) {
            List<Integer> prediction = predictions.get(entry.getKey());
            if (entry.getValue().equals(prediction)) {
                correct++;
            }
        }

        double accuracy = truths.isEmpty() ? 0.0 : (double) correct / truths.size();

        if (outputPath != null) {
            new File(outputPath).mkdirs();
            Files.write(Paths.get(outputPath, "evaluation.prototext"), toPrototext("exact-match-accuracy", accuracy).getBytes());
        } else {
            System.out.println("{\"exact-match-accuracy\": " + accuracy + "}");
        }
    }
}
