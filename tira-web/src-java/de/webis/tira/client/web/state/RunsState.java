package de.webis.tira.client.web.state;

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.ExecutionException;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;

import com.google.common.base.Function;
import com.google.common.collect.Lists;
import com.google.common.collect.Ordering;
import com.google.protobuf.TextFormat.ParseException;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluation;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.ExtendedRun;
import de.webis.tira.client.web.generated.TiraClientWebMessages.ExtendedRunOrBuilder;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.RunReview;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;
import de.webis.tira.client.web.storage.DatasetsStore;
import de.webis.tira.client.web.storage.RunsStore;
import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.TasksStore;
import de.webis.tira.client.web.storage.UsersStore;

public class RunsState {

	private static final String
		FILE_NAME_SIZE_TXT = "size.txt",
		FILE_NAME_STDERR_TXT = "stderr.txt",
		FILE_NAME_STDOUT_TXT = "stdout.txt",
		FILE_NAME_FILE_LIST_TXT = "file-list.txt",
		FILE_NAME_RUNTIME_TXT = "runtime.txt",
		FILE_NAME_RUN_REVIEW_PROTOTEXT = "run-review.prototext",
		FILE_NAME_EVALUATION_PROTOTEXT = "evaluation.prototext",
		FOLDER_RUN_OUTPUT = "output";
		
	private static final String
		EVALUATOR = "evaluator",
		SOFTWARE = "software",
		NONE = "none",
		HIDDEN = "hidden";
	
	private static final String 
		GNU_TIME_OUTPUT_SUFFIX_ELAPSED = "elapsed",
		BASH_TIME_OUTPUT_REAL = "real",
		OUTPUT_MODERATOR_MESSAGE = "Note: The output can only be viewed by task moderators.",
		OUTPUT_MODERATOR_MESSAGE_2 = "Note: The complete output can only be viewed by task moderators.",
		PARTIAL_OUTPUT_LEAD = "[...] ";
	
	private static final String 
		ABBREV_MINUTES = "m",
		ZERO_HOURS_PREFIX = "00:",
		RUNTIME_FORMAT = "%02d:%02d:%02d",
		REGEX_WHITESPACES = "\\s+";
		
	private static final String 
		NEWLINE = "\n",
		DOUBLE_LF = "\n\n",
		COLON = ":",
		ZERO = "0";
	
	private static final int 
		ONE_MB_IN_BYTES = 1048576;
	
	private static final char
		CH_E = 'e',
		CH_DOT = '.',
		CH_COLON = ':';
	
	public static ExtendedRun
	collectExtendedRun(String taskId, String userName, String runId,
		boolean filterTestDatasetOutput, boolean blindTestDatasetOutput,
		boolean readOutput, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		File runDir = RunsStore.findRun(taskId, userName, runId);
		return collectExtendedRun(taskId, runDir, filterTestDatasetOutput, 
				blindTestDatasetOutput, readOutput, sc);
	}

	public static ExtendedRun
	collectExtendedRun(String taskId, File runDir,
		boolean filterTestDatasetOutput, boolean blindTestDatasetOutput,
		boolean readOutput, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		Run r = RunsStore.readRunFromRunDir(taskId, runDir, sc);
		if (r == null) return null;
		ExtendedRun.Builder erb = ExtendedRun.newBuilder();
		erb.setRun(r);
		collectExtendedRun(taskId, runDir, r, erb, filterTestDatasetOutput,
				blindTestDatasetOutput, true, sc);
		ExtendedRun er = erb.build();
		return er;
	}

