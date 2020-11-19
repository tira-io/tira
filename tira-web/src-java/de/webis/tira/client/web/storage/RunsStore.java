package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutionException;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.common.cache.CacheBuilder;
import com.google.common.cache.CacheLoader;
import com.google.common.cache.LoadingCache;
import com.google.common.cache.Weigher;
import com.google.common.collect.LinkedListMultimap;
import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluation;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.RunReview;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluation.Measure;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;

public class RunsStore {

	private static final String 
		UTF8 = Charsets.UTF_8.name(),
		EMPTY = "";
	
	private static final String
		FILE_NAME_RUN_BIN = "run.bin",
		FILE_NAME_RUN_PROTOTEXT = "run.prototext",
		FILE_NAME_RUN_REVIEW_PROTOTEXT = "run-review.prototext",
		FILE_NAME_RUN_REVIEW_BIN = "run-review.bin",
		FILE_NAME_EVALUATION_BIN = "evaluation.bin";
	
	public static final LoadingCache<String, String>
		FILE_CACHE = CacheBuilder.newBuilder()
	       .maximumWeight(1073741824)
	       .weigher(new Weigher<String, String>() {
	          public int weigh(String k, String v) {
	            return v.length();
	          }
	        })
	       .build(new CacheLoader<String, String>() {
              public String load(String key)
              throws IOException {
                return FileUtils.readFileToString(new File(key), UTF8);
              }
            });
	
	private static final LoadingCache<String, Evaluation>
		EVALUATION_CACHE = CacheBuilder.newBuilder()
			.maximumSize(10000)
			.build(new CacheLoader<String, Evaluation>() {
				public Evaluation load(String key) throws IOException {
					return Evaluation.parseFrom(FileUtils
							.readFileToByteArray(new File(key)));
				}
			});

	private static final LoadingCache<String, Run>
		RUN_CACHE = CacheBuilder.newBuilder()
			.maximumSize(10000)
			.build(new CacheLoader<String, Run>() {
				public Run load(String key) throws IOException {
					return Run.parseFrom(FileUtils
							.readFileToByteArray(new File(key)));
				}
			});

	private static final LoadingCache<String, RunReview>
		RUN_REVIEW_CACHE = CacheBuilder.newBuilder()
			.maximumSize(10000)
			.build(new CacheLoader<String, RunReview>() {
				public RunReview load(String key) throws IOException {
					return RunReview.parseFrom(FileUtils
							.readFileToByteArray(new File(key)));
				}
			});
	
	public static Run
	createRun(String taskId, String softwareId, Dataset dataset, String run, 
			String outputDirName) {
		Run.Builder rb = Run.newBuilder();
		rb.setSoftwareId(softwareId);
		rb.setRunId(outputDirName);
		rb.setInputDataset(dataset.getDatasetId());
		rb.setInputRun(run);
		rb.setDeleted(false);
		rb.setDownloadable(!dataset.getIsConfidential());
		rb.setAccessToken(UUID.randomUUID().toString());
		
		// TODO: This is a hack. It is required to be able to distinguish
		// runs by task, since in the current organization, two tasks
		// with input datasets by the same name will cause the runs to
		// end up in the same directory on disk, making them
		// indistinguishable. This will have to be fixed later, and then
		// this hack may be removed again.
		if (!rb.hasTaskId())
			rb.setTaskId(taskId);
		
		return rb.build();
	}
	
	public static File 
	findRun(String userName, String runId)
	throws IOException {
		Tasks tasks = TasksStore.readTasks();
		for (Task task : tasks.getTasksList()) {
			Collection<File> taskUserDatasets = 
					TasksStore.getTaskUserDatasetsWithRuns(userName, task);
			for (File taskUserDataset : taskUserDatasets) {
				File userRuns = new File(taskUserDataset, userName);
				for (File run : userRuns.listFiles()) {
					if (run.getName().equals(runId)) {
						return run;
					}
				}
			}
		}
		return null;
	}
	
