package de.webis.tira.client.web;

import java.io.File;
import java.io.IOException;
import java.util.List;
//import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

//import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.common.collect.Lists;
//import com.google.common.collect.Sets;

import de.webis.tira.client.web.generated.TiraClientWebMessages.Hosts;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Hosts.Host;
//import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares;
//import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task.TaskStatistics;
import de.webis.tira.client.web.request.Checker;
import de.webis.tira.client.web.response.Renderer;
//import de.webis.tira.client.web.state.SoftwaresState;
//import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.TasksStore;

@WebServlet(TasksServlet.ROUTE)
@SuppressWarnings("serial")
public class TasksServlet extends HttpServlet {
	
	public static final String ROUTE = "/tasks/*";
	
	private static final String	
		ROUTE_TASKS = "^/$",
		ROUTE_TASKS_HOST_ID = "^/(?<hostId>[a-zA-Z0-9-]+)/$";
	
	private static final String
		GROUP_NAME_HOST_ID = "hostId";
	
	private static final Pattern
    	PATTERN_TASKS = Pattern.compile(ROUTE_TASKS, Pattern.CASE_INSENSITIVE),
	    PATTERN_TASKS_HOST_ID = Pattern.compile(ROUTE_TASKS_HOST_ID, Pattern.CASE_INSENSITIVE);
	
	private static final String 
		TEMPLATE_TASKS = "/templates/tira-tasks.mustache",
		TEMPLATE_TASK_FROM_HOST = "/templates/tira-tasks-host.mustache";
	
	private static final Object
		HIGHLIGHT_TASKS_LINK = new Object() {
			@SuppressWarnings("unused")
			boolean highlightTasksLink = true;
		};
	
	@Override
	protected void 
	doGet(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		try {
			String path = req.getPathInfo();
			if (path.matches(ROUTE_TASKS)) getRouteTasks(req, resp);			
			else if (path.matches(ROUTE_TASKS_HOST_ID)) getRouteTasksHostId(req, resp);
		} catch (ExecutionException e) {
			throw new ServletException(e);
		}
	}
	
	private void 
	getRouteTasks(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequestTasks(req, resp)) return;
		Matcher m = PATTERN_TASKS.matcher(req.getPathInfo());
		m.find();
		
		Hosts h = getTasksByHost();
		Renderer.render(getServletContext(), req, resp, TEMPLATE_TASKS, h,
				HIGHLIGHT_TASKS_LINK);
	}
	
	private void 
	getRouteTasksHostId(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest2(req, resp)) return;
		Matcher m = PATTERN_TASKS_HOST_ID.matcher(req.getPathInfo());
		m.find();
		String hostId = m.group(GROUP_NAME_HOST_ID);
		
		Tasks.Builder tb = Tasks.newBuilder();
		tb.addAllTasks(getTasksByHost(hostId, readTasksAndTaskStatistics()));
		Tasks t = tb.build();
		Renderer.render(
				getServletContext(), req, resp, TEMPLATE_TASK_FROM_HOST, t,
				HIGHLIGHT_TASKS_LINK);
	}

	private Hosts
	getTasksByHost() throws IOException, ServletException {
		Tasks tasks = readTasksAndTaskStatistics();
		Hosts hosts = TasksStore.getOrganizers();
		Hosts.Builder hb1 = Hosts.newBuilder(hosts);
		for (Host.Builder hb2 : hb1.getHostsBuilderList()) {
			hb2.addAllTasks(getTasksByHost(hb2.getHostId(), tasks));
		}
		hosts = hb1.build();
		return hosts;
	}

	private List<Task>
	getTasksByHost(String hostId, Tasks tasks) {
		List<Task> tasksByHost = Lists.newArrayList();
		for (Task task : tasks.getTasksList()) {
			if (hostId.equals(task.getHostId())) {
				tasksByHost.add(task);
			}
		}
		return tasksByHost;
	}
	
	private Tasks
	readTasksAndTaskStatistics()
	throws IOException, ServletException {
		Tasks.Builder tb = Tasks.newBuilder();
		TasksStore.getTasks(tb);
		collectTaskStatistics(tb);
		Tasks t = tb.build();
		return t;
	}
	
	private void
	collectTaskStatistics(Tasks.Builder tb)
	throws IOException, ServletException {
		for (Task.Builder t : tb.getTasksBuilderList()) {
			collectTaskStatistics(t);
		}
	}
	
	private void
	collectTaskStatistics(Task.Builder tb)
	throws IOException, ServletException {
		TaskStatistics.Builder tsb = TaskStatistics.newBuilder();
		tsb.setParticipants(collectTaskParticipants(tb.getTaskId()));
//		tsb.setSoftwares(collectTaskSoftwares(tb.getTaskId()));
//		tsb.setSoftwaresRunning(collectTaskSoftwaresRunning(tb));
//		tsb.setShowSoftwaresRunning(tsb.getSoftwaresRunning() > 0);
//		tsb.setRuns(collectTaskRuns(tb));
		tb.setTaskStatistics(tsb);
	}
	
	private int
	collectTaskParticipants(String taskId) {
		File[] users = TasksStore.getTaskUsers(taskId);
		return (users == null) ? 0 : users.length;
	}

	/*private int
	collectTaskSoftwares(String taskId)
	throws IOException, ServletException {
		File[] users = TasksStore.getTaskUsers(taskId);
		if (users == null) return 0;
		int softwares = 0;
		for (File user : users) {
			Softwares s1 = SoftwaresStore.readSoftwares(taskId, user.getName());
			for (Software s2 : s1.getSoftwaresList()) {
				if (!s2.getDeleted()) {
					softwares++;
				}
			}
		}
		return softwares;
	}
	
	private int
	collectTaskSoftwaresRunning(Task.Builder tb)
	throws IOException, ServletException {
		Set<String> taskRunNames = getTaskRunsNames(tb);
		ServletContext sc = getServletContext();
		Set<String> runningProcessesRunNames = SoftwaresState.getRunningProcessesRunNames(sc);
		return Sets.intersection(taskRunNames, runningProcessesRunNames).size();
	}

	private static Set<String>
	getTaskRunsNames(Task.Builder tb) {
		List<File> taskRuns = TasksStore.getTaskRuns(tb);
		Set<String> taskRunNames = Sets.newHashSet();
		for (File run : taskRuns) {
			taskRunNames.add(run.getName());
		}
		return taskRunNames;
	}
	
	private static int
	collectTaskRuns(Task.Builder tb)
	throws IOException {
		// This variant includes deleted RUNS
		return TasksStore.getTaskRuns(tb).size();
		// The below version does not, but it is too slow.
//		int RUNS = 0;
//		for (File run : getTaskRuns(tb)) {
//			File runPrototext = new File(run, TaskServlet.FILE_NAME_RUN_PROTOTEXT);
//			Run r = TaskServlet.readRun(runPrototext);
//			if (!r.getDeleted()) {
//				RUNS++;
//			}
//		}
//		return RUNS;
	}*/

	private boolean
	checkRequestTasks(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest2(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
//		if (!c.checkHostExists(req, resp)) return false;
		return true;
	}
}
