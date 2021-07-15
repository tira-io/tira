package de.webis.tira.client.web.request;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.concurrent.ExecutionException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.common.collect.Sets;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.TaskServlet;
import de.webis.tira.client.web.authentication.Authenticator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.state.VirtualMachinesState;
import de.webis.tira.client.web.storage.Directories;
import de.webis.tira.client.web.storage.RunsStore;
import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.TasksStore;
import de.webis.tira.client.web.storage.UsersStore;
import de.webis.tira.client.web.storage.VirtualMachinesStore;

public class Checker {
	
	private static final Pattern 
		TASK_ID_PATHS = Pattern.compile("^/(?<taskId>[a-zA-Z0-9-]+)/.*$"),
		USER_ID_PATHS = Pattern.compile("^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/.*$"),
		SOFTWARE_ID_PATHS = Pattern.compile("^/(?<taskId>[a-zA-Z0-9-]+)/user/(?<userName>[a-zA-Z0-9-]+)/software/(?<softwareId>software\\d+)/.*$"),
		RUN_ID_PATHS = Pattern.compile("^/(?<taskId>[a-zA-Z0-9-]+)/(evaluations/)?user/(?<userName>[a-zA-Z0-9-]+)/run/(?<runId>[a-zA-Z0-9-]+)(\\.|/).*$"),
		CMD_REGEX = Pattern.compile("^[\\p{Alnum}-\\_ \\$\\./]+$"),
		DIR_REGEX = Pattern.compile("^[/\\p{Alnum}-\\_\\.]+$"),
		DATASET_REGEX = Pattern.compile("^[\\p{Alnum}-]+$"),
		RUN_REGEX = Pattern.compile("^[\\p{Alnum}-]+$");

	public static final String
		GROUP_NAME_TASK_ID = "taskId",
		GROUP_NAME_USER_NAME = "userName",
		GROUP_NAME_SOFTWARE_ID = "softwareId",
		GROUP_NAME_RUN_ID = "runId";

	private static final String
		FORM_FIELD_COMMAND = "command",
		FORM_FIELD_WORKING_DIRECTORY = "workingDirectory",
		FORM_FIELD_DATASET = "dataset",
		FORM_FIELD_RUN = "run",
		FORM_FIELD_ACTION = "action";
	
	private static final String
		FILE_NAME_RUN_PROTOTEXT = "run.prototext",
		FILE_NAME_SOFTWARES_PROTOTEXT = "softwares.prototext";
	
	private final String DISRAPTOR_APP_SECRET_KEY;
	
	private static Checker INSTANCE = null;
	
	public static Checker getInstance() {
		if (INSTANCE == null) {
			INSTANCE = new Checker();
		}
		return INSTANCE;
	}
	
	public Checker() {
//        ClassLoader loader = Checker.class.getClassLoader();
    DISRAPTOR_APP_SECRET_KEY = System.getenv("DISRAPTOR_APP_SECRET_KEY");
	}
	
	public boolean 
	checkPathIsEmpty(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		String contextPath = req.getContextPath();
		String uri = req.getRequestURI();
		if (!uri.equals(contextPath + "/")) {
			int sc = HttpServletResponse.SC_NOT_FOUND;
			String error = "Resource not found.";
			resp.sendError(sc, error);
			return false;
		}
		return true;
	}
	
	public boolean 
	checkPathEndsWithSlash(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		String path = req.getPathInfo();
		if (path != null && !path.endsWith("/")) {
			resp.sendRedirect(req.getRequestURI() + "/");
			return false;
		}
		return true;
	}

	public boolean 
	checkTaskExists(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Matcher m = TASK_ID_PATHS.matcher(req.getPathInfo());
		if (!m.find()) {
			respondBadRequest(resp, "Task id invalid.");
			return false;
		}
		String taskId = m.group(GROUP_NAME_TASK_ID);
		if (TasksStore.getTask(taskId) == null) {
			respondNotFound(resp, "Task does not exist.");
			return false;
		}
		return true;
	}
	
	/**
	 * Checks if the incoming request has the Disraptor secret key header.
	 * If so, it checks whether the incoming secret key matches the stored secret key.
	 * 
	 * @param req the incoming request
	 * @return whether the incoming secret key is correct
	 */
	public boolean
	checkDisraptorSecretKeyIsCorrect(HttpServletRequest req) {
		String incomingSecretKey = req.getHeader("x-disraptor-app-secret-key");
		return incomingSecretKey != null && incomingSecretKey.equals(DISRAPTOR_APP_SECRET_KEY);
	}

	public boolean
	checkUserSignedIn(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		if (!m.find()) {
			respondBadRequest(resp, "User name invalid.");
			return false;
		}
		
		if (!Authenticator.isSignedIn(req)) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = Authenticator.signedInUser(req);
		if (!u.getUserName().equals(userName)) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		return true;
	}
	
