package de.webis.tira.client.web.state;

import java.io.File;
import java.io.IOException;
import java.util.Set;
import java.util.concurrent.ExecutionException;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import scala.actors.threadpool.Arrays;

import com.google.common.base.Joiner;
import com.google.common.collect.Sets;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Run;
import de.webis.tira.client.web.generated.TiraClientWebMessages.TaskUser;
import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachineState2;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.storage.DatasetsStore;
import de.webis.tira.client.web.storage.Directories;
import de.webis.tira.client.web.storage.RunsStore;
import de.webis.tira.client.web.storage.SoftwaresStore;
import de.webis.tira.client.web.storage.VirtualMachinesStore;

public class VirtualMachinesState {
	
	private static final String
		TIRA_HOST_USER = "tira";
	
	private static final String 
		VM_INFO_GUEST_OS = "Guest OS:",
		VM_INFO_MEMORY_SIZE = "Memory size:",
		VM_INFO_NUMBER_OF_CP_US = "Number of CPUs:",
		VM_INFO_STATE = "State:",
		VM_INFO_STATE_RUNNING = "running",
		VM_INFO_STATE_REGEX = "(\\d\\d)T(\\d\\d?)",
		VM_INFO_STATE_REGEX_REPLACEMENT = "$1 $2",
		VM_INFO_STATE_SINCE_REGEX = "\\.\\d+\\)",
		VM_INFO_STATE_SINCE_REPLACEMENT = ")",
		VM_INFO_SPLIT_REGEX = ": ",
		VM_INFO_NO_SUCH_FILE_OR_DIRECTORY = "No such file or directory",
		VM_INFO_CONNECTION_TO = "Connection to",
		VM_INFO_CLOSED = "closed.",
		VM_INFO_LATEST_OUTPUT_BEGIN = "Latest output begin:",
		VM_INFO_VM_IS_NOT_RUNNING = "VM is not running!";

	private static final String
		FILE_TYPE_SANDBOXED = ".sandboxed",
		FILE_TYPE_SANDBOXING = ".sandboxing",
		FILE_TYPE_UNSANDBOXING = ".unsandboxing";
	
	private static final String
		EVALUATOR = "evaluator",
		NONE = "none",
		UNKNOWN = "unknown",
		CLONE = "clone",
		PROCESS_NAME_SHUTDOWN_VM = "shutdownVm",
		PROCESS_NAME_STOP_VM = "stopVm",
		PROCESS_NAME_START_VM = "startVm";
	
	private static final String 
		CMD_OUT_NMAP_OUTPUT_PORT_OPEN = "%s/tcp open",
		SPLIT_REGEX_SUPERVISOR_PROCESS_UPTIME = "uptime ",
		SPLIT_REGEX_SUPERVISOR_PROCESS_NAMES = "(.conf\\s+|\\s\\s+)",
		REGEX_WHITESPACES = "\\s+",
		ABBREV_MEGABYTE = "MB";
	
	private static final String 
		NEWLINE = "\n",
		TILDE = "~",
		DASH = "-";
	
	private static final char
		CH_DASH = '-';
	
	public static final Set<String>
		PROCESS_STATES = 
			Sets.newHashSet("STARTING", "RUNNING", "BACKOFF", "STOPPING");
	
	public static void 
	collectVmInfo(VirtualMachineState.Builder vmsb, String taskId, User u,
		ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		String virtualMachineId = u.getVirtualMachineId();
		String userName = u.getUserName();
		VirtualMachine vm = 
				VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		vmsb.setHost(vm.getHost());
		vmsb.setPortSsh(vm.getPortSsh());
		vmsb.setPortRdp(vm.getPortRdp());
		
		// The order of calling these methods may is important.
		collectTiraVmInfoState(vmsb, virtualMachineId, sc);
		collectNmapPortState(vmsb, virtualMachineId, sc);
		collectTiraSandboxState(vmsb, virtualMachineId, sc);
		collectSupervisorState(vmsb, userName, sc);
		collectOngoingRun(vmsb, taskId, userName, sc);
		collectOngoingRunsLatestOutput(vmsb, vm, taskId, u, sc);
	}

