package de.webis.tira.client.web.state;

import java.io.File;
import java.io.FileFilter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.concurrent.ExecutionException;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

import scala.actors.threadpool.Arrays;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Ordering;

import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.DatasetRuns;
import de.webis.tira.client.web.generated.TiraClientWebMessages.ExtendedRun;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskDataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskDataset.DatasetListItem;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview.SoftwareRunning;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser.Execution;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState;
import de.webis.tira.client.web.storage.DatasetsStore;
import de.webis.tira.client.web.storage.Directories;
import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.TasksStore;
import de.webis.tira.client.web.storage.UsersStore;

public class TasksState {
	
	private static final String
		FILE_NAME_RUN_REVIEW_PROTOTEXT = "run-review.prototext",
		FILE_NAME_EVALUATION_PROTOTEXT = "evaluation.prototext",
		FILE_NAME_SOFTWARES_PROTOTEXT = "softwares.prototext",
		FOLDER_RUN_OUTPUT = "output";

	public static TaskReview
	collectTaskReviewAllRuns(Task t, String datasetId,
			boolean testDatasetsOnly, boolean publicRunsOnly, ServletContext sc,
			HttpServletRequest req)
	throws ServletException, IOException, ExecutionException {
		List<File> taskDatasets = TasksStore.getTaskDatasetsWithRuns(t, datasetId);
		return collectTaskReview(t, taskDatasets, testDatasetsOnly,
				publicRunsOnly, true, false, false, sc, req);
	}
	
	public static TaskReview
	collectTaskReviewEvaluatorRuns(Task t, String datasetId,
			boolean testDatasetsOnly, boolean publicRunsOnly, ServletContext sc,
			HttpServletRequest req)
	throws ServletException, IOException, ExecutionException {
		List<File> taskDatasets = TasksStore.getTaskDatasetsWithRuns(t, datasetId);
		return collectTaskReview(t, taskDatasets, testDatasetsOnly,
				publicRunsOnly, false, true, false, sc, req);
	}
	
	public static TaskReview
	collectTaskReviewTaskUsers(Task t, boolean testDatasetsOnly,
			boolean publicRunsOnly, ServletContext sc, HttpServletRequest req)
	throws ServletException, IOException, ExecutionException {
		List<File> taskDatasets = TasksStore.getTaskDatasetsWithRuns(t);
		Collections.sort(taskDatasets, Ordering.natural());
		return collectTaskReview(t, taskDatasets, testDatasetsOnly, 
				publicRunsOnly, false, false, true, sc, req);
	}
	
