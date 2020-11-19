package de.webis.tira.client.web.state;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Map;
import java.util.Set;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import com.google.common.base.Joiner;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskReview.SoftwareRunning;
import de.webis.tira.client.web.storage.RunsStore;
import de.webis.tira.client.web.storage.VirtualMachinesStore;

public class SoftwaresState {

	private static final String
		UNKNOWN = "unknown";
	
	private static final String
		TIRA_HOST_USER = "tira";
	
	private static final String
		FILE_TYPE_CONF = ".conf";
	
	private static final String 
		SPLIT_REGEX_SUPERVISOR_PROCESS_UPTIME = "uptime ",
		SPLIT_REGEX_SUPERVISOR_PROCESS_NAMES = "(.conf\\s+|\\s\\s+)";
	
	private static final String
		SOFTWARE = "software",
		WINDOWS = "windows",
		UBUNTU = "ubuntu",
		FEDORA = "fedora";
	
	private static final String 
		NEWLINE = "\n",
		DASH = "-";
	
	private static final char
		CH_DASH = '-';
	
	private static final Set<String>
		PROCESS_STATES = 
			Sets.newHashSet("STARTING", "RUNNING", "BACKOFF", "STOPPING");
	
	public static Map<String, SoftwareRunning.Builder>
	collectRunningSoftwares(ServletContext sc)
	throws IOException, ServletException {
		Map<String, SoftwareRunning.Builder> runningSoftwares = Maps.newHashMap(); 
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(CommandLineExecutor.CMD_SUPERVISORCTL_STATUS, null, stdout, new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		for (String line : lines) {
			String[] fields = line.split(SPLIT_REGEX_SUPERVISOR_PROCESS_NAMES);
			if (fields.length > 1 && PROCESS_STATES.contains(fields[1])) {
				SoftwareRunning.Builder srb = SoftwareRunning.newBuilder(); 
				String[] fields2 = fields[0].split(DASH);
				String userName = fields2[0];
				runningSoftwares.put(userName, srb);
				String type = fields2.length > 1 ? fields2[1] : UNKNOWN;
				srb.setType(type);
				String runId = fields2.length > 7 ? Joiner.on(CH_DASH).join(Arrays.copyOfRange(fields2, fields2.length - 6, fields2.length)) : UNKNOWN;
				srb.setRunId(runId);
				if (fields.length > 2) {
					String[] time = fields[2].split(SPLIT_REGEX_SUPERVISOR_PROCESS_UPTIME);
					srb.setTime(time.length > 1 ? time[1] : UNKNOWN);
				}
				else {
					srb.setTime(UNKNOWN);
				}
			}
		}
		return runningSoftwares;
	}
	
	public static void
	killRunningSoftwares(User u, String taskId, boolean unsandboxVm,
			ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(CommandLineExecutor.CMD_SUPERVISORCTL_STATUS, null, stdout, new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		for (String line : lines) {
			if (!line.startsWith(vm.getUserName())) continue;
			String[] fields = line.split(SPLIT_REGEX_SUPERVISOR_PROCESS_NAMES);
			if (fields.length > 1 && PROCESS_STATES.contains(fields[1])) {
				String name = fields[0] + FILE_TYPE_CONF;
				
				if (name.contains(SOFTWARE)) {
					String runId = extractRunName(name);
					File run = RunsStore.findRun(taskId, u.getUserName(), runId);
					String inputDatasetName = run.getParentFile().getParentFile().getName(); 
					String vmName = vm.getVmName();
					String os = vmName.contains(UBUNTU) ? UBUNTU : vmName.contains(FEDORA) ? FEDORA : WINDOWS;
					String command = String.format(CommandLineExecutor.CMD_TIRA_RUN_COPY_TO_LOCAL,
						TIRA_HOST_USER, vm.getHost(), runId, inputDatasetName,
						vm.getUserName(), vm.getUserPw(), vm.getHost(),
						vm.getPortSsh(), os);
					CommandLineExecutor.executeCommand(command, sc);
				}
				// TODO: Secure the evaluator run, too, if it gets killed.
				
				String command = String.format(CommandLineExecutor.CMD_SUPERVISORCTL_STOP, name);
				CommandLineExecutor.executeCommand(command, sc);
				if (unsandboxVm) {
					command = String.format(CommandLineExecutor.CMD_TIRA_VM_UNSANDBOX, TIRA_HOST_USER, u.getHost(), u.getVmName());
					CommandLineExecutor.executeCommand(command, sc);
				}
			}
		}
	}

	public static Set<String>
	getRunningProcessesRunNames(ServletContext sc)
	throws IOException, ServletException {
		Set<String> runningProcessesRunNames = Sets.newHashSet();
		String command = CommandLineExecutor.CMD_SUPERVISORCTL_STATUS;
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(command, null, stdout, new StringBuilder(), sc);
		for (String line : stdout.toString().split("\n")) {
			String[] fields = line.split("\\s+");
			if (fields.length > 2 && PROCESS_STATES.contains(fields[1])) {
				runningProcessesRunNames.add(extractRunName(fields[0]));
			}
		}
		return runningProcessesRunNames;
	}
	
	public static String
	extractRunName(String processName) {
		String[] fields = processName.split("\\.");
		if (fields.length > 1) {
			fields = fields[0].split("-");
			if (fields.length > 5) {
				return Joiner.on('-').join(Arrays.copyOfRange(fields, fields.length - 6, fields.length));
			}
		}
		return "unknown";
	}
}
