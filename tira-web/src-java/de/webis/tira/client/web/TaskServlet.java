package de.webis.tira.client.web;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.Writer;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ExecutionException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.IOUtils;

import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskDataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser.Execution;
import de.webis.tira.client.web.generated.TiraClientWebMessages.ExtendedRun;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;
import de.webis.tira.client.web.request.Checker;
import de.webis.tira.client.web.request.Preprocessor;
import de.webis.tira.client.web.response.Renderer;
import de.webis.tira.client.web.state.RunsState;
import de.webis.tira.client.web.state.SoftwaresState;
import de.webis.tira.client.web.state.TasksState;
import de.webis.tira.client.web.state.VirtualMachinesState;
import de.webis.tira.client.web.storage.DatasetsStore;
import de.webis.tira.client.web.storage.RunsStore;
import de.webis.tira.client.web.storage.RunsStore.RunStore;
import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.SubmissionFilesStore;
import de.webis.tira.client.web.storage.TasksStore;
import de.webis.tira.client.web.storage.UsersStore;
import de.webis.tira.client.web.storage.VirtualMachinesStore;

@WebServlet(TaskServlet.ROUTE)
@SuppressWarnings("serial")
public class TaskServlet extends HttpServlet {

	private static final Object 
		LOCK = new Object();

	public static final String
		ROUTE = "/task/*";
	