	public static void 
	collectUserRuns(String taskId, TaskUser.Builder tub, final User u,
			boolean filterTestDatasetOutput, ServletContext sc)
	throws ServletException, IOException, ExecutionException {
		Task t = TasksStore.getTask(taskId);
		Collection<File> taskUserDatasets = TasksStore.getTaskUserDatasetsWithRuns(u, t);
		List<File> runs = Lists.newArrayList(); 
		for (File taskUserDataset : taskUserDatasets) {
			File userRuns = new File(taskUserDataset, u.getUserName());
			runs.addAll(Lists.newArrayList(userRuns.listFiles()));
		}
		runs = Ordering.natural().onResultOf(new Function<File, String>() {
			public String apply(File f) {
				return f.getName();
			}
		}).reverse().sortedCopy(runs);
		for (File run : runs) {
			collectUserRun(taskId, tub, run.getParentFile().getParentFile(), run, filterTestDatasetOutput, sc);
		}
		for (ExtendedRun.Builder erb : tub.getRunsBuilderList()) {
			markDeletedSoftware(tub.getSoftwaresList(), erb);
			markDeletedRun(tub.getRunsOrBuilderList(), erb);
		}
		for (ExtendedRun.Builder erb : tub.getRunsBuilderList()) {
			if (!erb.getRun().getDeleted()) {
				tub.addRunsNotDeleted(erb);
				if (!DatasetsStore.isConfidential(taskId, erb.getRun().getInputDataset())) {
					tub.addRunsNotDeletedNotTest(erb);
				}
				if (erb.getRun().getSoftwareId().startsWith(EVALUATOR)) {
					tub.addEvaluatorRunsNotDeleted(erb);
				}
				if (erb.getRun().getSoftwareId().startsWith(SOFTWARE)) {
					tub.addSoftwareRunsNotDeleted(erb);
				}
			}
		}
		tub.setHasRunsNotDeleted(tub.getRunsNotDeletedCount() > 0);
		tub.setHasEvaluatorRunsNotDeleted(tub.getEvaluatorRunsNotDeletedCount() > 0);
		tub.setHasSoftwareRunsNotDeleted(tub.getSoftwareRunsNotDeletedCount() > 0);
	}

	private static void 
	collectUserRun(String taskId, TaskUser.Builder tub, File taskUserDataset,
			File run, boolean filterTestDatasetOutput, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		Run r = RunsStore.readRunFromRunDir(taskId, run, sc);
		if (r != null && (!r.hasTaskId() || taskId.equals(r.getTaskId()))) {
			ExtendedRun.Builder erb = tub.addRunsBuilder();
			erb.setRun(r);
			// This ensures the NFS cache is up to date
			CommandLineExecutor.executeCommand(String.format(
				CommandLineExecutor.CMD_LIST_FILES, run.getAbsolutePath()), sc);
			collectExtendedRun(taskId, run, r, erb, filterTestDatasetOutput, true, false, sc);
		}
	}

