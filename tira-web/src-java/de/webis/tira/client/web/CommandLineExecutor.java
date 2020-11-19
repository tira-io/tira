package de.webis.tira.client.web;

import java.io.File;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import org.apache.commons.io.FileExistsException;
import org.apache.commons.io.FileUtils;

import de.webis.tira.client.web.storage.Directories;

public class CommandLineExecutor {

	private static final String
		FILE_TYPE_CONF = ".conf",
		FILE_NAME_SUFFIX_STDERR_LOG = "-stderr.log",
		FILE_NAME_SUFFIX_STDOUT_LOG = "-stdout.log";

	private static final String
		TIRA_HOST_USER = "tira";
	
	public static final String
		CMD_TIRA_VM_INFO = "sudo -u %s -H tira vm-info -r %s %s",
		CMD_TIRA_VM_METRICS = "sudo -u %s -H tira vm-metrics -r %s %s",
		CMD_TIRA_VM_RUNTIME_OUTPUT = "sudo -u %s -H tira vm-runtime-output -r %s %s %s",
		CMD_TIRA_VM_SCREENSHOT = "sudo -u %s -H tira vm-screenshot -r %s %s",
		CMD_TIRA_VM_SHUTDOWN = "sudo -u %s -H tira vm-shutdown -r %s %s",
		CMD_TIRA_VM_START = "sudo -u %s -H tira vm-start -r %s %s",
		CMD_TIRA_VM_STOP = "sudo -u %s -H tira vm-stop -r %s %s",
		CMD_TIRA_VM_UNSANDBOX = "sudo -u %s -H tira vm-unsandbox -r %s %s",
	    CMD_TIRA_RUN_COPY_TO_LOCAL = "sudo -u %s -H tira run-copy-to-local -r %s %s %s %s %s %s %s %s",
		CMD_TIRA_RUN_EXECUTE = "sudo -u %s -H tira run-execute -r %s %s %s %s %s %s -T %s",
		CMD_TIRA_RUN_EVAL = "sudo -u %s -H tira run-eval -r %s %s %s %s %s -T %s",
		CMD_SUPERVISORCTL_START = "supervisorctl start %s",
		CMD_SUPERVISORCTL_UPDATE = "supervisorctl update",
		CMD_SUPERVISORCTL_STATUS = "supervisorctl status",
		CMD_SUPERVISORCTL_STOP = "supervisorctl stop %s",
		CMD_BASH = "bash",
		CMD_MKDIR = "mkdir -p -m 775 %s",
		CMD_MKDIR_AS_TIRA = "sudo -u tira -H mkdir -p -m 775 %s",
		CMD_NMAP_PORTSCAN = "nmap --max-rtt-timeout 100ms -p %s,%s -PN %s | grep open",
		CMD_TOUCH_AS_TIRA = "sudo -u tira -H touch %s",
		CMD_LIST_FILES = "ls -la %s",
		CMD_ZIP_RECURSIVE = "zip -r %s %s",
		CMD_PARAM_BASH_C = "-c";
	
	private static final String
		SUPERVISOR_CONF_PROGRAM = "[program:%s]\n",
		SUPERVISOR_CONF_COMMAND = "command=%s\n",
		SUPERVISOR_CONF_USER = "user=%s\n",
		SUPERVISOR_CONF_AUTOSTART_FALSE = "autostart=false\n",
		SUPERVISOR_CONF_AUTORESTART_FALSE = "autorestart=false\n",
		SUPERVISOR_CONF_STARTRETRIES_0 = "startretries=0\n",
		SUPERVISOR_CONF_STOPSIGNAL_KILL = "stopsignal=KILL\n",
		SUPERVISOR_CONF_STDERR_LOGFILE = "stderr_logfile=%s\n",
		SUPERVISOR_CONF_STDOUT_LOGFILE = "stdout_logfile=%s\n";

	private static final String 
		DATE_FORMAT_SORTABLE = "YYYY-MM-dd-HH-mm-ss";
	
	private static final String 
		DASH = "-";
	
	public static void 
	executeCommand(String command, ServletContext sc)
	throws IOException, ServletException {
		executeCommand(command, null, sc);
	}

	public static void 
	executeCommand(String command, File workingDir, ServletContext sc)
	throws IOException, ServletException {
		executeCommand(command, workingDir, new StringBuilder(), 
				new StringBuilder(), sc);
	}
	
	public static void
	executeSupervisedCommand(String user, String type, String command, String runId, ServletContext sc)
	throws IOException, ServletException {
		executeSupervisedCommand(user, type, command, null, runId, sc);
	}
	