	public static File 
	findRun(String taskId, String userName, String runId)
	throws IOException {
		Task t = TasksStore.getTask(taskId);
		Collection<File> taskUserDatasets = 
				TasksStore.getTaskUserDatasetsWithRuns(userName, t);
		for (File taskUserDataset : taskUserDatasets) {
			File userRuns = new File(taskUserDataset, userName);
			for (File run : userRuns.listFiles()) {
				if (run.getName().equals(runId)) {
					return run;
				}
			}
		}
		return null;
	}
	
	public static void
	deleteRun(File run, String taskId, String runId, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		if (run.exists()) {
			FileUtils.deleteDirectory(run);
		}
		
		// TODO The old way of handling deletions can be removed eventually (2017-05-04).
//		File runPrototext = new File(run, FILE_NAME_RUN_PROTOTEXT);
//		if (!runPrototext.exists()) return;
//		Run r = readRun(runPrototext, sc);
//		Run.Builder rb = Run.newBuilder(r);
//		rb.setDeleted(true);
//		r = rb.build();
//		saveRun(r, runPrototext, sc);
	}
	
	public static class RunStore {
		
		private File dataRunDir;
		
		private RunStore(File dataRunDir) {
			this.dataRunDir = dataRunDir;
		}
		
		public void saveRun(Run r, ServletContext sc)
		throws IOException, ServletException {
			File runPrototext = new File(dataRunDir, FILE_NAME_RUN_PROTOTEXT);
			// This ensures the NFS cache is up to date
			String command = String.format(CommandLineExecutor.CMD_LIST_FILES, 
					dataRunDir.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
			RunsStore.saveRun(r, runPrototext, sc);
		}
		
	}
	
