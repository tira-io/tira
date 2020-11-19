package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.FileFilter;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.Set;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.common.collect.Iterators;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Hosts;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.TaskOrBuilder;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;

public class TasksStore {
	
	private static final String 
		FILE_TYPE_PROTOTEXT  = ".prototext",
		FILE_NAME_ORGANIZERS_PROTOTEXT = "organizers.prototext",
		UTF8 = Charsets.UTF_8.name();
	
	public static Tasks readTasks() throws IOException {
		Tasks.Builder tb = Tasks.newBuilder();
		getTasks(tb);
		return tb.build();
	}

	public static Hosts
	getOrganizers()
	throws IOException {
		File organizers = new File(Directories.ORGANIZERS, FILE_NAME_ORGANIZERS_PROTOTEXT);
		String prototext = FileUtils.readFileToString(organizers, UTF8);
		Hosts.Builder hb = Hosts.newBuilder();
		TextFormat.merge(prototext, hb);
		return hb.build();
	}
	
	public static void
	getTasks(Tasks.Builder tb)
	throws IOException {
		File[] tasks = Directories.TASKS.listFiles(new FileFilter() {
			@Override
			public boolean accept(File pathname) {
				return pathname.isFile() &&
					   pathname.getName().endsWith(FILE_TYPE_PROTOTEXT);
			}
			
		});
		Arrays.sort(tasks);
		if (tasks != null) {
			for (File task : tasks) {
				String prototext = FileUtils.readFileToString(task, UTF8);
				Task.Builder tb2 = tb.addTasksBuilder();
				TextFormat.merge(prototext, tb2);
			}
		}
	}
	
	public static File[]
	getTaskUsers(String taskId) {
		File task = new File(Directories.SOFTWARES_MODEL, taskId);
		File[] users = task.listFiles(new FileFilter() {
			@Override
			public boolean accept(File f) {
				return f.isDirectory();
			}
		});
		return users;
	}
	
	public static List<File>
	getTaskRuns(Task.Builder tb) {
		List<File> runs = Lists.newArrayList();
		List<File> taskDatasets = getTaskDatasetsWithRuns(tb);
		for (File taskDataset : taskDatasets) {
			for (File userRuns : taskDataset.listFiles()) {
				runs.addAll(Arrays.asList(userRuns.listFiles()));
			}
		}
		return runs;
	}
	
	public static List<File>
	getTaskDatasetsWithRuns(final TaskOrBuilder t) {
		File[] taskDatasets = Directories.RUNS.listFiles(new FileFilter() {
			
			private Set<String> datasets = Sets.newHashSet(
				Iterators.concat(t.getTrainingDatasetList().iterator(), 
							     t.getTestDatasetList().iterator()));
			
			@Override
			public boolean accept(File f) {
				return datasets.contains(f.getName());
			}
		});
		return Lists.newArrayList(taskDatasets);
	}
	
	public static List<File>
	getTaskDatasetsWithPublishedRuns(final TaskOrBuilder t, final ServletContext sc) {
		File[] taskDatasets = Directories.RUNS.listFiles(new FileFilter() {
			
			private Set<String> datasets = Sets.newHashSet(
				Iterators.concat(t.getTrainingDatasetList().iterator(), 
							     t.getTestDatasetList().iterator()));
			
			@Override
			public boolean accept(File f) {
				if (datasets.contains(f.getName())) {
					String[] command = new String[] {
						"bash",
						"-c",
						"find -maxdepth 3 -type f -name \"run-review.prototext\" -exec grep \"^published: true$\" {} \\; -a -quit",
					};
					StringBuilder stdout = new StringBuilder();
					StringBuilder stderr = new StringBuilder();
					try {
						CommandLineExecutor.executeCommand(command, f, stdout, stderr, true, sc);
					} catch (IOException | ServletException e) {
						throw new RuntimeException(e);
					}
					if ("published: true".equals(stdout.toString().trim())) {
						return true;
					}
				}
				return false;
			}
		});
		return Lists.newArrayList(taskDatasets);
	}
	
	public static List<File>
	getTaskDatasetsWithRuns(final TaskOrBuilder t, final String datasetId) {
		File[] taskDatasets = Directories.RUNS.listFiles(new FileFilter() {
			
			@Override
			public boolean accept(File f) {
				return f.getName().equals(datasetId);
			}
		});
		return Lists.newArrayList(taskDatasets);
	}
	
	public static List<File> 
	getTaskUserDatasetsWithRuns(final User u, final Task t) {
		return getTaskUserDatasetsWithRuns(u.getUserName(), t);
	}
	
	public static List<File> 
	getTaskUserDatasetsWithRuns(final String userName, final Task t) {
		Collection<File> taskDatasets = getTaskDatasetsWithRuns(t);
		List<File> taskUserDatasets = Lists.newArrayList();
		for (File taskDataset : taskDatasets) {
			Set<String> runs = Sets.newHashSet(taskDataset.list());
			if (runs.contains(userName)) {
				taskUserDatasets.add(taskDataset);
			}
		}
		return taskUserDatasets;
	}

	public static Task 
	getTask(String taskId) 
	throws IOException {
		Tasks tasks = readTasks();
		for (Task t : tasks.getTasksList()) {
			if (t.getTaskId().equals(taskId)) {
				return t;
			}
		}
		return null;
	}
}