	private static void 
	collectExtendedRun(String taskId, File run, Run r, ExtendedRun.Builder erb,
			boolean filterTestDatasetOutput, boolean blindTestDatasetOutput,
			boolean readOutput, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		
		// NOTE. The RunReview must be read before stdout and stderr.
		File runReview = new File(run, FILE_NAME_RUN_REVIEW_PROTOTEXT);
		if (runReview.exists()) {
			RunReview rr = RunsStore.readRunReview(runReview, sc);
			erb.setRunReview(rr);
			erb.setHasReview(true);
			if (rr.hasBlinded()) {
				filterTestDatasetOutput = filterTestDatasetOutput && rr.getBlinded();
			}
		}
		
		File stdoutFile = new File(run, FILE_NAME_STDOUT_TXT);
		if (readOutput && stdoutFile.exists()) {
			Task t = TasksStore.getTask(taskId);
			int maxCharsOnTestData = t.getMaxStdOutCharsOnTestData();
			int maxCharsOnTestDataEval = t.getMaxStdOutCharsOnTestDataEval();
			String stdout = readOutput(taskId, r, filterTestDatasetOutput,
					stdoutFile, maxCharsOnTestData,	maxCharsOnTestDataEval);
			erb.setStdout(stdout);
		}
		
		File stderrFile = new File(run, FILE_NAME_STDERR_TXT);
		if (readOutput && stderrFile.exists()) {
			Task t = TasksStore.getTask(taskId);
			int maxCharsOnTestData = t.getMaxStdErrCharsOnTestData();
			int maxCharsOnTestDataEval = t.getMaxStdErrCharsOnTestDataEval();
			String stderr = readOutput(taskId, r, filterTestDatasetOutput,
					stderrFile, maxCharsOnTestData,	maxCharsOnTestDataEval);
			erb.setStderr(stderr);
		}
		
		File fileListFile = new File(run, FILE_NAME_FILE_LIST_TXT);
		if (readOutput && fileListFile.exists()) {
			Task t = TasksStore.getTask(taskId);
			int maxCharsOnTestData = t.getMaxFileListCharsOnTestData();
			int maxCharsOnTestDataEval = t.getMaxFileListCharsOnTestDataEval();
			String fileList = readOutput(taskId, r, filterTestDatasetOutput,
					fileListFile, maxCharsOnTestData, maxCharsOnTestDataEval);
			erb.setFileList(fileList);
		}
		
		if (r.getSoftwareId().startsWith(EVALUATOR)) {
			erb.setEvaluationRun(true);
		}
		
		if (filterTestDatasetOutput &&
			DatasetsStore.isConfidential(taskId, r.getInputDataset())) {
			erb.setRuntime(HIDDEN);
			erb.setRuntimeDetails(HIDDEN);
			erb.setSize(HIDDEN);
			erb.setSizeInBytes(HIDDEN);
			erb.setNumDirectories(HIDDEN);
			erb.setNumFiles(HIDDEN);
			erb.setNumLines(HIDDEN);
		}
		else {
			File runtime = new File(run, FILE_NAME_RUNTIME_TXT);
			if (runtime.exists()) {
				String runtimeDetails = RunsStore.FILE_CACHE.get(runtime.getAbsolutePath());
				erb.setRuntimeDetails(runtimeDetails);
				parseRuntimeDetails(erb, runtimeDetails);
			}
			
			File size = new File(run, FILE_NAME_SIZE_TXT);
			if (size.exists()) {
				String[] sizes = RunsStore.FILE_CACHE.get(size.getAbsolutePath()).split(NEWLINE);
				if (sizes.length == 2) {
					erb.setSizeInBytes(sizes[0]);
					erb.setSize(sizes[1]);
				}
				else if (sizes.length == 5) {
					erb.setSizeInBytes(sizes[0]);
					erb.setSize(sizes[1]);
					erb.setNumLines(sizes[2]);
					erb.setNumFiles(sizes[3]);
					erb.setNumDirectories(sizes[4]);
				}
			}
		}
		
		String datasetId = erb.getRun().getInputDataset();
		if (r.getSoftwareId().startsWith(EVALUATOR)) {
			File output = new File(run, FOLDER_RUN_OUTPUT);
			File evaluationPrototext = 
					new File(output, FILE_NAME_EVALUATION_PROTOTEXT);
			if (evaluationPrototext.exists()) {
				Task t = TasksStore.getTask(taskId);
				List<String> measureKeys = getDatasetEvaluatorMeasureKeys(taskId, r, t);
				Evaluation evaluation = RunsStore.readEvaluation(
					evaluationPrototext, measureKeys, sc);
				erb.setEvaluation(evaluation);
			}
		}
		
		String userName = run.getParentFile().getName();
		User u = UsersStore.getUser(userName);
		erb.setUser(u);
		
		erb.setHasInputRun(false);
		if (!erb.getRun().getInputRun().isEmpty() && 
			!erb.getRun().getInputRun().equals(NONE)) {
			File inputRun = RunsStore.findRun(taskId, userName,
					erb.getRun().getInputRun());
			if (inputRun != null && inputRun.exists()) {
				ExtendedRun er = collectExtendedRun(taskId, inputRun,
						filterTestDatasetOutput, blindTestDatasetOutput, 
						readOutput, sc);
				if (er != null) {
					erb.setInputRun(er);
					erb.setInputRunDeleted(er.getRun().getDeleted());
					erb.setHasInputRun(true);
				}
			}
		}
		
		Dataset d = DatasetsStore.getDataset(taskId, datasetId);
		boolean isDeprecated = 
			erb.hasIsDeprecated() ? erb.getIsDeprecated() : false;
		if (d.hasIsDeprecated()) {
			isDeprecated = isDeprecated || d.getIsDeprecated();
			erb.setIsDeprecated(isDeprecated);
			erb.setInputDatasetDeprecated(d.getIsDeprecated());
		}
		if (erb.hasInputRun()) {
			ExtendedRun inputRun = erb.getInputRun();
			if (inputRun.hasIsDeprecated()) {
				isDeprecated = isDeprecated || inputRun.getIsDeprecated();
				erb.setIsDeprecated(isDeprecated);
			}
		}
		if (erb.getRun().getSoftwareId().startsWith(EVALUATOR)) {
			Task t = TasksStore.getTask(taskId);
			Evaluator e = SoftwaresStore.getEvaluator(t, r.getSoftwareId());
			if (e == null || e.hasIsDeprecated()) {
				isDeprecated = isDeprecated || e == null || e.getIsDeprecated();
				erb.setIsDeprecated(isDeprecated);
				erb.setSoftwareDeprecated(e == null || e.getIsDeprecated());
			}
		}
	}

	public static List<String> getDatasetEvaluatorMeasureKeys(String taskId, Run r, Task t)
			throws ParseException, IOException {
		// We cannot use the evaluatorId from the Run message,
		// since it may be at odds with the one currently configured
		// for the dataset, yielding the wrong list of measureKeys.
		String evaluatorId = DatasetsStore.getEvaluatorId(taskId, r.getInputDataset());
		Evaluator e = SoftwaresStore.getEvaluator(t, evaluatorId);
		List<String> measureKeys =
			(e != null && e.getMeasureKeysCount() > 0) ?
			e.getMeasureKeysList() :
			null;
		return measureKeys;
	}