	private static TaskReview
	collectTaskReview(Task t, List<File> taskDatasets, boolean testDatasetsOnly,
			boolean publicRunsOnly, boolean allRuns, boolean evaluatorRuns,
			boolean onlyTaskUser, ServletContext sc, HttpServletRequest req)
	throws ServletException, IOException, ExecutionException {
		TaskReview.Builder trb = TaskReview.newBuilder();
		trb.setTask(t);
		
		String taskId = t.getTaskId();
		List<TaskReview.TaskUser.Builder> 
			taskUsers = collectTaskReviewTaskUsers(trb, taskId, req);
		
		Map<String, SoftwareRunning.Builder> 
			runningSoftwares = SoftwaresState.collectRunningSoftwares(sc);
		
		Map<String, List<ExtendedRun>> runIndex = Maps.newTreeMap();
		Map<String, List<ExtendedRun>> evaluatorRunIndex = Maps.newTreeMap();
		for (File taskDataset : taskDatasets) {
			if (testDatasetsOnly &&
				!DatasetsStore.isConfidential(taskId, taskDataset.getName())) {
				continue;
			}
			for (TaskReview.TaskUser.Builder tub : taskUsers) {
				String datasetName = taskDataset.getName();
				String userName = tub.getUser().getUserName();
				File taskDatasetUser = new File(taskDataset, userName);
				if (!taskDatasetUser.exists()) continue;
				SoftwareRunning.Builder srb = runningSoftwares.get(userName);
				tub.setSoftwareRunning(tub.getSoftwareRunning() || false);
				// This will be set to true once the corresponding run is found.
				File[] runs = taskDatasetUser.listFiles();
				tub.setRunsTotal(tub.getRunsTotal() + runs.length);
				for (File run : runs) {
					File review = new File(run, FILE_NAME_RUN_REVIEW_PROTOTEXT);
					if (review.exists()) {
						tub.setRunsReviewed(tub.getRunsReviewed() + 1);
					}
					else {
						tub.setRunsUnreviewed(tub.getRunsUnreviewed() + 1);
					}
					if (srb != null && run.getName().equals(srb.getRunId())) {
						tub.setSoftwareRunning(true);
						tub.setRunningSoftware(srb);
					}
					
					if (onlyTaskUser) continue;
					
					ExtendedRun er = null;
					if (allRuns) {
						er = RunsState.collectExtendedRun(taskId, run, false, false, false, sc);
						if (er == null) continue;
						if (publicRunsOnly) {
							if (!er.hasRunReview() || 
								!er.getRunReview().getPublished()) {
								continue;
							}
						}
						
						if (!runIndex.containsKey(datasetName)) {
							runIndex.put(datasetName, new ArrayList<ExtendedRun>());
						}
						runIndex.get(datasetName).add(er);
					}
					
					if (evaluatorRuns) {
						File output = new File(run, FOLDER_RUN_OUTPUT);
						File evaluationPrototext = new File(output, FILE_NAME_EVALUATION_PROTOTEXT);
						if (evaluationPrototext.exists()) {
							if (er == null) {
								er = RunsState.collectExtendedRun(taskId, run, false, false, false, sc);
								if (er == null) continue;
								if (publicRunsOnly) {
									if (!er.hasRunReview() || 
										!er.getRunReview().getPublished()) {
										continue;
									}
								}
							}
							if (!evaluatorRunIndex.containsKey(datasetName)) {
								evaluatorRunIndex.put(datasetName, new ArrayList<ExtendedRun>());
							}
							evaluatorRunIndex.get(datasetName).add(er);
						}
					}
				}
			}
		}
		
		for (Entry<String, List<ExtendedRun>> e : runIndex.entrySet()) {
			Dataset d = DatasetsStore.getDataset(taskId, e.getKey());
			DatasetRuns.Builder drb = trb.addRunsBuilder();
			drb.setDataset(e.getKey());
			drb.setDatasetDeprecated(d.getIsDeprecated());
			for (ExtendedRun er : e.getValue()) {
				drb.addRuns(er);
			}
		}
		trb.setHasRuns(trb.getRunsCount() > 0);
		
		for (Entry<String, List<ExtendedRun>> e : evaluatorRunIndex.entrySet()) {
			Dataset d = DatasetsStore.getDataset(taskId, e.getKey());
			DatasetRuns.Builder drb = trb.addEvaluatorRunsBuilder();
			drb.setDataset(e.getKey());
			drb.setDatasetDeprecated(d.getIsDeprecated());
			for (ExtendedRun er : e.getValue()) {
				drb.addRuns(er);
			}
		}
		trb.setHasEvaluatorRuns(trb.getEvaluatorRunsCount() > 0);
		
		TaskReview tr = trb.build();
		return tr;
	}

	public static TaskUser 
	collectTaskUser(String taskId, User u, boolean reviewerSignedIn, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		TaskUser.Builder tub = TaskUser.newBuilder();
		tub.setTask(TasksStore.getTask(taskId));
		tub.setUser(u);
		// TODO: Make the distinction of USERS who have VMs and those who don't smarter.
		tub.setHasVm(true);
		VirtualMachineState.Builder vmsb = tub.getVmInfoBuilder();
		VirtualMachinesState.collectVmInfo(vmsb, taskId, u, sc);
		VirtualMachinesState.collectMasterInfo(tub, sc);
		collectSoftwareInfo(taskId, u.getUserName(), tub);
		collectExecutionInfo(taskId, tub);
		RunsState.collectUserRuns(taskId, tub, u, true, sc);
		TaskUser tu = tub.build();
		return tu;
	}

