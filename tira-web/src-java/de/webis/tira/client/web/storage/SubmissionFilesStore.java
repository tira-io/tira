package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;

public class SubmissionFilesStore {

	private static final String
		SUBMISSION_FILE_USER = "user=\"%s\"\n",
		SUBMISSION_FILE_OS = "os=\"%s\"\n",
		SUBMISSION_FILE_HOST = "host=\"%s\"\n",
		SUBMISSION_FILE_SSHPORT = "sshport=\"%s\"\n",
		SUBMISSION_FILE_USERPW = "userpw=\"%s\"\n",
		SUBMISSION_FILE_WORKING_DIR = "workingDir=\"%s\"\n",
		SUBMISSION_FILE_CMD = "cmd=\"%s\"\n";
	
	public static final String
		FILE_PREFIX_SUBMISSION = "submission-",
		FILE_TYPE_TXT = ".txt";
	
	private static final String
		WINDOWS = "windows",
		UBUNTU = "ubuntu",
		FEDORA = "fedora";
	
	public static final String 
		DASH = "-";
	
	public static File 
	createEvaluatorSubmissionFile(VirtualMachine vm, Evaluator evaluator,
			VirtualMachine taskVm, String runId, ServletContext sc) 
	throws IOException, ServletException {
		return createSubmissionFile(vm.getUserName(), taskVm.getUserName(),
				taskVm.getVmName(), taskVm.getHost(), taskVm.getPortSsh(),
				taskVm.getUserPw(), evaluator.getWorkingDirectory(),
				evaluator.getCommand(), runId, sc);
	}
	
	public static File 
	createSubmissionFile(VirtualMachine vm, Software s, String runId,
			ServletContext sc) 
	throws IOException, ServletException {
		return createSubmissionFile(vm.getUserName(), vm.getUserName(),
				vm.getVmName(), vm.getHost(), vm.getPortSsh(), vm.getUserPw(),
				s.getWorkingDirectory(), s.getCommand(), runId, sc);
	}
	
	private static File
	createSubmissionFile(String tiraUser, String vmUser, String os, String host,
			String sshport,	String userpw, String workingDir, String cmd,
			String runId, ServletContext sc)
	throws IOException, ServletException {
		File softwaresDir = new File(Directories.SOFTWARES_STATE, tiraUser);
		if (!softwaresDir.exists()) {
			String command = String.format(CommandLineExecutor.CMD_MKDIR_AS_TIRA,
					softwaresDir.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		File submissionFile = new File(softwaresDir, tiraUser + DASH + 
				FILE_PREFIX_SUBMISSION + runId + FILE_TYPE_TXT);
		String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
				submissionFile.getAbsolutePath());
		CommandLineExecutor.executeCommand(command, sc);
		
		FileWriter writer = new FileWriter(submissionFile, true);
		writer.write(String.format(SUBMISSION_FILE_USER, vmUser));
		writer.write(String.format(SUBMISSION_FILE_OS,
			os.contains(UBUNTU) ? UBUNTU : os.contains(FEDORA) ? FEDORA : WINDOWS));
		writer.write(String.format(SUBMISSION_FILE_HOST, host));
		writer.write(String.format(SUBMISSION_FILE_SSHPORT, sshport));
		writer.write(String.format(SUBMISSION_FILE_USERPW, userpw));
		writer.write(String.format(SUBMISSION_FILE_WORKING_DIR, workingDir));
		writer.write(String.format(SUBMISSION_FILE_CMD, cmd));
		writer.flush();
		writer.close();
		return submissionFile;
	}
	
}