	public static void
	executeSupervisedCommand(String user, String type, String command, 
			File workingDir, String runId, ServletContext sc)
	throws IOException, ServletException {
		File userConfDir = new File(Directories.SUPERVISOR_CONFS, user);
		if (!userConfDir.exists()) {
			String mkDirCommand = String.format(CMD_MKDIR,
					userConfDir.getAbsolutePath());
			executeCommand(mkDirCommand, sc);
		}
		
		File userLogDir = new File(Directories.SUPERVISOR_LOGS, user);
		if (!userLogDir.exists()) {
			String mkDirCommand = String.format(CMD_MKDIR,
					userLogDir.getAbsolutePath());
			executeCommand(mkDirCommand, sc);
		}
		
		// Clean the user's conf directory
		// TODO: Find a better way to clean the directory immediately after a
		// process is finished.
		for (File f : userConfDir.listFiles(new FilenameFilter() {
			
			@Override
			public boolean accept(File dir, String name) {
				return name.endsWith(FILE_TYPE_CONF);
			}
		})) {
			try {
				FileUtils.moveFile(f, new File(userLogDir, f.getName()));
			}
			catch (FileExistsException e) {
				// TODO: Make note of this incident in the event log.
				File dest = File.createTempFile(f.getName(), "", userLogDir);
				dest.delete();
				FileUtils.moveFile(f, dest);
			}
		}
		
		String fileName = user + DASH + type;
		if (runId != null) {
			fileName +=  DASH + runId;
		}
		else {
			DateFormat df = new SimpleDateFormat(DATE_FORMAT_SORTABLE);
			fileName += DASH + df.format(new Date());
		}
		
		File confFile = new File(userConfDir, fileName + FILE_TYPE_CONF);
		FileWriter writer = new FileWriter(confFile);
		writer.write(String.format(SUPERVISOR_CONF_PROGRAM, confFile.getName()));
		writer.write(String.format(SUPERVISOR_CONF_COMMAND, command));
		writer.write(String.format(SUPERVISOR_CONF_USER, TIRA_HOST_USER));
		writer.write(SUPERVISOR_CONF_AUTOSTART_FALSE);
		writer.write(SUPERVISOR_CONF_AUTORESTART_FALSE);
		writer.write(SUPERVISOR_CONF_STARTRETRIES_0);
		writer.write(SUPERVISOR_CONF_STOPSIGNAL_KILL);
		writer.write(String.format(SUPERVISOR_CONF_STDOUT_LOGFILE, 
			new File(userLogDir, fileName + FILE_NAME_SUFFIX_STDOUT_LOG)));
		writer.write(String.format(SUPERVISOR_CONF_STDERR_LOGFILE, 
			new File(userLogDir, fileName + FILE_NAME_SUFFIX_STDERR_LOG)));
		writer.flush();
		writer.close();
		
		// This ensures the NFS cache is up to date
		executeCommand(String.format(CMD_LIST_FILES, Directories.SUPERVISOR_CONFS), sc);
		executeCommand(CMD_SUPERVISORCTL_UPDATE, sc);
		executeCommand(String.format(CMD_SUPERVISORCTL_START, confFile.getName()), sc);
	}
	
	public static void 
	executeCommand(String command, File workingDir,	StringBuilder stdout,
			StringBuilder stderr, ServletContext sc)
	throws IOException, ServletException {
		Process p = Runtime.getRuntime().exec(command, null, workingDir);
		handleProcess(p, sc, stdout, stderr, true);
	}
	
	public static void 
	executeCommand(String[] cmdArray, File workingDir, StringBuilder stdout,
			StringBuilder stderr, boolean failOnExitCode1, ServletContext sc)
	throws IOException, ServletException {
		Process p = Runtime.getRuntime().exec(cmdArray, null, workingDir);
		handleProcess(p, sc, stdout, stderr, failOnExitCode1);
	}
	
	public static void 
	handleProcess(Process p, ServletContext sc, StringBuilder stdout,
			StringBuilder stderr, boolean failOnExitCode1)
					throws ServletException, IOException {
		Future<String> futureStdout = 
				BackgroundExecutor.dispatchStreamReader(sc, p.getInputStream()); 
		Future<String> futureStderr = 
				BackgroundExecutor.dispatchStreamReader(sc, p.getErrorStream());
		int exitValue;
		try {
			exitValue = p.waitFor();
		} 
		catch (InterruptedException e) {
			throw new ServletException(e);
		}
		try {
			stdout.append(futureStdout.get());
			stderr.append(futureStderr.get());
		} catch (InterruptedException e) {
			throw new ServletException(e);
		} catch (ExecutionException e) {
			throw new ServletException(e);
		}
		if (failOnExitCode1 && exitValue != 0) {
			throw new ServletException(
					"Error executing command:\nSTDOUT:" + stdout +
					"\n\nSTDERR:" + stderr);
		}
	}
	
}
