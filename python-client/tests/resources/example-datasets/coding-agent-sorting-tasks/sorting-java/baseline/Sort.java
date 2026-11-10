/**
 * Minimal reference baseline for the sorting-java task.
 *
 * Reads the single *.jsonl file in --input (fields: id, unsorted) and writes predictions.jsonl to
 * --output with each array sorted in ascending order.
 *
 * Usage:
 *     java Sort --input <inputs-dir> --output <output-dir>
 */
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class Sort {

    private static String findJsonl(String directory) throws IOException {
        File[] matches = new File(directory).listFiles((dir, name) -> name.endsWith(".jsonl"));
        if (matches == null || matches.length != 1) {
            throw new IOException("Expected exactly one *.jsonl file in " + directory);
        }
        return matches[0].getPath();
    }

    public static void main(String[] args) throws IOException {
        String input = null;
        String output = null;
        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--input")) {
                input = args[++i];
            } else if (args[i].equals("--output")) {
                output = args[++i];
            }
        }
        if (input == null || output == null) {
            throw new IllegalArgumentException("Usage: Sort --input <dir> --output <dir>");
        }

        new File(output).mkdirs();
        Pattern idPattern = Pattern.compile("\"id\"\\s*:\\s*\"([^\"]*)\"");
        Pattern arrayPattern = Pattern.compile("\"unsorted\"\\s*:\\s*\\[([^\\]]*)\\]");

        List<String> outputLines = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(findJsonl(input)))) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            Matcher idMatcher = idPattern.matcher(line);
            Matcher arrayMatcher = arrayPattern.matcher(line);
            if (!idMatcher.find() || !arrayMatcher.find()) {
                continue;
            }
            String id = idMatcher.group(1);
            String numbersRaw = arrayMatcher.group(1).trim();
            List<Long> numbers = new ArrayList<>();
            if (!numbersRaw.isEmpty()) {
                for (String n : numbersRaw.split(",")) {
                    numbers.add(Long.parseLong(n.trim()));
                }
            }
            Collections.sort(numbers);
            String sortedStr = numbers.stream().map(String::valueOf).collect(Collectors.joining(", "));
            outputLines.add("{\"id\": \"" + id + "\", \"sorted\": [" + sortedStr + "]}");
        }

        Files.write(Paths.get(output, "predictions.jsonl"), String.join("\n", outputLines).concat("\n").getBytes());
    }
}