	private static void
	collectTiraVmInfoState(VirtualMachineState.Builder vmsb,
		String virtualMachineId, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = 
			VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		String command = String.format(CommandLineExecutor.CMD_TIRA_VM_INFO, 
			TIRA_HOST_USER, vm.getHost(), vm.getVmName());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(command, null, stdout, 
			new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		for (String line : lines) {
			if (line.startsWith(VM_INFO_GUEST_OS)) {
				vmsb.setGuestOs(line.split(VM_INFO_SPLIT_REGEX)[1].trim());
			}
			else if (line.startsWith(VM_INFO_MEMORY_SIZE)) {
				vmsb.setMemorySize(line.split(VM_INFO_SPLIT_REGEX)[1].trim());
			} else if(line.startsWith("Memory size")) {
				//probably a bug in new versions of virtualbox
				//Example line: "Memory size                  4096MB"
				vmsb.setMemorySize(line.split("size")[1].trim());
			}
			else if (line.startsWith(VM_INFO_NUMBER_OF_CP_US)) {
				vmsb.setNumberOfCpus(line.split(VM_INFO_SPLIT_REGEX)[1].trim());
			}
			else if (line.startsWith(VM_INFO_STATE)) {
				vmsb.setState(line.split(VM_INFO_SPLIT_REGEX)[1].trim()
				   .replaceFirst(VM_INFO_STATE_REGEX, 
						   		 VM_INFO_STATE_REGEX_REPLACEMENT)
				   .replaceFirst(VM_INFO_STATE_SINCE_REGEX, 
						   		 VM_INFO_STATE_SINCE_REPLACEMENT));
			}
		}
		if (!vmsb.hasGuestOs()) vmsb.setGuestOs(UNKNOWN);
		if (!vmsb.hasMemorySize()) vmsb.setMemorySize(UNKNOWN);
		if (!vmsb.hasNumberOfCpus()) vmsb.setNumberOfCpus(UNKNOWN);
		if (!vmsb.hasState()) vmsb.setState(UNKNOWN);
		vmsb.setStateRunning(vmsb.getState().startsWith(VM_INFO_STATE_RUNNING));
	}

	private static void
	collectNmapPortState(VirtualMachineState.Builder vmsb,
		String virtualMachineId, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = 
				VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		vmsb.setPortSshOpen(false);
		vmsb.setPortRdpOpen(false);
		String command = String.format(CommandLineExecutor.CMD_NMAP_PORTSCAN,
				vm.getPortSsh(), vm.getPortRdp(), vm.getHost());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(new String[] {
			CommandLineExecutor.CMD_BASH, CommandLineExecutor.CMD_PARAM_BASH_C,
			command
		}, null, stdout, new StringBuilder(), false, sc);
		String[] lines = stdout.toString().split(NEWLINE);
		String portSshOpen = 
				String.format(CMD_OUT_NMAP_OUTPUT_PORT_OPEN, vm.getPortSsh());
		String portRdpOpen = 
				String.format(CMD_OUT_NMAP_OUTPUT_PORT_OPEN, vm.getPortRdp());
		for (String line : lines) {
			if (line.startsWith(portSshOpen)) {
				vmsb.setPortSshOpen(true);
			}
			else if (line.startsWith(portRdpOpen)) {
				vmsb.setPortRdpOpen(true);
			}
		}
	}

	private static void
	collectTiraSandboxState(VirtualMachineState.Builder vmsb,
		String virtualMachineId, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm =
			VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		// This ensures the NFS cache is up to date
		CommandLineExecutor.executeCommand(String.format(
			CommandLineExecutor.CMD_LIST_FILES,
			Directories.VIRTUAL_MACHINES_STATE.getAbsolutePath()), sc);
		File sandboxed = new File(Directories.VIRTUAL_MACHINES_STATE,
			TILDE + vm.getVmName() + FILE_TYPE_SANDBOXED);
		File sandboxing = new File(Directories.VIRTUAL_MACHINES_STATE,
			TILDE + vm.getVmName() + FILE_TYPE_SANDBOXING);
		File unsandboxing = new File(Directories.VIRTUAL_MACHINES_STATE,
			TILDE + vm.getVmName() + FILE_TYPE_UNSANDBOXING);
		vmsb.setStateSandboxed(sandboxed.exists());
		vmsb.setStateSandboxing(sandboxing.exists());
		vmsb.setStateUnsandboxing(unsandboxing.exists());
	}

	public static void
	collectSupervisorState(VirtualMachineState.Builder vmsb, String userName,
			ServletContext sc)
	throws IOException, ServletException {
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(
			CommandLineExecutor.CMD_SUPERVISORCTL_STATUS, null, stdout,
			new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		for (String line : lines) {
			if (!line.startsWith(userName + "-")) continue;
			String[] fields = line.split(SPLIT_REGEX_SUPERVISOR_PROCESS_NAMES);
			if (fields.length > 1 && PROCESS_STATES.contains(fields[1])) {
				String[] fields2 = fields[0].split(DASH);
				String type = UNKNOWN; 
				if (fields2.length > 7) {
					type = fields2[fields2.length - 7];
				}
				vmsb.setProcessRunning(
					!type.equals(PROCESS_NAME_START_VM) && 
					!type.equals(PROCESS_NAME_STOP_VM) && 
					!type.equals(PROCESS_NAME_SHUTDOWN_VM));
				vmsb.setProcessType(type);
				String runId = UNKNOWN;
				if (fields2.length > 7) {
					runId = Joiner.on(CH_DASH).join(Arrays.copyOfRange(
						fields2, fields2.length - 6, fields2.length));
				}
				vmsb.setProcessRunId(runId);
				vmsb.setProcessState(fields[1].toLowerCase());
				if (fields.length > 2) {
					String[] time = 
						fields[2].split(SPLIT_REGEX_SUPERVISOR_PROCESS_UPTIME);
					vmsb.setProcessTime(time.length > 1 ? time[1] : UNKNOWN);
				}
				else {
					vmsb.setProcessTime(UNKNOWN);
				}
				vmsb.setVmBooting(type.equals(PROCESS_NAME_START_VM));
				vmsb.setVmPoweringOff(type.equals(PROCESS_NAME_STOP_VM));
				vmsb.setVmShuttingDown(type.equals(PROCESS_NAME_SHUTDOWN_VM));
				break;
			}
		}
		if (!vmsb.getProcessRunning() && 
			!vmsb.getVmBooting() && 
			!vmsb.getVmPoweringOff() && 
			!vmsb.getVmShuttingDown()) {
			vmsb.setProcessRunning(false);
			vmsb.setProcessType(NONE);
			vmsb.setProcessRunId(NONE);
			vmsb.setProcessState(NONE);
			vmsb.setProcessTime(NONE);
			vmsb.setVmBooting(false);
			vmsb.setVmPoweringOff(false);
			vmsb.setVmShuttingDown(false);
		}
	}

	private static void
	collectOngoingRun(VirtualMachineState.Builder vmsb, String taskId,
		String userName, ServletContext sc)
	throws IOException, ExecutionException, ServletException {
		String runId = vmsb.getProcessRunId();
		if (!NONE.equals(runId)) {
			File runDir = RunsStore.findRun(userName, runId);
			if (runDir != null) {
				Run r = RunsStore.readRunFromRunDir(taskId, runDir, sc);
				vmsb.setRun(r);
				String softwareId = vmsb.getProcessType();
				if (!softwareId.startsWith(EVALUATOR)) {
					Software s = SoftwaresStore.findSoftware(taskId, userName,
						softwareId);
					// TODO: This should not be possible.
					if (s != null) {
						vmsb.setSoftware(s);
					}
				}
			}
		}
	}

	private static void 
	collectOngoingRunsLatestOutput(VirtualMachineState.Builder vmsb,
		VirtualMachine vm, String taskId, User u, ServletContext sc)
	throws IOException, ServletException, ExecutionException {
		vmsb.setHasLatestOutput(false);
		
		if (!vmsb.getProcessRunning() || 
			vmsb.getStateSandboxing() ||
			vmsb.getStateUnsandboxing()) {
			return;
		}
		Run r = RunsStore.readRunFromRunDir(taskId,
			RunsStore.findRun(taskId, u.getUserName(), vmsb.getProcessRunId()),
			sc);
		if (r != null) {
			Dataset d = DatasetsStore.getDataset(taskId, r.getInputDataset());
			if (d.getIsConfidential()) {
				return;
			}
		}
		
		String command = String.format(
			CommandLineExecutor.CMD_TIRA_VM_RUNTIME_OUTPUT, TIRA_HOST_USER,
			vm.getHost(), vm.getVmName(), vmsb.getProcessRunId());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(command, null, stdout,
			new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		stdout.delete(0, stdout.length());
		boolean recordOutput = false;
		for (String line : lines) {
			line = line.trim();
			if (line.endsWith(VM_INFO_LATEST_OUTPUT_BEGIN)) {
				recordOutput = true;
				continue;
			}
			if (line.startsWith(VM_INFO_CONNECTION_TO) &&
				line.endsWith(VM_INFO_CLOSED)) {
				recordOutput = false;
				break;
			}
			if (recordOutput) {
				if (line.endsWith(VM_INFO_NO_SUCH_FILE_OR_DIRECTORY)) {
					break;
				}
				stdout.append(line).append(NEWLINE);
			}
		}
		if (stdout.length() > 0) {
			vmsb.setLatestOutput(stdout.toString());
			vmsb.setHasLatestOutput(true);
		}
	}
	
	public static String
	collectVirtualMachineMetrics(VirtualMachineState.Builder vmsb, VirtualMachine vm,
		ServletContext sc)
	throws IOException, ServletException {
		String vmName = vm.getVmName();
		if (vmsb.getProcessRunning()) {
			String runId = vmsb.getProcessRunId();
			vmName += DASH + CLONE + DASH + runId;
		}
		String metrics = "";
		String command = String.format(CommandLineExecutor.CMD_TIRA_VM_METRICS,
			TIRA_HOST_USER, vm.getHost(), vmName);
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(command, null, stdout,
			new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		String lastLine = lines[lines.length - 1].trim();
		if (lines.length > 2 && !lastLine.endsWith(VM_INFO_VM_IS_NOT_RUNNING)) {
			String cpuLoadLine = lines[lines.length - 3];
			String ramTotalLine = lines[lines.length - 2];
			String ramFreeLine = lines[lines.length - 1];
			String[] fields = cpuLoadLine.split(REGEX_WHITESPACES);
			if (fields.length > 2) {
				String cpuLoad = cpuLoadLine.split(REGEX_WHITESPACES)[2];
				int totalRam = 
					Integer.parseInt(ramTotalLine.split(REGEX_WHITESPACES)[2]);
				int freeRam = 
					Integer.parseInt(ramFreeLine.split(REGEX_WHITESPACES)[2]);
				int usedRam = (totalRam - freeRam)/1024;
				StringBuilder sb = new StringBuilder(); 
				sb.append(cpuLoad).append(NEWLINE);
				sb.append(Integer.toString(usedRam)).append(ABBREV_MEGABYTE);
				metrics = sb.toString();
			}
		}
		return metrics;
	}
	
	public static void
	runTiraShutdown(User u, String taskId, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		String command = String.format(CommandLineExecutor.CMD_TIRA_VM_SHUTDOWN, TIRA_HOST_USER, vm.getHost(), vm.getUserName());
		CommandLineExecutor.executeSupervisedCommand(vm.getUserName(), PROCESS_NAME_SHUTDOWN_VM, command, null, sc);
	}
	
	public static void 
	runTiraVmStartStop(User u, String taskId, boolean stopVm, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		String format = stopVm ? CommandLineExecutor.CMD_TIRA_VM_STOP : CommandLineExecutor.CMD_TIRA_VM_START;
		String command = String.format(format, TIRA_HOST_USER, vm.getHost(), vm.getVmName());
		CommandLineExecutor.executeSupervisedCommand(vm.getUserName(), stopVm ? PROCESS_NAME_STOP_VM : PROCESS_NAME_START_VM, command, null, sc);
	}
	
	public static void
	collectMasterInfo(TaskUser.Builder tub, ServletContext sc)
	throws IOException, ServletException {
		String virtualMachineId = tub.getTask().getVirtualMachineId();
		VirtualMachine taskVm = VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		VirtualMachineState2.Builder vmsb = tub.getTaskVmInfoBuilder();
		vmsb.setTaskVm(taskVm);
		vmsb.setPortSshOpen(false);
		vmsb.setPortRdpOpen(false);
		String command = String.format(
				CommandLineExecutor.CMD_NMAP_PORTSCAN, 
				taskVm.getPortSsh(), taskVm.getPortRdp(), taskVm.getHost());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(new String[] {CommandLineExecutor.CMD_BASH, CommandLineExecutor.CMD_PARAM_BASH_C, command}, null, stdout, new StringBuilder(), false, sc);
		String[] lines = stdout.toString().split(NEWLINE);
		String portSshOpen = String.format(CMD_OUT_NMAP_OUTPUT_PORT_OPEN, taskVm.getPortSsh());
		String portRdpOpen = String.format(CMD_OUT_NMAP_OUTPUT_PORT_OPEN, taskVm.getPortRdp());
		for (String line : lines) {
			if (line.startsWith(portSshOpen)) {
				vmsb.setPortSshOpen(true);
			}
			else if (line.startsWith(portRdpOpen)) {
				vmsb.setPortRdpOpen(true);
			}
		}
	}
	
	public static boolean
	checkVmRunning(User u, ServletContext sc)
	throws IOException, ServletException {
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(u.getVirtualMachineId());
		String command = String.format(CommandLineExecutor.CMD_TIRA_VM_INFO, TIRA_HOST_USER, vm.getHost(), vm.getVmName());
		StringBuilder stdout = new StringBuilder();
		CommandLineExecutor.executeCommand(command, null, stdout, new StringBuilder(), sc);
		String[] lines = stdout.toString().split(NEWLINE);
		String state = null;
		for (String line : lines) {
			if (line.startsWith(VM_INFO_STATE)) {
				state = line.split(VM_INFO_SPLIT_REGEX)[1].trim();
			}
		}
		if (state == null || !state.startsWith(VM_INFO_STATE_RUNNING)) {
			return false;
		}
		return true;
	}
}
