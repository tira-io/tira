package de.webis.tira.client.web;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.Writer;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
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

import com.google.common.collect.Maps;
import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.DatasetRuns;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskDataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview.SoftwareRunning;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReviewUserRun;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReviewUser;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;
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

@WebServlet(AdminTaskServlet.ROUTE)
@SuppressWarnings("serial")
public class AdminTaskServlet extends HttpServlet {

	private static final Object 
		LOCK = new Object();

	public static final String
		ROUTE = "/tira/admin/task/*";

	private static final String	
		ROUTE1 = "^/(?<taskId>[a-zA-Z0-9-]+)/$",
		ROUTE2a = "^/(?<taskId>[a-zA-Z0-9-]+)/settings/$",
		ROUTE2 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/$",
		ROUTE3 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/vm-metrics/$",
		ROUTE4 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/vm-shutdown/$",
		ROUTE5 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/vm-start/$",
		ROUTE6 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/vm-stop/$",
		ROUTE7 = "^/(?<taskId>[a-zA-Z0-9-]+)/virtual-machine/vm-screenshot.png$",
		ROUTE8 = "^/(?<taskId>[a-zA-Z0-9-]+)/scorers/$",
		ROUTE9 = "^/(?<taskId>[a-zA-Z0-9-]+)/scorers/(?<softwareId>software\\d+)/save/$",
		ROUTE10 = "^/(?<taskId>[a-zA-Z0-9-]+)/scorers/(?<softwareId>software\\d+)/delete/$",
		ROUTE11 = "^/(?<taskId>[a-zA-Z0-9-]+)/scorers/(?<softwareId>software\\d+)/run/$",
		ROUTE12 = "^/(?<taskId>[a-zA-Z0-9-]+)/scorers/(?<softwareId>software\\d+)/kill/$",
		ROUTE18 = "^/(?<taskId>[a-zA-Z0-9-]+)/participants/$",
		ROUTE19 = "^/(?<taskId>[a-zA-Z0-9-]+)/participants/(?<userName>[a-zA-Z0-9-]+)/$",
    	ROUTE20a = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/$",
    	ROUTE20b = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/dataset/(?<datasetId>[a-zA-Z0-9-]+)/$",
		ROUTE20 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/view/$",
		ROUTE21 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/save/$",
		ROUTE22 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+).zip$",
		ROUTE23 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/publish/$",
		ROUTE24 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/unpublish/$",
		ROUTE25 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/blind/$",
		ROUTE26 = "^/(?<taskId>[a-zA-Z0-9-]+)/evaluations/user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)/unblind/$",
		ROUTE27 = "^/(?<taskId>[a-zA-Z0-9-]+)/runs/$",
		ROUTE28 = "^/(?<taskId>[a-zA-Z0-9-]+)/runs/dataset/(?<datasetId>[a-zA-Z0-9-]+)/$";
	
	private static final String
 		GROUP_NAME_TASK_ID = "taskId",
 		GROUP_NAME_USER_NAME = "userName",
 		GROUP_NAME_SOFTWARE_ID = "softwareId",
 		GROUP_NAME_DATASET_ID = "datasetId",
 		GROUP_NAME_RUN_ID = "runId";

	private static final Pattern
	    PATTERN1 = Pattern.compile(ROUTE1, Pattern.CASE_INSENSITIVE),
	    PATTERN2a = Pattern.compile(ROUTE2a, Pattern.CASE_INSENSITIVE),
   	    PATTERN2 = Pattern.compile(ROUTE2, Pattern.CASE_INSENSITIVE),
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
		PATTERN18 = Pattern.compile(ROUTE18, Pattern.CASE_INSENSITIVE),
		PATTERN19 = Pattern.compile(ROUTE19, Pattern.CASE_INSENSITIVE),
		PATTERN20 = Pattern.compile(ROUTE20, Pattern.CASE_INSENSITIVE),
		PATTERN20a = Pattern.compile(ROUTE20a, Pattern.CASE_INSENSITIVE),
		PATTERN20b = Pattern.compile(ROUTE20b, Pattern.CASE_INSENSITIVE),
		PATTERN21 = Pattern.compile(ROUTE21, Pattern.CASE_INSENSITIVE),
		PATTERN22 = Pattern.compile(ROUTE22, Pattern.CASE_INSENSITIVE),
		PATTERN23 = Pattern.compile(ROUTE23, Pattern.CASE_INSENSITIVE),
		PATTERN24 = Pattern.compile(ROUTE24, Pattern.CASE_INSENSITIVE),
		PATTERN25 = Pattern.compile(ROUTE25, Pattern.CASE_INSENSITIVE),
		PATTERN26 = Pattern.compile(ROUTE26, Pattern.CASE_INSENSITIVE),
		PATTERN27 = Pattern.compile(ROUTE27, Pattern.CASE_INSENSITIVE),
		PATTERN28 = Pattern.compile(ROUTE28, Pattern.CASE_INSENSITIVE);
	
	private static final String
		FORM_FIELD_COMMAND = "command",
		FORM_FIELD_WORKING_DIRECTORY = "workingDirectory",
		FORM_FIELD_DATASET = "dataset",
		FORM_FIELD_RUN = "run",
		FORM_FIELD_NO_ERRORS = "noErrors",
		FORM_FIELD_MISSING_OUTPUT = "missingOutput",
		FORM_FIELD_EXTRANEOUS_OUTPUT = "extraneousOutput",
		FORM_FIELD_INVALID_OUTPUT = "invalidOutput",
		FORM_FIELD_HAS_ERROR_OUTPUT = "hasErrorOutput",
		FORM_FIELD_OTHER_ERRORS = "otherErrors",
		FORM_FIELD_COMMENT = "comment";
	
	private static final String 
		TEMPLATE_ADMIN_TASK = "/templates/tira-admin-task.mustache",
		TEMPLATE_ADMIN_TASK_VIRTUAL_MACHINE = "/templates/tira-admin-task-virtual-machine.mustache",
		TEMPLATE_ADMIN_TASK_PARTICIPANTS = "/templates/tira-admin-task-participants.mustache",
		TEMPLATE_ADMIN_TASK_EVALUATIONS = "/templates/tira-admin-task-evaluations.mustache",
		TEMPLATE_ADMIN_TASK_EVALUATIONS_DATASET = "/templates/tira-admin-task-evaluations-dataset.mustache",
		TEMPLATE_ADMIN_TASK_REVIEW_USER = "/templates/tira-admin-task-participants-user.mustache",
		TEMPLATE_ADMIN_TASK_REVIEW_USER_RUN = "/templates/tira-admin-task-participants-user-run.mustache",
		TEMPLATE_ADMIN_TASK_RUNS = "/templates/tira-admin-task-runs.mustache",
		TEMPLATE_ADMIN_TASK_RUNS_DATASET = "/templates/tira-admin-task-runs-dataset.mustache";
	
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
		URL_PATH_ADMIN_TASK_VIRTUAL_MACHINE = "%s/tira/admin/task/%s/virtual-machine/",
		URL_PATH_TASK_REVIEW_USER = "%s/tira/admin/task/%s/participants/%s/",
		URL_PATH_ADMIN_TASK_EVALUATIONS = "%s/tira/admin/task/%s/evaluations/",
		TRUE_AS_STRING = "\"true\"",
		ON = "on";
		
	private static final String
		EMPTY = "";

	@Override
	protected void 
	doGet(HttpServletRequest req, HttpServletResponse resp)
	throws ServletException, IOException {
		try {
			String path = req.getPathInfo();
			if (path.matches(ROUTE1)) getRoute1(req, resp);
			else if (path.matches(ROUTE2)) getRoute2(req, resp);
			else if (path.matches(ROUTE3)) getRoute3(req, resp);
			else if (path.matches(ROUTE7)) getRoute7(req, resp);
			else if (path.matches(ROUTE18))	getRoute18(req, resp);
			else if (path.matches(ROUTE19)) getRoute19(req, resp);
			else if (path.matches(ROUTE20)) getRoute20(req, resp);
			else if (path.matches(ROUTE20a)) getRoute20a(req, resp);
			else if (path.matches(ROUTE20b)) getRoute20b(req, resp);
			else if (path.matches(ROUTE22)) getRoute22(req, resp);
			else if (path.matches(ROUTE27)) getRoute27(req, resp);
			else if (path.matches(ROUTE28)) getRoute28(req, resp);
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
			else if (path.matches(ROUTE21)) postRoute21(req, resp);
			else if (path.matches(ROUTE23)) postRoute23(req, resp);
			else if (path.matches(ROUTE24)) postRoute24(req, resp);
			else if (path.matches(ROUTE25)) postRoute25(req, resp);
			else if (path.matches(ROUTE26)) postRoute26(req, resp);
		} catch (ExecutionException e) {
			throw new ServletException(e);
		}
	}

	private void 
	getRoute1(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest1(req, resp)) return;
		Matcher m = PATTERN1.matcher(req.getPathInfo());
		m.find();
		
		String taskId = m.group(GROUP_NAME_TASK_ID);
		Task t = TasksStore.getTask(taskId);
		
		ServletContext sc = getServletContext();
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK, t);
	}
	
	private void 
	getRoute2(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest2(req, resp)) return;
		Matcher m = PATTERN2.matcher(req.getPathInfo());
		m.find();
		
		String taskId = m.group(GROUP_NAME_TASK_ID);
		Task t = TasksStore.getTask(taskId);
		User u = getTaskVirtualMachineUser(taskId);
		TaskUser tu = null;
		if (t.hasVirtualMachineId()) {
			ServletContext sc = getServletContext();
			tu = TasksState.collectTaskUser(taskId, u, true, sc);
		}
		
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
			@SuppressWarnings("unused")
			public boolean isVirtualMachines = true;
		};
		
		ServletContext sc = getServletContext();
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_VIRTUAL_MACHINE, t, tu, admin);
	}

	private void 
	getRoute3(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest3(req, resp)) return;
		Matcher m = PATTERN3.matcher(req.getPathInfo());
		m.find();
		
		String taskId = m.group(GROUP_NAME_TASK_ID);
		User u = getTaskVirtualMachineUser(taskId);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		
		VirtualMachineState.Builder vmsb = VirtualMachineState.newBuilder();
		ServletContext sc = getServletContext();
		VirtualMachinesState.collectSupervisorState(vmsb, u.getUserName(), sc);
		Run r = RunsStore.readRunFromRunDir(taskId,
			RunsStore.findRun(taskId, u.getUserName(), vmsb.getProcessRunId()),
			sc);
		String metrics = ""; 
		if (r != null) {
			Dataset d = DatasetsStore.getDataset(taskId, r.getInputDataset());
			if (d.getIsConfidential()) {
				metrics = "hidden\nhidden";
			} 
			else {
				metrics = VirtualMachinesState.collectVirtualMachineMetrics(vmsb, vm, sc);
			}
		}

		Writer w = resp.getWriter();
		w.write(metrics);
		w.flush();
		w.close();
	}

	private User
	getTaskVirtualMachineUser(String taskId)
	throws IOException, ServletException {
		Task t = TasksStore.getTask(taskId);
		// TODO: Separate task master user ID from VM ID.
		return UsersStore.getUser(t.getVirtualMachineId());
	}

	private void 
	postRoute4(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest4(req, resp)) return;
		Matcher m = PATTERN4.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		User u = getTaskVirtualMachineUser(taskId);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraShutdown(u, taskId, sc);
		redirectToTaskUserPage(req, resp, taskId);
	}
	
	private void 
	postRoute5(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest5(req, resp)) return;
		Matcher m = PATTERN5.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		User u = getTaskVirtualMachineUser(taskId);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraVmStartStop(u, taskId, false, sc);
		redirectToTaskUserPage(req, resp, taskId);
	}
	
	private void 
	postRoute6(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest6(req, resp)) return;
		Matcher m = PATTERN6.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		User u = getTaskVirtualMachineUser(taskId);
		ServletContext sc = getServletContext();
		VirtualMachinesState.runTiraVmStartStop(u, taskId, true, sc);
		redirectToTaskUserPage(req, resp, taskId);
	}

	private void 
	getRoute7(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest7(req, resp)) return;
		Matcher m = PATTERN7.matcher(req.getPathInfo());
		m.find();
		
		User u = Authenticator.signedInUser(req);
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
//		redirectToTaskUserPage(req, resp, task, userName);
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
//		redirectToTaskUserPage(req, resp, taskId, userName);
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
//		redirectToTaskUserPage(req, resp, task, userName);
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

		User u = Authenticator.signedInUser(req);
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