	public boolean
	checkUserOrReviewerSignedIn(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		if (!m.find()) {
			respondBadRequest(resp, "User name invalid.");
			return false;
		}
		
		if (!Authenticator.isSignedIn(req)) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		String userName = m.group(GROUP_NAME_USER_NAME);
		User tiraUser = Authenticator.signedInUser(req);
		
		if (!tiraUser.getUserName().equals(userName) && !tiraUser.getRolesList().contains("reviewer")) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		return true;
	}
	
	public boolean
	checkReviewerSignedIn(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		if (!Authenticator.isSignedIn(req)) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		User tiraUser = Authenticator.signedInUser(req);
		
		if (tiraUser.getRolesCount() == 0 || !tiraUser.getRolesList().contains("reviewer")) {
			respondUnauthorized(resp, "Not authorized.");
			return false;
		}
		
		return true;
	}
	
	public boolean
	checkVmRunning(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = req.getServletContext();
		if (!VirtualMachinesState.checkVmRunning(u, sc)) {
			respondConflict(resp, "VM not running.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkVmNotRunning(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		ServletContext sc = req.getServletContext();
		if (VirtualMachinesState.checkVmRunning(u, sc)) {
			respondConflict(resp, "VM already running.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkVmReady(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		// TODO: This should check whether the VM is ready for execution.
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		String command = String.format("nmap --max-rtt-timeout 100ms -p %s -PN %s | grep open",
				vm.getPortSsh(), vm.getHost());
		StringBuilder stdout = new StringBuilder();
		StringBuilder stderr = new StringBuilder();
		ServletContext sc = req.getServletContext();
		CommandLineExecutor.executeCommand(new String[] {"bash", "-c", command}, null, stdout, stderr, false, sc);
		if (stderr.length() > 0) {
			respondInternalServerError(resp, "Could not stat VM.");
			return false;
		}
		String expected = String.format("%s/tcp open", vm.getPortSsh());
		if (stdout.length() == 0 || !stdout.toString().startsWith(expected)) {
			respondConflict(resp, "VM not accessible via SSH.");
			return false;
		}
		return true;
	}
	
	public boolean
	checkMasterVmRunning(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = TASK_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		Task t = TasksStore.getTask(taskId);
		String virtualMachineId = t.getVirtualMachineId();
		VirtualMachine master = VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		String command = String.format("nmap --max-rtt-timeout 100ms -p %s -PN %s | grep open",
				master.getPortSsh(), master.getHost());
		StringBuilder stdout = new StringBuilder();
		StringBuilder stderr = new StringBuilder();
		ServletContext sc = req.getServletContext();
		CommandLineExecutor.executeCommand(new String[] {"bash", "-c", command}, null, stdout, stderr, false, sc);
		if (stderr.length() > 0) {
			respondInternalServerError(resp, "Could not stat master VM.");
			return false;
		}
		String expected = String.format("%s/tcp open", master.getPortSsh());
		if (stdout.length() == 0 || !stdout.toString().startsWith(expected)) {
			respondConflict(resp, "Master VM not running.");
			return false;
		}
		return true;
	}
	
	public boolean
	checkFormFieldsEmpty(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Map<String, String[]> parameters = req.getParameterMap();
		if (parameters.size() != 0) {
			respondBadRequest(resp, "Wrong number of parameters.");
			return false;
		}
		return true;
	}
	
	public boolean
	checkFormFieldsSoftwareSet(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		Map<String, String[]> parameters = req.getParameterMap();
		if (parameters.size() != 4) {
			respondBadRequest(resp, "Wrong number of parameters.");
			return false;
		}
		if (!(parameters.containsKey(FORM_FIELD_COMMAND) ||
			  parameters.containsKey(FORM_FIELD_WORKING_DIRECTORY) ||
			  parameters.containsKey(FORM_FIELD_DATASET) ||
			  parameters.containsKey(FORM_FIELD_RUN))) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		String[] cmd = parameters.get(FORM_FIELD_COMMAND); 
		String[] dir = parameters.get(FORM_FIELD_WORKING_DIRECTORY);
		String[] dataset = parameters.get(FORM_FIELD_DATASET);
		String[] run = parameters.get(FORM_FIELD_RUN);
		if (cmd.length != 1 || dir.length != 1 || dataset.length != 1 ||
			run.length != 1) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		return true;
	}

	public boolean 
	checkFormFieldSoftwareCommandValid(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		String cmd = req.getParameter(FORM_FIELD_COMMAND);
		if (cmd != null && cmd.length() > 0 && !CMD_REGEX.matcher(cmd).find()) {
			respondBadRequest(resp, "Commands can only contain alphanumeric chars, spaces, dashes, dots, underscores, and the dollar sign.");
			return false;
		}
		return true;
	}

	public boolean 
	checkFormFieldSoftwareWorkingDirValid(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		String dir = req.getParameter(FORM_FIELD_WORKING_DIRECTORY);
		if (dir != null && dir.length() > 0 && !DIR_REGEX.matcher(dir).find()) {
			respondBadRequest(resp, "Paths are restricted to Unix-style paths consisting of slash-separated alphanumeric character sequences.");
			return false;
		}
		return true;
	}
	
	public boolean
	checkFormFieldSoftwareDatasetValid(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		String dataset = req.getParameter(FORM_FIELD_DATASET);
		if (dataset.trim().isEmpty()) {
			respondBadRequest(resp, "Dataset variable empty.");
			return false;
		}
		if (!DATASET_REGEX.matcher(dataset).find()) {
			respondBadRequest(resp, "Dataset names can only consist of alpahnumeric chars and the dash sign:" + dataset);
			return false;
		}
		Matcher m = TASK_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		Task t = TasksStore.getTask(taskId);
		Set<String> datasets = Sets.newHashSet();
		datasets.addAll(t.getTrainingDatasetList());
		datasets.addAll(t.getTestDatasetList());
		if (!datasets.contains(dataset)) {
			respondNotFound(resp, "Requested evaluation dataset not found.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkFormFieldSoftwareActionValid(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		String action = req.getParameter(FORM_FIELD_ACTION);
		Set<String> actions = Sets.newHashSet("add", "save", "delete", "run"); 
		if (actions.contains(action)) {
			respondBadRequest(resp, "Unrecognized action.");
			return false;
		}
		return true;
	}

	public boolean 
	checkFormFieldsRunSet(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Map<String, String[]> parameters = req.getParameterMap();
		if (parameters.size() != 1) {
			respondBadRequest(resp, "Wrong number of parameters.");
			return false;
		}
		if (!parameters.containsKey(FORM_FIELD_DATASET)) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		String[] dataset = parameters.get(FORM_FIELD_DATASET);
		if (dataset.length != 1) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkSoftwaresExists(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		File softwaresDir = new File(Directories.SOFTWARES_MODEL, taskId);
		File userDir = new File(softwaresDir, userName);
		File softwares = new File(userDir, FILE_NAME_SOFTWARES_PROTOTEXT);
		if (!softwares.exists()) {
			respondConflict(resp, "No softwares specified.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkSoftwareExists(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = SOFTWARE_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String softwareId = m.group(GROUP_NAME_SOFTWARE_ID);
		Softwares s = SoftwaresStore.readSoftwares(taskId, userName);
		for (Software s2 : s.getSoftwaresList()) {
			if (!s2.getDeleted() && s2.getId().equals(softwareId)) {
				return true;
			}
		}
		respondNotFound(resp, "Software not found.");
		return false;
	}
	
	public boolean
	checkUserIdle(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		String command = String.format("supervisorctl status | grep \"^%s-\"",
				u.getUserName());
		StringBuilder stdout = new StringBuilder();
		StringBuilder stderr = new StringBuilder();
		ServletContext sc = req.getServletContext();
		CommandLineExecutor.executeCommand(new String[] {"bash", "-c", command}, null, stdout, stderr, false, sc);
		if (stderr.length() > 0) {
			respondInternalServerError(resp, "Could not stat user's processes.");
			return false;
		}
		if (stdout.length() > 0) {
			Set<String> processes = Sets.newHashSet(stdout.toString().split("\\s"));
			Set<String> states = Sets.newHashSet("STARTING", "RUNNING", "BACKOFF",
					"STOPPING");
			if (Sets.intersection(processes, states).size() > 0) {
				respondConflict(resp, "User is already running a process.");
				return false;
			}
		}
		return true;
	}
	
	public boolean 
	checkUserBusy(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ServletException {
		Matcher m = USER_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String userName = m.group(GROUP_NAME_USER_NAME);
		User u = UsersStore.getUser(userName);
		String command = String.format("supervisorctl status | grep %s",
				u.getUserName());
		StringBuilder stdout = new StringBuilder();
		StringBuilder stderr = new StringBuilder();
		ServletContext sc = req.getServletContext();
		CommandLineExecutor.executeCommand(new String[] {"bash", "-c", command}, null, stdout, stderr, true, sc);
		if (stderr.length() > 0) {
			respondInternalServerError(resp, "Could not stat user's processes.");
			return false;
		}
		Set<String> processes = Sets.newHashSet(stdout.toString().split("\\s"));
		Set<String> states = Sets.newHashSet("STARTING", "RUNNING", "BACKOFF",
				"STOPPING");
		if (Sets.intersection(processes, states).isEmpty()) {
			respondConflict(resp, "User is not running a process.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkRunExists(HttpServletRequest req, HttpServletResponse resp)
	throws IOException {
		Matcher m = RUN_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String userName = m.group(GROUP_NAME_USER_NAME);
		String runId = m.group(GROUP_NAME_RUN_ID);
		if (RunsStore.findRun(taskId, userName, runId) == null) {
			respondNotFound(resp, "Run not found.");
			return false;
		}
		return true;
	}

	public boolean 
	checkRunNotDeleted(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Matcher m = RUN_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String runId = m.group(GROUP_NAME_RUN_ID);
		File runDir = TaskServlet.findRun(req, resp, taskId, runId);
		File runPrototext = new File(runDir, FILE_NAME_RUN_PROTOTEXT);
		Run run = RunsStore.readRun(runPrototext, req.getServletContext());
		if (run.getDeleted()) {
			respondNotFound(resp, "Run not found.");
			return false;
		}
		return true;
	}

	public boolean 
	checkRunDownloadable(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Matcher m = RUN_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String runId = m.group(GROUP_NAME_RUN_ID);
		File runDir = TaskServlet.findRun(req, resp, taskId, runId);
		File runPrototext = new File(runDir, FILE_NAME_RUN_PROTOTEXT);
		Run run = RunsStore.readRun(runPrototext, req.getServletContext());
		if (!run.getDownloadable()) {
			respondNotFound(resp, "Run not found.");
			return false;
		}
		return true;
	}
	
	public boolean 
	checkFormFieldsEvaluationSet(HttpServletRequest req,
			HttpServletResponse resp)
	throws IOException {
		Map<String, String[]> parameters = req.getParameterMap();
		if (parameters.size() != 1) {
			respondBadRequest(resp, "Wrong number of parameters.");
			return false;
		}
		if (!(parameters.containsKey(FORM_FIELD_RUN))) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		String[] run = parameters.get(FORM_FIELD_RUN);
		if (run.length != 1) {
			respondBadRequest(resp, "Wrong set of parameters.");
			return false;
		}
		return true;
	}

	public boolean
	checkFormFieldRunValid(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		String runId = req.getParameter(FORM_FIELD_RUN);
		if ("none".equals(runId)) {
			return true;
		}
		if (!RUN_REGEX.matcher(runId).find()) {
			respondBadRequest(resp, "Run names can only consist of alpahnumeric chars and the dash sign.");
			return false;
		}
		Matcher m = TASK_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		File runDir = TaskServlet.findRun(req, resp, taskId, runId);
		if (runDir == null) {
			respondNotFound(resp, "Run not found.");
			return false;
		}
		Run r = RunsStore.readRun(new File(runDir, FILE_NAME_RUN_PROTOTEXT), req.getServletContext()); 
		if (r.getDeleted()) {
			respondNotFound(resp, "Run not found.");
			return false;
		}
		return true;
	}
	
	public boolean
	checkFormFieldRunNotOnTestDataset(HttpServletRequest req, HttpServletResponse resp)
	throws IOException, ExecutionException, ServletException {
		Matcher m = TASK_ID_PATHS.matcher(req.getPathInfo());
		m.find();
		String taskId = m.group(GROUP_NAME_TASK_ID);
		String runId = req.getParameter(FORM_FIELD_RUN);
		if ("none".equals(runId)) {
			return true;
		}
		File runDir = TaskServlet.findRun(req, resp, taskId, runId);
		Run r = RunsStore.readRun(new File(runDir, FILE_NAME_RUN_PROTOTEXT), req.getServletContext()); 
		if (r.getInputDataset().contains("test-dataset")) {
			respondConflict(resp, "Run cannot be used as input.");
			return false;
		}
		return true;
	}

	/*public boolean
	checkRdpConfigForm(HttpServletRequest req, HttpServletResponse resp)
		throws IOException {
		String resolution = (String) req.getSession().getAttribute("resolution");
		String depth = (String) req.getSession().getAttribute("depth");
		String layout = (String) req.getSession().getAttribute("layout");
		String res[] = resolution.split("x");
		// valid parameters

	}*/
	
	private void 
	respondConflict(HttpServletResponse resp, String message)
	throws IOException {
		resp.sendError(HttpServletResponse.SC_CONFLICT, message);
	}
	
	private void 
	respondInternalServerError(HttpServletResponse resp, String message)
	throws IOException {
		resp.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, message);
	}
	
	private void respondUnauthorized(HttpServletResponse resp, String message)
	throws IOException {
		resp.sendError(HttpServletResponse.SC_UNAUTHORIZED, message);
	}
	
	private void respondNotFound(HttpServletResponse resp, String message)
	throws IOException {
		resp.sendError(HttpServletResponse.SC_NOT_FOUND, message);
	}
	
	private void respondBadRequest(HttpServletResponse resp, String message)
	throws IOException {
		resp.sendError(HttpServletResponse.SC_BAD_REQUEST, message);
	}

}