	public static RunStore
	getOrCreateRunStore(String dataset, String runId, User u, boolean create,
			ServletContext sc)
	throws IOException,	ServletException {
		File dataRunsDataset = new File(Directories.RUNS, dataset);
		File dataRunsDatasetUser = new File(dataRunsDataset, u.getUserName());
		File dataRunDir = new File(dataRunsDatasetUser, runId);
		if (create && !dataRunDir.exists()) {
			String command = String.format(
					CommandLineExecutor.CMD_MKDIR_AS_TIRA,
					dataRunDir.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		
		RunStore rs = new RunStore(dataRunDir);
		
		return rs;
	}
	
	private static RunReview
	createRunReview(String runId, String reviewerId, Boolean noErrors, 
			Boolean missingOutput, Boolean extraOutput, Boolean invalidOutput,
			Boolean hasErrorOutput, Boolean otherErrors, String comment,
			Boolean published, Boolean blinded) {
		RunReview.Builder rrb = RunReview.newBuilder();
		rrb.setRunId(runId);
		rrb.setReviewerId(reviewerId);
		String date = new Date().toString();
		rrb.setReviewDate(date);
		if (noErrors != null) rrb.setNoErrors(noErrors);
		if (missingOutput != null) rrb.setMissingOutput(missingOutput);
		if (extraOutput != null) rrb.setExtraneousOutput(extraOutput);
		if (invalidOutput != null) rrb.setInvalidOutput(invalidOutput);
		if (hasErrorOutput != null) rrb.setHasErrorOutput(hasErrorOutput);
		if (otherErrors != null) rrb.setOtherErrors(otherErrors);
		if (comment != null) rrb.setComment(comment);
		rrb.setHasErrors(
				rrb.getInvalidOutput() ||
				rrb.getMissingOutput() ||
				rrb.getOtherErrors());
		rrb.setHasWarnings(
				rrb.getHasErrorOutput() || 
				rrb.getExtraneousOutput());
		rrb.setHasNoErrors(
				rrb.getNoErrors() &&
				!rrb.getHasErrors() &&
				!rrb.getHasWarnings());
		if (published != null) rrb.setPublished(published);
		if (blinded != null) rrb.setBlinded(blinded);
		return rrb.build();
	}
	
	private static File
	getOrCreateRunReviewPrototext(String taskId, String userName, String runId,
			boolean create)
	throws IOException, ServletException {
		return getOrCreateRunReviewPrototext(taskId, userName, runId, create, null);
	}
	
	private static File
	getOrCreateRunReviewPrototext(String taskId, String userName, String runId,
			boolean create, ServletContext sc)
	throws IOException, ServletException {
		File runDir = findRun(taskId, userName, runId);
		File runReviewPrototext = new File(runDir, FILE_NAME_RUN_REVIEW_PROTOTEXT);
		if (create && !runReviewPrototext.exists() && sc != null) {
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runReviewPrototext.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		File runReviewBin = new File(runDir, FILE_NAME_RUN_REVIEW_BIN);
		if (create && !runReviewBin.exists() && sc != null) {
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runReviewBin.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		return runReviewPrototext;
	}

	public static void 
	updateRunReview(String taskId, String userName, String reviewerId,
			String runId, Boolean noErrors, Boolean missingOutput,
			Boolean extraOutput, Boolean invalidOutput, Boolean hasErrorOutput,
			Boolean otherErrors, String comment, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		Boolean published = null;
		Boolean blinded = null;
		File runReview = getOrCreateRunReviewPrototext(taskId, userName, runId, false);
		if (runReview.exists()) {
			RunReview rrOld = readRunReview(runReview, sc);
			if (rrOld.hasPublished()) {
				published = rrOld.getPublished();
			}
			if (rrOld.hasBlinded()) {
				blinded = rrOld.getBlinded();
			}
		}
		RunReview rr = createRunReview(runId, reviewerId, noErrors, 
				missingOutput, extraOutput, invalidOutput, hasErrorOutput,
				otherErrors, comment, published, blinded);
		saveRunReview(taskId, userName, runId, rr);
	}
	
	public static void 
	updateRunReview(String taskId, String userName, String reviewerId,
			String runId, Boolean published, Boolean blinded, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		Boolean noErrors = null;
		Boolean missingOutput = null;
		Boolean extraOutput = null;
		Boolean invalidOutput = null;
		Boolean hasErrorOutput = null;
		Boolean otherErrors = null;
		String comment = null;
		File runReview = getOrCreateRunReviewPrototext(taskId, userName, runId, false);
		if (runReview.exists()) {
			RunReview rrOld = readRunReview(runReview, sc);
			noErrors = rrOld.hasNoErrors() ? rrOld.getNoErrors() : null;
			missingOutput = rrOld.hasMissingOutput() ? rrOld.getMissingOutput() : null;
			extraOutput = rrOld.hasExtraneousOutput() ? rrOld.getExtraneousOutput() : null;
			invalidOutput = rrOld.hasInvalidOutput() ? rrOld.getInvalidOutput() : null;
			hasErrorOutput = rrOld.hasHasErrorOutput() ? rrOld.getHasErrorOutput() : null;
			otherErrors = rrOld.hasOtherErrors() ? rrOld.getOtherErrors() : null;
			if (published == null) published = rrOld.getPublished() ? true : null;
			if (blinded == null) blinded = rrOld.getBlinded() ? null : false;
		}
		RunReview rr = createRunReview(runId, reviewerId, noErrors, 
				missingOutput, extraOutput, invalidOutput, hasErrorOutput,
				otherErrors, comment, published, blinded);
		saveRunReview(taskId, userName, runId, rr);
	}

	private static void
	saveRunReview(String taskId, String userName, String runId, RunReview rr)
	throws IOException, ServletException {
		File runReview = getOrCreateRunReviewPrototext(taskId, userName, 
				runId, true);
		saveRunReview(rr, runReview);
	}
	
	private static void 
	saveRunReview(RunReview rr, File runReview)
	throws IOException {
		FileWriter writer = new FileWriter(runReview);
		TextFormat.print(rr, writer);
		writer.close();
		File runReviewBin = new File(runReview.getParentFile(), FILE_NAME_RUN_REVIEW_BIN);
		OutputStream out = new FileOutputStream(runReviewBin);
		rr.writeTo(out);
		out.close();
		
		FILE_CACHE.invalidate(runReview.getAbsolutePath());
		RUN_REVIEW_CACHE.invalidate(runReviewBin.getAbsolutePath());
	}
	
	public static Run readRunFromRunDir(String taskId, File run, ServletContext sc)
	throws IOException, ExecutionException, ServletException {
		File runPrototext = new File(run, FILE_NAME_RUN_PROTOTEXT);
		return readRun(runPrototext, sc);
	}
	
	public static Run 
	readRun(File runPrototext, ServletContext sc) 
	throws IOException, ExecutionException, ServletException {
		File runBin = new File(runPrototext.getParentFile(), FILE_NAME_RUN_BIN);
		if (runBin.exists()) {
			return RUN_CACHE.get(runBin.getAbsolutePath());
		}
		else if (runPrototext.exists()) {
			Run.Builder rb = Run.newBuilder();
			String prototext = FILE_CACHE.get(runPrototext.getAbsolutePath());
			TextFormat.merge(prototext, rb);
			Run r = rb.build();
			
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runBin.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
			OutputStream out = new FileOutputStream(runBin);
			r.writeTo(out);
			out.close();
			
			return r;
		}
		return null;
	}
	
	public static void 
	saveRun(Run r, File runPrototext, ServletContext sc)
	throws IOException, ServletException {
		if (!runPrototext.exists()) {
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runPrototext.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		FileWriter writer = new FileWriter(runPrototext);
		TextFormat.print(r, writer);
		writer.close();
		
		File runBin = new File(runPrototext.getParentFile(), FILE_NAME_RUN_BIN);
		if (!runBin.exists()) {
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runBin.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		OutputStream out = new FileOutputStream(runBin);
		r.writeTo(out);
		out.close();
		
		FILE_CACHE.invalidate(runPrototext.getAbsolutePath());
		RUN_CACHE.invalidate(runBin.getAbsolutePath());
	}
	
	public static RunReview
	readRunReview(File runReviewPrototext, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		File runReviewBin = new File(runReviewPrototext.getParentFile(), FILE_NAME_RUN_REVIEW_BIN);
		if (runReviewBin.exists()) {
			return RUN_REVIEW_CACHE.get(runReviewBin.getAbsolutePath());
		}
		else if (runReviewPrototext.exists()) {
			RunReview.Builder rrb = RunReview.newBuilder();
			String prototext = FILE_CACHE.get(runReviewPrototext.getAbsolutePath());
			TextFormat.merge(prototext, rrb);
			RunReview rr = rrb.build();
			
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					runReviewBin.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
			OutputStream out = new FileOutputStream(runReviewBin);
			rr.writeTo(out);
			out.close();
			
			return rr;
		}
		return null;
	}
	
	public static Evaluation
	readEvaluation(File evaluationPrototext, List<String> measureKeys, ServletContext sc)
	throws IOException, ExecutionException, ServletException {
		File evaluationBin = new File(evaluationPrototext.getParentFile(), FILE_NAME_EVALUATION_BIN);
		if (evaluationBin.exists()) {
			return EVALUATION_CACHE.get(evaluationBin.getAbsolutePath());
		}
		else if (evaluationPrototext.exists()) {
			Evaluation.Builder eb = Evaluation.newBuilder();
			String prototext;
			prototext = FILE_CACHE.get(evaluationPrototext.getAbsolutePath());
			TextFormat.merge(prototext, eb);
						
			if (measureKeys != null && measureKeys.size() > 0) {
				// Duplicate keys in the measureKeys list are allowed.
				// The multimap ensures that no measures with the same key are lost.
				List<Measure.Builder> measures = eb.getMeasureBuilderList();
				LinkedListMultimap<String, Measure.Builder> measureMap = LinkedListMultimap.create();
				for (Measure.Builder mb : measures) {
					measureMap.put(mb.getKey(), mb);
				}
				eb.clearMeasure();
				for (String key : measureKeys) {
					if (measureMap.containsKey(key)) {
						List<Measure.Builder> measureList = measureMap.get(key); 
						if (measureList.size() > 0) {
							eb.addMeasure(measureList.remove(0));
						}
					}
					else {
						Measure.Builder mb = eb.addMeasureBuilder();
						mb.setKey(key);
						mb.setValue(EMPTY);
					}
				}
			}
			
			Evaluation e = eb.build();
			
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					evaluationBin.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
			OutputStream out = new FileOutputStream(evaluationBin);
			e.writeTo(out);
			out.close();
			
			EVALUATION_CACHE.put(evaluationBin.getAbsolutePath(), e);
			
			return e;
		}
		return null;
	}
}