	private static List<TaskReview.TaskUser.Builder>
	collectTaskReviewTaskUsers(TaskReview.Builder trb, String taskId, HttpServletRequest req)
	throws ServletException, IOException {
		File softwaresDir = new File(Directories.SOFTWARES_MODEL, taskId);
		File[] softwaresUserDirs = softwaresDir.listFiles(new FileFilter() {
			
			@Override
			public boolean accept(File pathname) {
				return pathname.isDirectory();
			}
		});
		if (softwaresUserDirs == null) return Lists.newArrayList();
		Arrays.sort(softwaresUserDirs);
		
		List<TaskReview.TaskUser.Builder> softwaresUsers = Lists.newArrayList();
		for (File softwaresUserDir : softwaresUserDirs) {
			TaskReview.TaskUser.Builder tub = trb.addTaskUsersBuilder();
			tub.setSoftwares(0);
			tub.setSoftwaresDeleted(0);
			tub.setSoftwareRunning(false);
			tub.setRunsTotal(0);
			tub.setRunsReviewed(0);
			tub.setRunsUnreviewed(0);
			
			String userName = softwaresUserDir.getName();
			User u = UsersStore.getUser(userName);
			if (u != null) {
				tub.setUser(u);
			}
			tub.setUserSignedIn(Authenticator.isSignedIn(req));
			
			File softwares = new File(softwaresUserDir, FILE_NAME_SOFTWARES_PROTOTEXT);
			if (softwares.exists()) {
				Softwares s = SoftwaresStore.readSoftwares(taskId, userName);
				tub.setSoftwares(s.getSoftwaresCount());
				
				for (Software software : s.getSoftwaresList()) {
					if (software.getDeleted()) {
						tub.setSoftwaresDeleted(tub.getSoftwaresDeleted() + 1);
					}
				}
			}
			
			softwaresUsers.add(tub);
		}
		return softwaresUsers;
	}
	
	private static void 
	collectExecutionInfo(String taskId, TaskUser.Builder tub)
	throws IOException {
		Task t = TasksStore.getTask(taskId);
		Execution.Builder eb = tub.getExecutionBuilder();
		for (String datasetId : t.getTrainingDatasetList()) {
			eb.addTrainingDatasets(DatasetsStore.getDataset(taskId, datasetId));
		}
		for (String datasetId : t.getTestDatasetList()) {
			eb.addTestDatasets(DatasetsStore.getDataset(taskId, datasetId));
		}
	}

	public static void 
	collectSoftwareInfo(String task, String userName, TaskUser.Builder tub) 
	throws IOException, ServletException {
		Softwares s = SoftwaresStore.readSoftwares(task, userName, false);
		tub.addAllSoftwares(s.getSoftwaresList());
		for (Software.Builder sb : tub.getSoftwaresBuilderList()) {
			if (!sb.getDeleted()) {
				tub.addSoftwaresNotDeleted(sb);
			}
		}
		tub.setHasSoftwaresNotDeleted(tub.getSoftwaresNotDeletedCount() > 0);
	}

	public static TaskDataset
	collectTaskDataset(Task t)
	throws IOException {
		return collectTaskDataset(t, false, "", null);
	}
	
	public static TaskDataset
	collectTaskDataset(Task t, String activeDatasetId)
	throws IOException {
		return collectTaskDataset(t, false, activeDatasetId, null);
	}
	
	public static TaskDataset
	collectTaskDataset(Task t, boolean mustHavePublishedRuns,
			ServletContext sc)
	throws IOException {
		return collectTaskDataset(t, mustHavePublishedRuns, "", sc);
	}
	
	public static TaskDataset
	collectTaskDataset(Task t, boolean mustHavePublishedRuns,
			String activeDatasetId, ServletContext sc)
	throws IOException {
		TaskDataset.Builder tdb = TaskDataset.newBuilder();
		List<File> datasets;
		if (mustHavePublishedRuns) {
			datasets = TasksStore.getTaskDatasetsWithPublishedRuns(t, sc);
		}
		else {
			datasets = TasksStore.getTaskDatasetsWithRuns(t);
		}
		Collections.sort(datasets, Ordering.natural());
		for (File dataset : datasets) {
			String datasetId = dataset.getName();
			Dataset d = DatasetsStore.getDataset(t.getTaskId(), datasetId); 
			int runsCount = dataset.list().length;
			DatasetListItem.Builder dlib = tdb.addDatasetsBuilder();
			dlib.setDataset(d);
			dlib.setRunsCount(runsCount);
			dlib.setActive(activeDatasetId.equals(datasetId));
		}
		return tdb.build();
	}
}