	private static final String	
		ROUTE_TASK = "^/(?<taskId>[a-zA-Z0-9-]+)/$",
		ROUTE_TASK_DATASET = "^/(?<taskId>[a-zA-Z0-9-]+)/dataset/(?<datasetId>[a-zA-Z0-9-]+)/$",
		ROUTE_TASK_USER = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/$",
		ROUTE_TEST_UNPOLY_IN_DISRAPTOR = "^/(?<taskId>[a-zA-Z0-9-]+)/unpoly-in-disraptor-test-delete-me-later$",
		ROUTE_TASK_USER_ID = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/.*$",
		ROUTE3 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/vm-metrics/$",
		ROUTE4 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/vm-shutdown/$",
		ROUTE5 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/vm-start/$",
		ROUTE6 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/vm-stop/$",
		ROUTE7 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/vm-screenshot.png$",
		ROUTE8 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/$",
		ROUTE9 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/(?<softwareId>software\\d+)/save/$",
		ROUTE10 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/(?<softwareId>software\\d+)/delete/$",
		ROUTE11 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/(?<softwareId>software\\d+)/run/$",
		ROUTE12 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/(?<softwareId>software\\d+)/kill/$",
		ROUTE13 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/evaluator/run/$",
		ROUTE14 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/evaluator/kill/$",
		ROUTE15 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+).zip/*$",
		ROUTE16 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/delete/$",
		ROUTE17 = "^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/view/$";
	
	private static final String
 		GROUP_NAME_TASK_ID = "taskId",
 		GROUP_NAME_DATASET_ID = "datasetId",
 		GROUP_NAME_USER_NAME = "userName",
 		GROUP_NAME_SOFTWARE_ID = "softwareId",
 		GROUP_NAME_RUN_ID = "runId";

	private static final Pattern
	    PATTERN_TASK = Pattern.compile(ROUTE_TASK, Pattern.CASE_INSENSITIVE),
	    PATTERN_TASK_DATASET = Pattern.compile(ROUTE_TASK_DATASET, Pattern.CASE_INSENSITIVE),
   	    PATTERN_TASK_USER = Pattern.compile(ROUTE_TASK_USER, Pattern.CASE_INSENSITIVE),
 		PATTERN_USER_ID_PATHS = Pattern.compile(ROUTE_TASK_USER_ID),
   	 	PATTERN3 = Pattern.compile(ROUTE3, Pattern.CASE_INSENSITIVE),
   	 	PATTERN4 = Pattern.compile(ROUTE4, Pattern.CASE_INSENSITIVE),
   	    PATTERN5 = Pattern.compile(ROUTE5, Pattern.CASE_INSENSITIVE),
   	    PATTERN6 = Pattern.compile(ROUTE6, Pattern.CASE_INSENSITIVE),
  	    PATTERN7 = Pattern.compile(ROUTE7, Pattern.CASE_INSENSITIVE),
  	    PATTERN8 = Pattern.compile(ROUTE8, Pattern.CASE_INSENSITIVE),
  		PATTERN9 = Pattern.compile(ROUTE9, Pattern.CASE_INSENSITIVE),
		PATTERN10 = Pattern.compile(ROUTE10, Pattern.CASE_INSENSITIVE),
  	    PATTERN11 = Pattern.compile(ROUTE11, Pattern.CASE_INSENSITIVE),
  	    PATTERN12 = Pattern.compile(ROUTE12, Pattern.CASE_INSENSITIVE),
	    PATTERN13 = Pattern.compile(ROUTE13, Pattern.CASE_INSENSITIVE),
	    PATTERN14 = Pattern.compile(ROUTE14, Pattern.CASE_INSENSITIVE),
	    PATTERN15 = Pattern.compile(ROUTE15, Pattern.CASE_INSENSITIVE),
		PATTERN16 = Pattern.compile(ROUTE16, Pattern.CASE_INSENSITIVE),
		PATTERN17 = Pattern.compile(ROUTE17, Pattern.CASE_INSENSITIVE);
	
	private static final String
		FORM_FIELD_COMMAND = "command",
		FORM_FIELD_WORKING_DIRECTORY = "workingDirectory",
		FORM_FIELD_DATASET = "dataset",
		FORM_FIELD_RUN = "run";
	
	private static final String 
		TEMPLATE_TASK = "/templates/tira-task.mustache",
		TEMPLATE_TASK_DATASET = "/templates/tira-task-dataset.mustache",
		TEMPLATE_TASK_USER_IDLE = "/templates/tira-task-user-idle.mustache",
		TEMPLATE_TASK_USER_BUSY = "/templates/tira-task-user-busy.mustache",
		TEMPLATE_TASK_USER_RUN = "/templates/tira-task-user-run.mustache";
	
	private static final String 
		HEADER_LOCATION = "Location",
		HEADER_CONTENT_DISPOSITION = "Content-Disposition",
		HEADER_CONTENT_DISPOSITION_ATTACHMENT = "attachment; filename=\"%s-%s-run-%s.zip\"",
		HEADER_CONTENT_TYPE_IMAGE_PNG = "image/png",
		HEADER_CONTENT_TYPE_APPLICATION_ZIP = "application/zip",
		HEADER_CACHE_CONTROL = "Cache-Control",
		HEADER_CACHE_CONTROL_NO_CACHING = "no-cache, no-store, must-revalidate",
		HEADER_PRAGMA = "Pragma",
		HEADER_PRAGMA_NO_CACHE = "no-cache",
		HEADER_EXPIRES = "Expires";
	
	private static final int 
		HEADER_EXPIRES_0 = 0;
	
	private static final String
		FILE_PEFIX_RUN = "run-",
		FILE_TYPE_ZIP = ".zip",
		FILE_TYPE_PNG = ".png",
		FOLDER_UNIX_TMP = "/tmp";
		
	private static final String
		SOFTWARE = "software",
		NONE = "none";
	
	private static final String
		TIRA_HOST_USER = "tira";
	
	private static final String 
		DATE_FORMAT_SORTABLE = "YYYY-MM-dd-HH-mm-ss",
		URL_PATH_TASK_USER = "%s/task/%s/user/%s/",
		TRUE_AS_STRING = "\"true\"";
		
	private static final String 
		EMPTY = "";
	
	@Override
	protected void 
	doGet(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		try { 
			String path = req.getPathInfo();
			if (path.matches(ROUTE_TASK)) getRouteTask(req, resp);
			else if (path.matches(ROUTE_TASK_DATASET)) getRouteTaskDataset(req, resp);
			else if (path.matches(ROUTE_TASK_USER)) getRouteTaskUser(req, resp);
			else if (path.matches(ROUTE_TEST_UNPOLY_IN_DISRAPTOR)) getRouteUnpolyTest(req, resp);
			else if (path.matches(ROUTE3)) getRoute3(req, resp);
			else if (path.matches(ROUTE7)) getRoute7(req, resp);
			else if (path.matches(ROUTE15)) getRoute15(req, resp);
			else if (path.matches(ROUTE17)) getRoute17(req, resp);
		} catch (ExecutionException e) {
			throw new ServletException(e);
		}
	}

	@Override
	protected void 
	doPost(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		try {
			String path = req.getPathInfo();
			if (path.matches(ROUTE4)) postRoute4(req, resp);
			else if (path.matches(ROUTE5)) postRoute5(req, resp);
			else if (path.matches(ROUTE6)) postRoute6(req, resp);
			else if (path.matches(ROUTE8)) postRoute8(req, resp);
			else if (path.matches(ROUTE9)) postRoute9(req, resp);
			else if (path.matches(ROUTE10)) postRoute10(req, resp);
			else if (path.matches(ROUTE11)) postRoute11(req, resp);
			else if (path.matches(ROUTE12)) postRoute12(req, resp);
			else if (path.matches(ROUTE13)) postRoute13(req, resp);
			else if (path.matches(ROUTE14)) postRoute14(req, resp);
			else if (path.matches(ROUTE16)) postRoute16(req, resp);
		} catch (ExecutionException e) {
			throw new ServletException(e);
		}
	}

	private void 
	getRouteTask(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest1(req, resp)) return;
		Matcher m = PATTERN_TASK.matcher(req.getPathInfo());
		m.find();
		
		String taskId = m.group(GROUP_NAME_TASK_ID);
		
		ServletContext sc = getServletContext();
		final Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t, true, sc);
		
		@SuppressWarnings("unused")
		Object o = new Object() {
			// TODO: Workaround for tira-task-user-toolbar-body.mustache.
			Task task = t;
			boolean isPublicResults = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_TASK, t, td, o);
	}
	
	private void 
	getRouteTaskDataset(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest1b(req, resp)) return;
		Matcher m = PATTERN_TASK_DATASET.matcher(req.getPathInfo());
		m.find();
		
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String datasetId = m.group(GROUP_NAME_DATASET_ID);
		
		ServletContext sc = getServletContext();
		final Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t, true, datasetId, sc);
		TaskReview tr = TasksState.collectTaskReviewEvaluatorRuns(t, datasetId, false, true, sc, req);
		String evaluatorId = DatasetsStore.getEvaluatorId(taskId, datasetId);
		Evaluator e = SoftwaresStore.getEvaluator(t, evaluatorId);
		
		@SuppressWarnings("unused")
		Object o = new Object() {
			// TODO: Workaround for tira-task-user-toolbar-body.mustache.
			Task task = t;
			boolean isPublicResults = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_TASK_DATASET, t, e, td, tr, o);
	}
	
	private void 
	getRouteTaskUser(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest2(req, resp)) return;
		Matcher m = PATTERN_TASK_USER.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String pathUserName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(pathUserName);
		
		User u2 = Authenticator.signedInUser(req);
		
		boolean reviewerSignedIn = 
			u2.getRolesCount() > 0 && u2.getRolesList().contains("reviewer");

		@SuppressWarnings("unused")
		Object o = new Object() {
			boolean isMySoftware = true;
		};
			
		ServletContext sc = getServletContext();
		if (u.hasVirtualMachineId()) {
			TaskUser tu = TasksState.collectTaskUser(taskId, u, reviewerSignedIn, sc);
			if (tu.getVmInfo().getProcessRunning()) {
				Renderer.render(sc, req, resp, TEMPLATE_TASK_USER_BUSY, tu, o);
			}
			else {
				Renderer.render(sc, req, resp, TEMPLATE_TASK_USER_IDLE, tu, o);
			}
		}
		else {
			TaskUser.Builder tub = TaskUser.newBuilder();
			tub.setTask(TasksStore.getTask(taskId));
			tub.setUser(u);
			tub.setHasVm(false);
			Renderer.render(sc, req, resp, TEMPLATE_TASK_USER_IDLE, tub, o);
		}
	}
	
	private void
	getRouteUnpolyTest(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		@SuppressWarnings("unused")
		Object o = new Object() {
			boolean isMySoftware = true;
		};
		
		Renderer.render(getServletContext(), req, resp, TEMPLATE_TASK_USER_BUSY, dummyUnpolyTestUser(), o);
	}

	static TaskUser
	dummyUnpolyTestUser() {
		Task task = Task.newBuilder()
			.setTaskId("does-not-exist")
			.setTaskName("My Test Task")
			.build();
		Execution execution = Execution.newBuilder()
				.build();
		Run run = Run.newBuilder()
				.setSoftwareId("no-id")
				.setRunId("no-id")
				.setInputDataset("no-input-dataset")
				.setDownloadable(true)
				.setDeleted(false)
				.build();
		ExtendedRun extendedRun = ExtendedRun.newBuilder()
				.setRun(run)
				.setIsRunning(true)
				.setStdout("this is some stdout.")
				.build();
		
		Date start = new Date();
		try {
			Thread.sleep(1000);
		} catch (InterruptedException e) {
			throw new RuntimeException(e);
		}
		
		
		String tmpOutput = "This is my output...\n\nStarted at: " + start +"\nFinished at: " + new Date();
		
		de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState vmInfo = de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState.newBuilder()
			.setPortSshOpen(false)
			.setGuestOs("my-os")
			.setMemorySize("0 byte")
			.setNumberOfCpus("-1")
			.setState("running")
			.setStateSandboxed(true)
			.setStateSandboxing(false)
			.setStateUnsandboxing(false)
			.setStateRunning(true)
			.setLatestOutput(tmpOutput)
			.setHost("ssaas")
			.setPortSsh("-1")
			.setPortRdp("-1")
			.setPortSshOpen(false)
			.setPortRdpOpen(false)
			.setProcessRunning(true)
			.setProcessType("test")
			.setProcessRunId("-1")
			.setProcessState("my-state")
			.setProcessTime("00:00:00")
			.setVmBooting(true)
			.setVmPoweringOff(false)
			.setVmShuttingDown(false)
			.setHasLatestOutput(true)
			.build();
		
		return TaskUser.newBuilder()
			.mergeUser(UsersStore.userWithoutVM())
			.setHasVm(true)
			.addRuns(extendedRun)
			.setHasSoftwaresNotDeleted(false)
			.setHasRunsNotDeleted(false)
			.setHasEvaluatorRunsNotDeleted(false)
			.setHasSoftwareRunsNotDeleted(false)
			.mergeTask(task)
			.setVmInfo(vmInfo)
			.mergeExecution(execution)
			.build();
	}
	
	private void 
	getRoute3(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest3(req, resp)) return;
		Matcher m = PATTERN3.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		
		VirtualMachineState.Builder vmsb = VirtualMachineState.newBuilder();
		ServletContext sc = getServletContext();
		VirtualMachinesState.collectSupervisorState(vmsb, u.getUserName(), sc);
		String metrics = "";
		if (vmsb.getProcessRunning()) {
			Run r = RunsStore.readRunFromRunDir(taskId,
				RunsStore.findRun(taskId, u.getUserName(), vmsb.getProcessRunId()),
				sc);
			if (r != null) {
				Dataset d = DatasetsStore.getDataset(taskId, r.getInputDataset());
				if (d.getIsConfidential()) {
					metrics = "hidden\nhidden";
				}
				else {
					metrics = VirtualMachinesState.collectVirtualMachineMetrics(vmsb, vm, sc);
				}
			}
		}
		
		Writer w = resp.getWriter();
		w.write(metrics);
		w.flush();
		w.close();
	}

	private void 
	postRoute4(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest4(req, resp)) return;
		Matcher m = PATTERN4.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraShutdown(u, taskId, sc);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}
	
	private void 
	postRoute5(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest5(req, resp)) return;
		Matcher m = PATTERN5.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraVmStartStop(u, taskId, false, sc);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}
	
	private void 
	postRoute6(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest6(req, resp)) return;
		Matcher m = PATTERN6.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraVmStartStop(u, taskId, true, sc);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}

	private void 
	getRoute7(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest7(req, resp)) return;
		Matcher m = PATTERN7.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		String command = String.format(CommandLineExecutor.CMD_TIRA_VM_SCREENSHOT,
				TIRA_HOST_USER, vm.getHost(), vm.getVmName());
		ServletContext sc = getServletContext();
		CommandLineExecutor.executeCommand(command, sc);
		
		String fileName = vm.getVmName() + FILE_TYPE_PNG;
		File screenshot = new File(FOLDER_UNIX_TMP, fileName);
		resp.setContentType(HEADER_CONTENT_TYPE_IMAGE_PNG);
		setNoCachingHeaders(resp);
		FileInputStream fis = FileUtils.openInputStream(screenshot); 
		IOUtils.copy(fis, resp.getOutputStream());
		fis.close();
		resp.flushBuffer();
	}

	private void setNoCachingHeaders(HttpServletResponse resp) {
		// http://stackoverflow.com/questions/49547/making-sure-a-web-page-is-not-cached-across-all-browsers
		// HTTP 1.1.
		resp.setHeader(HEADER_CACHE_CONTROL, HEADER_CACHE_CONTROL_NO_CACHING);
        // HTTP 1.0.
		resp.setHeader(HEADER_PRAGMA, HEADER_PRAGMA_NO_CACHE);
		// Proxies.
		resp.setDateHeader(HEADER_EXPIRES, HEADER_EXPIRES_0);
	}
	
	private void 
	postRoute8(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest8(req, resp)) return;
		Matcher m = PATTERN8.matcher(req.getPathInfo());
		m.find();
		String task = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		SoftwaresStore.addSoftware(task, userName, getServletContext());
		redirectToTaskUserPage(req, resp, task, userName);
    }
	
	private void 
	postRoute9(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest9(req, resp)) return;
		Matcher m = PATTERN9.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String softwareId = m.group(GROUP_NAME_SOFTWARE_ID);
		saveSoftware(req, taskId, userName, softwareId);
		redirectToTaskUserPage(req, resp, taskId, userName);
    }

	private void 
	postRoute10(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest10(req, resp)) return;
		Matcher m = PATTERN10.matcher(req.getPathInfo());
		m.find();
		String task = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String softwareId = m.group(GROUP_NAME_SOFTWARE_ID);
		SoftwaresStore.deleteSoftware(task, userName, softwareId);
		redirectToTaskUserPage(req, resp, task, userName);
    }
	
	private void 
	postRoute11(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest11(req, resp)) return;
		Matcher m = PATTERN11.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String softwareId = m.group(GROUP_NAME_SOFTWARE_ID);

		saveSoftware(req, taskId, userName, softwareId);
		
		String datasetId = req.getParameter(FORM_FIELD_DATASET);
		Dataset dataset = DatasetsStore.getDataset(taskId, datasetId);
		String inputRun = req.getParameter(FORM_FIELD_RUN);
		String inputRunDirPath = inputRun;
		if (!NONE.equals(inputRun)) {
			File inputRunDir = findRun(req, resp, taskId, inputRun);
			inputRunDirPath = inputRunDir.getAbsolutePath();
		}

		User u = UsersStore.getUser(userName);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		
		synchronized (LOCK) { 
			
			Checker c = new Checker();
			if (c.checkUserIdle(req, resp)) {
				ServletContext sc = getServletContext();
				
				DateFormat df = new SimpleDateFormat(DATE_FORMAT_SORTABLE);
				String runId = df.format(new Date());
		
				RunStore rs = RunsStore.getOrCreateRunStore(datasetId, runId, u, true, sc);
				
				Run r = RunsStore.createRun(taskId, softwareId, dataset, inputRun, runId);
				rs.saveRun(r, sc);
				
				Software s = SoftwaresStore.findSoftware(taskId, u.getUserName(), softwareId);
				File submissionFile = SubmissionFilesStore.createSubmissionFile(vm, s, runId, sc);
				String command = String.format(CommandLineExecutor.CMD_TIRA_RUN_EXECUTE, TIRA_HOST_USER, vm.getHost(),
						submissionFile.getName(), datasetId, inputRunDirPath, runId, TRUE_AS_STRING, taskId);
				CommandLineExecutor.executeSupervisedCommand(u.getUserName(), softwareId, command, runId, sc);
			}
		
		}

		redirectToTaskUserPage(req, resp, taskId, u.getUserName());
    }

	private void 
	postRoute12(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest12(req, resp)) return;
		Matcher m = PATTERN12.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = getServletContext();
		SoftwaresState.killRunningSoftwares(u, taskId, true, sc);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}

	private void 
	postRoute13(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest13(req, resp)) return;
		Matcher m = PATTERN13.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		
		String inputRun = req.getParameter(FORM_FIELD_RUN);
		
		User u = UsersStore.getUser(userName);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		
		synchronized (LOCK) {
			
			Checker c = new Checker();
			if (c.checkUserIdle(req, resp)) {
				ServletContext sc = getServletContext();
				
				Task t = TasksStore.getTask(taskId);
				String virtualMachineId = t.getVirtualMachineId();
				VirtualMachine taskVm = VirtualMachinesStore.getVirtualMachine(virtualMachineId);
				File inputRunDir = findRun(req, resp, taskId, inputRun);
				
				String datasetName = inputRunDir.getParentFile().getParentFile().getName();
				Dataset dataset = DatasetsStore.getDataset(taskId, datasetName);
				String evaluatorId = DatasetsStore.getEvaluatorId(taskId, datasetName);
				Evaluator e = SoftwaresStore.getEvaluator(t, evaluatorId);
				
				DateFormat df = new SimpleDateFormat(DATE_FORMAT_SORTABLE);
				String outputDirName = df.format(new Date());
				
				RunStore rs = RunsStore.getOrCreateRunStore(datasetName, outputDirName, u, true, sc);
				Run r = RunsStore.createRun(taskId, e.getEvaluatorId(), dataset, inputRun, outputDirName);
				rs.saveRun(r, sc);
				
				File submissionFile = SubmissionFilesStore.createEvaluatorSubmissionFile(vm, e, taskVm, r.getRunId(), sc);
				String command = String.format(CommandLineExecutor.CMD_TIRA_RUN_EVAL, TIRA_HOST_USER,
						taskVm.getHost(), submissionFile.getName(), datasetName,
						inputRunDir.getAbsolutePath(), outputDirName, taskId);
				CommandLineExecutor.executeSupervisedCommand(userName, e.getEvaluatorId(), command, r.getRunId(), sc);
			}
			
		}
		
		redirectToTaskUserPage(req, resp, taskId, userName);
	}
	
	private void 
	postRoute14(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest14(req, resp)) return;
		Matcher m = PATTERN14.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = getServletContext();
		SoftwaresState.killRunningSoftwares(u, taskId, false, sc);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}

	private void 
	getRoute15(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest15(req, resp)) return;
		Matcher m = PATTERN15.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		sendZippedRun(req, resp, taskId, userName, runId);
	}

	private void 
	postRoute16(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest16(req, resp)) return;
		Matcher m = PATTERN16.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		File run = findRun(req, resp, taskId, runId);
		RunsStore.deleteRun(run, taskId, runId, getServletContext());
		resp.setStatus(HttpServletResponse.SC_OK);
		redirectToTaskUserPage(req, resp, taskId, userName);
	}
	
	private void 
	getRoute17(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest17(req, resp)) return;
		Matcher m = PATTERN17.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		ServletContext sc = getServletContext();
		ExtendedRun er = collectExtendedRun(req, resp, taskId, runId, true, true, true, sc);
		
		Renderer.render(sc, req, resp, TEMPLATE_TASK_USER_RUN, er);
	}

	private void
	sendZippedRun(HttpServletRequest req, HttpServletResponse resp,
		String taskId, String userName, String runId)
	throws IOException, ServletException {
		File runDir = RunsStore.findRun(taskId, userName, runId);
		File tmpZip = File.createTempFile(FILE_PEFIX_RUN, FILE_TYPE_ZIP);
		tmpZip.delete();
		
		String command = String.format(CommandLineExecutor.CMD_ZIP_RECURSIVE,
				tmpZip.getAbsolutePath(), runDir.getName());
		ServletContext sc = getServletContext();
		CommandLineExecutor.executeCommand(command, runDir.getParentFile(), sc);
		
		resp.setContentType(HEADER_CONTENT_TYPE_APPLICATION_ZIP);
		resp.setHeader(HEADER_CONTENT_DISPOSITION, String.format(
				HEADER_CONTENT_DISPOSITION_ATTACHMENT, taskId, userName, runId));
		IOUtils.copy(FileUtils.openInputStream(tmpZip), resp.getOutputStream());
		resp.flushBuffer();
		
		tmpZip.delete();
	}

	private ExtendedRun
	collectExtendedRun(HttpServletRequest req, HttpServletResponse resp,
		String taskId, String runId, boolean filterTestDatasetOutput,
		boolean blindTestDatasetOutput, boolean readOutput, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		File runDir = findRun(req, resp, taskId, runId);
		return RunsState.collectExtendedRun(taskId, runDir,
				filterTestDatasetOutput, blindTestDatasetOutput, 
				readOutput, sc);
	}

	public static File 
	findRun(HttpServletRequest req, HttpServletResponse resp, String taskId,
			String runId)
	throws IOException, ServletException {
		Matcher m = PATTERN_USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		return RunsStore.findRun(taskId, u.getUserName(), runId);
	}

	private void 
	redirectToTaskUserPage(HttpServletRequest req, HttpServletResponse resp,
			String taskId, String userName) {
		resp.setStatus(HttpServletResponse.SC_SEE_OTHER);
		String contextPath = Preprocessor.getContextPath(req);
    	String taskUrl = String.format(URL_PATH_TASK_USER, contextPath,
    			taskId, userName);
    	resp.setHeader(HEADER_LOCATION, taskUrl);
	}
	
	private void 
	saveSoftware(HttpServletRequest req, String taskId, String userName,
			String softwareId) 
	throws IOException, ServletException {
		String command = req.getParameter(FORM_FIELD_COMMAND);
		String workingDirectory = req.getParameter(FORM_FIELD_WORKING_DIRECTORY);
		String Dataset = req.getParameter(FORM_FIELD_DATASET);
		String run = req.getParameter(FORM_FIELD_RUN);
		String count = softwareId.replace(SOFTWARE, EMPTY);
		Software s = SoftwaresStore.createSoftware(softwareId, count, command,
				workingDirectory, Dataset, run);
		SoftwaresStore.saveSoftware(taskId, userName, s);
	}
	
	private boolean
	checkRequest1(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest1b(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		// TODO: Check dataset exists.
		return true;
	}
	
	private boolean
	checkRequest2(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest3(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		// TODO: Check rather if VM clone is running.
//		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest4(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkVmReady(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest5(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkVmNotRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest6(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest7(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest8(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsEmpty(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest9(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsSoftwareSet(req, resp)) return false;
		if (!c.checkFormFieldSoftwareCommandValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareWorkingDirValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareDatasetValid(req, resp)) return false;
		if (!c.checkFormFieldRunValid(req, resp)) return false;
		if (!c.checkFormFieldRunNotOnTestDataset(req, resp)) return false;
		if (!c.checkSoftwaresExists(req, resp)) return false;
		if (!c.checkSoftwareExists(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest10(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsSoftwareSet(req, resp)) return false;
		if (!c.checkFormFieldSoftwareCommandValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareWorkingDirValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareDatasetValid(req, resp)) return false;
		if (!c.checkFormFieldRunValid(req, resp)) return false;
		if (!c.checkSoftwaresExists(req, resp)) return false;
		if (!c.checkSoftwareExists(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest11(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsSoftwareSet(req, resp)) return false;
		if (!c.checkFormFieldSoftwareCommandValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareWorkingDirValid(req, resp)) return false;
		if (!c.checkFormFieldSoftwareDatasetValid(req, resp)) return false;
		if (!c.checkFormFieldRunValid(req, resp)) return false;
		if (!c.checkFormFieldRunNotOnTestDataset(req, resp)) return false;
		if (!c.checkSoftwaresExists(req, resp)) return false;
		if (!c.checkSoftwareExists(req, resp)) return false;
		if (!c.checkUserIdle(req, resp)) return false;
		if (!c.checkVmRunning(req, resp)) return false;
		if (!c.checkVmReady(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest12(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkUserBusy(req, resp)) return false;
		// TODO: Investigate whether other checks are necessary.
//		if (!c.checkVmRunning(req, resp)) return false;
//		if (!c.checkVmReady(req, resp)) return false;
		return true;
	}

	private boolean
	checkRequest13(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsEvaluationSet(req, resp)) return false;
		if (!c.checkFormFieldRunValid(req, resp)) return false;
		if (!c.checkUserIdle(req, resp)) return false;
		if (!c.checkMasterVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest14(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkUserBusy(req, resp)) return false;
		if (!c.checkMasterVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest15(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkRunExists(req, resp)) return false;
		if (!c.checkRunNotDeleted(req, resp)) return false;
		if (!c.checkRunDownloadable(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest16(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkRunExists(req, resp)) return false;
		if (!c.checkRunNotDeleted(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest17(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkDisraptorSecretKeyIsCorrect(req)) return false;
		if (!c.checkUserOrReviewerSignedIn(req, resp)) return false;
		if (!c.checkRunExists(req, resp)) return false;
		if (!c.checkRunNotDeleted(req, resp)) return false;
		return true;
	}
}