	public static String
	readOutput(String taskId, Run r, boolean filterTestDatasetOutput, File outputFile,
			int maxCharsOnTestData, int maxCharsOnTestDataEval)
	throws IOException {
		String output = "";
		if (filterTestDatasetOutput &&
			DatasetsStore.isConfidential(taskId, r.getInputDataset())) {
			int maxBytes = 0;
			if (r.getSoftwareId().startsWith(EVALUATOR)) {
				maxBytes = maxCharsOnTestDataEval;
			}
			else {
				maxBytes = maxCharsOnTestData;
			}
			output = readTail(outputFile, maxBytes);
			output = addModeratorMessage(output, outputFile.length());
		}
		else {
			output = readTail(outputFile, ONE_MB_IN_BYTES);
		}
		return output;
	}
	
	private static String
	readTail(File f, int maxBytes)
	throws IOException {
		if (maxBytes <= 0) return "";
		if (f.length() <= maxBytes) return FileUtils.readFileToString(f);
		RandomAccessFile randomAccessFile = new RandomAccessFile(f, "r");
		byte[] bytes = new byte[maxBytes];
		try {
			randomAccessFile.seek(f.length() - maxBytes); 
			randomAccessFile.read(bytes, 0, maxBytes);
		} 
		finally {
			randomAccessFile.close();
		}
		return new String(bytes);
	}

	private static String
	addModeratorMessage(String output, long fullOutputLength) {
		if (output.length() == 0) {
			return OUTPUT_MODERATOR_MESSAGE;
		}
		else if (fullOutputLength > output.length()) {
			return PARTIAL_OUTPUT_LEAD + output + DOUBLE_LF + OUTPUT_MODERATOR_MESSAGE_2;
		}
		else {
			return output;
		}
	}
	
	private static void 
	parseRuntimeDetails(ExtendedRun.Builder erb, String runtimeDetails) {
		String[] details = runtimeDetails.split(REGEX_WHITESPACES);
		boolean foundReal = false;
		for (String detail : details) {
			// Note: Runs from Windows machines have a different runtime.txt
			// than RUNS from Ubuntu machines, therefore two parsing
			// strategies need to be applied here.
			if (foundReal) {
				detail = detail.substring(0, detail.indexOf(CH_DOT));
				String[] values = detail.split(ABBREV_MINUTES);
				if (values.length == 2) {
					int minutes = Integer.parseInt(values[0]);
					int seconds = Integer.parseInt(values[1]);
					int hours = minutes / 60;
					minutes = minutes % 60;
					erb.setRuntime(String.format(RUNTIME_FORMAT,
							hours, minutes, seconds));
				}
				break;
			}
			else if (detail.equals(BASH_TIME_OUTPUT_REAL)) {
				foundReal = true;
			}
			else if (detail.endsWith(GNU_TIME_OUTPUT_SUFFIX_ELAPSED)) {
				if (detail.indexOf(CH_COLON) == 1) {
					detail = ZERO + detail;
				}
				if (StringUtils.countMatches(detail, COLON) == 1) {
					detail = ZERO_HOURS_PREFIX + detail;
				}
				int end = detail.indexOf(CH_DOT);
				if (end == -1) {
					end = detail.indexOf(CH_E);
				}
				erb.setRuntime(detail.substring(0, end));
				break;
			}
		}
	}
	
	private static void
	markDeletedSoftware(List<Software> softwares, ExtendedRun.Builder erb) {
		Run r = erb.getRun();
		if (r.getSoftwareId().startsWith(EVALUATOR)) {
			erb.setSoftwareDeleted(false);
		}
		else {
			erb.setSoftwareDeleted(true);
			for (Software s : softwares) {
				if (r.getSoftwareId().equals(s.getId()) && !s.getDeleted()) {
					erb.setSoftwareDeleted(false);
				}
			}
		}
	}

	private static void
	markDeletedRun(List<? extends ExtendedRunOrBuilder> runs, ExtendedRun.Builder erb) {
		Run r1 = erb.getRun();
		erb.setInputRunDeleted(false);
		if (r1.getInputRun().length() == 0 || NONE.equals(r1.getInputRun())) {
			return;
		}
		for (ExtendedRunOrBuilder erob : runs) {
			Run r2 = erob.getRun();
			if (r2.getDeleted() &&
				r2.getRunId().equals(r1.getInputRun())) {
				erb.setInputRunDeleted(true);
			}
		}
	}
}