//		redirectToTaskUserPage(req, resp, taskId, u.getUserName());
    }

	private void 
	postRoute12(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest12(req, resp)) return;
		Matcher m = PATTERN12.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		User u = Authenticator.signedInUser(req);
		ServletContext sc = getServletContext();
		SoftwaresState.killRunningSoftwares(u, taskId, true, sc);
//		redirectToTaskUserPage(req, resp, taskId, userName);
	}

	private void 
	getRoute18(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest18(req, resp)) return;
		Matcher m = PATTERN18.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		
		Task t = TasksStore.getTask(taskId);
		ServletContext sc = getServletContext();
		TaskReview tr = TasksState.collectTaskReviewTaskUsers(t, false, false, sc, req);
		
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
			@SuppressWarnings("unused")
			public boolean isParticipants= true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_PARTICIPANTS, tr, t, admin);
	}
	
	private void 
	getRoute19(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest19(req, resp)) return;
		Matcher m = PATTERN19.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		
		Task t = TasksStore.getTask(taskId);
		User u = UsersStore.getUser(userName);
		
		TaskUser.Builder tub = TaskUser.newBuilder();
		TasksState.collectSoftwareInfo(taskId, userName, tub);
		ServletContext sc = getServletContext();		
		RunsState.collectUserRuns(taskId, tub, u, false, sc);
		
		Map<String, SoftwareRunning.Builder> runningSoftwares = 
				SoftwaresState.collectRunningSoftwares(sc);
		SoftwareRunning.Builder runningSoftware = runningSoftwares.get(userName);
		
		Map<String, List<ExtendedRun.Builder>> runIndex = Maps.newTreeMap();
		for (ExtendedRun.Builder erb : tub.getRunsBuilderList()) {
			if (runningSoftware != null && 
				erb.getRun().getRunId().equals(runningSoftware.getRunId())) {
				erb.setIsRunning(true);
			}
			else {
				erb.setIsRunning(false);
			}
			
			String inputDataset = erb.getRun().getInputDataset();
			if (!runIndex.containsKey(inputDataset)) {
				runIndex.put(inputDataset, new ArrayList<ExtendedRun.Builder>());
			}
			runIndex.get(inputDataset).add(erb);
		}
		
		TaskReviewUser.Builder trub = TaskReviewUser.newBuilder();
		trub.setUser(u);
		trub.setTask(t);
		for (Entry<String, List<ExtendedRun.Builder>> e : runIndex.entrySet()) {
			Dataset d = DatasetsStore.getDataset(taskId, e.getKey());
			DatasetRuns.Builder drb = trub.addUserDatasetRunsBuilder();
			drb.setDataset(e.getKey());
			drb.setDatasetDeprecated(d.getIsDeprecated());
			for (ExtendedRun.Builder erb : e.getValue()) {
				drb.addRuns(erb);
			}
		}
		TaskReviewUser tru = trub.build();
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_REVIEW_USER, t, tru);
	}
	
	private void 
	getRoute20(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest20(req, resp)) return;
		Matcher m = PATTERN20.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		Task t = TasksStore.getTask(taskId);
		
		ServletContext sc = getServletContext();
		TaskReviewUserRun.Builder trurb = TaskReviewUserRun.newBuilder();
		trurb.setUser(u);
		trurb.setTask(t);
		ExtendedRun er = RunsState.collectExtendedRun(taskId, userName, runId, false, false, true, sc);
		if (er != null) trurb.setRun(er);
		TaskReviewUserRun trur = trurb.build();
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_REVIEW_USER_RUN, t, trur);
	}

	private void 
	getRoute20a(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest20a(req, resp)) return;
		Matcher m = PATTERN20a.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		
		ServletContext sc = getServletContext();
		Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t);
		
		// TODO: Move this to model.
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
			@SuppressWarnings("unused")
			public boolean isEvaluations = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_EVALUATIONS, t, td, admin);
	}

	private void 
	getRoute20b(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest20b(req, resp)) return;
		Matcher m = PATTERN20b.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String datasetId = m.group(GROUP_NAME_DATASET_ID);
		
		ServletContext sc = getServletContext();
		Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t, datasetId);
		TaskReview tr = TasksState.collectTaskReviewEvaluatorRuns(t, datasetId, false, false, sc, req);
		String evaluatorId = DatasetsStore.getEvaluatorId(taskId, datasetId);
		Evaluator e = SoftwaresStore.getEvaluator(t, evaluatorId);
		
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
			@SuppressWarnings("unused")
			public boolean isEvaluations = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_EVALUATIONS_DATASET, t, e, td, tr, admin);
	}

	private void 
	postRoute21(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest21(req, resp)) return;
		Matcher m = PATTERN21.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		
		Boolean noErrors = parameterValueChecked(req, FORM_FIELD_NO_ERRORS);
		Boolean missingOutput = parameterValueChecked(req, FORM_FIELD_MISSING_OUTPUT);
		Boolean extraneousOutput = parameterValueChecked(req, FORM_FIELD_EXTRANEOUS_OUTPUT);
		Boolean invalidOutput = parameterValueChecked(req, FORM_FIELD_INVALID_OUTPUT);
		Boolean hasErrorOutput = parameterValueChecked(req, FORM_FIELD_HAS_ERROR_OUTPUT);
		Boolean otherErrors = parameterValueChecked(req, FORM_FIELD_OTHER_ERRORS);
		String comment = req.getParameter(FORM_FIELD_COMMENT);
		
		RunsStore.updateRunReview(taskId, userName, u.getUserName(), runId, noErrors,
				missingOutput, extraneousOutput, invalidOutput, hasErrorOutput,
				otherErrors, comment, getServletContext());
		redirectToTaskReviewUserPage(req, resp, taskId, userName);
    }
	
	private Boolean
	parameterValueChecked(HttpServletRequest req, String parameter) {
		String parameterValue = req.getParameter(parameter);
		if (parameterValue != null) {
			return parameterValue.equals(ON);
		}
		return null;
	}
	
	private void 
	getRoute22(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!checkRequest22(req, resp)) return;
		Matcher m = PATTERN22.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		sendZippedRun(req, resp, taskId, userName, runId);
	}
	
	private void 
	postRoute23(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest23(req, resp)) return;
		Matcher m = PATTERN23.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		
		RunsStore.updateRunReview(taskId, userName, u.getUserName(), runId, true, null, getServletContext());
		resp.setStatus(HttpServletResponse.SC_OK);
    }
	
	private void 
	postRoute24(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest24(req, resp)) return;
		Matcher m = PATTERN24.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		
		RunsStore.updateRunReview(taskId, userName, u.getUserName(), runId, false, null, getServletContext());
		resp.setStatus(HttpServletResponse.SC_OK);
    }

	private void 
	postRoute25(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest25(req, resp)) return;
		Matcher m = PATTERN25.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		
		RunsStore.updateRunReview(taskId, userName, u.getUserName(), runId, null, true, getServletContext());
		resp.setStatus(HttpServletResponse.SC_OK);
    }
	
	private void 
	postRoute26(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest26(req, resp)) return;
		Matcher m = PATTERN26.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		
		User u = Authenticator.signedInUser(req);
		
		RunsStore.updateRunReview(taskId, userName, u.getUserName(), runId, null, false, getServletContext());
		resp.setStatus(HttpServletResponse.SC_OK);
    }
	
	private void 
	getRoute27(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest27(req, resp)) return;
		Matcher m = PATTERN27.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		
		ServletContext sc = getServletContext();
		Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t);
		
		// TODO: Move this to model.
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_RUNS, t, td, admin);
	}

	private void 
	getRoute28(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException, ExecutionException {
		if (!checkRequest28(req, resp)) return;
		Matcher m = PATTERN28.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String datasetId = m.group(GROUP_NAME_DATASET_ID);
		
		ServletContext sc = getServletContext();
		Task t = TasksStore.getTask(taskId);
		TaskDataset td = TasksState.collectTaskDataset(t, datasetId);
		TaskReview tr = TasksState.collectTaskReviewAllRuns(t, datasetId, false, false, sc, req);
		
		Object admin = new Object() {
			@SuppressWarnings("unused")
			public boolean isAdmin = true;
		};
		
		Renderer.render(sc, req, resp, TEMPLATE_ADMIN_TASK_RUNS_DATASET, t, td, tr, admin);
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
	
//	public static ExtendedRun
//	collectExtendedRun(HttpServletRequest req, HttpServletResponse resp,
//		String taskId, String runId, boolean filterTestDatasetOutput,
//		boolean blindTestDatasetOutput, boolean readOutput, ServletContext sc)
//	throws IOException, ServletException, ExecutionException {
//		File runDir = findRun(req, resp, taskId, runId);
//		return RunsState.collectExtendedRun(taskId, runDir, filterTestDatasetOutput,
//				blindTestDatasetOutput, readOutput, sc);
//	}

	public static File 
	findRun(HttpServletRequest req, HttpServletResponse resp, String taskId,
			String runId)
	throws IOException, ServletException {
		User u = Authenticator.signedInUser(req);
		return RunsStore.findRun(taskId, u.getUserName(), runId);
	}

	private void 
	redirectToTaskUserPage(HttpServletRequest req, HttpServletResponse resp,
			String taskId) {
		resp.setStatus(HttpServletResponse.SC_SEE_OTHER);
		String contextPath = Preprocessor.getContextPath(req);
    	String taskUrl = String.format(URL_PATH_ADMIN_TASK_VIRTUAL_MACHINE,
    		contextPath, taskId);
    	resp.setHeader(HEADER_LOCATION, taskUrl);
	}
	
	private void 
	redirectToTaskReviewUserPage(HttpServletRequest req,
			HttpServletResponse resp, String taskId, String userName) {
		resp.setStatus(HttpServletResponse.SC_SEE_OTHER);
		String contextPath = Preprocessor.getContextPath(req);
    	String taskUrl = String.format(URL_PATH_TASK_REVIEW_USER, contextPath,
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
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		return true;
	}
	
	private boolean
	checkRequest2(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		return true;
	}
	
	private boolean
	checkRequest3(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
//		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest4(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		if (!c.checkVmReady(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest5(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		// TODO: Fix check to be relative to servlet.
//		if (!c.checkVmNotRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest6(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		// TODO: Fix check to be relative to servlet.
//		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest7(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: check if user is task admin
		// TODO: Fix check to be relative to servlet.
//		if (!c.checkVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest8(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkUserSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsEmpty(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest9(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkUserSignedIn(req, resp)) return false;
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
		if (!c.checkUserSignedIn(req, resp)) return false;
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
		if (!c.checkUserSignedIn(req, resp)) return false;
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
		if (!c.checkUserSignedIn(req, resp)) return false;
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
		if (!c.checkUserSignedIn(req, resp)) return false;
		if (!c.checkFormFieldsEvaluationSet(req, resp)) return false;
		if (!c.checkFormFieldRunValid(req, resp)) return false;
		if (!c.checkUserIdle(req, resp)) return false;
		if (!c.checkMasterVmRunning(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest18(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
	
	private boolean
	checkRequest19(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
	
	private boolean
	checkRequest20(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest20a(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
	
	private boolean
	checkRequest20b(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
	
	private boolean
	checkRequest21(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkPathEndsWithSlash(req, resp)) return false;
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
//		if (!c.checkFormFieldsRunReviewSet(req, resp)) return false;
//		if (!c.checkFormFieldRunReviewErrorsValid(req, resp)) return false;
//		if (!c.checkFormFieldRunReviewCommentValid(req, resp)) return false;
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest22(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest23(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest24(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest25(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
	
	private boolean
	checkRequest26(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		if (!c.checkRunExists(req, resp)) return false;
//		if (!c.checkRunFinished(req, resp)) return false;
		return true;
	}
		
	private boolean
	checkRequest27(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
	
	private boolean
	checkRequest28(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Checker c = Checker.getInstance();
		if (!c.checkTaskExists(req, resp)) return false;
		if (!c.checkReviewerSignedIn(req, resp)) return false;
		// TODO: Check that signed in user is task admin.
		return true;
	}
}
