package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Date;
import java.util.List;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.CommandLineExecutor;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Evaluator;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares;
import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Softwares.Software;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Tasks.Task;

public class SoftwaresStore {

	public static final String
		FILE_NAME_SOFTWARES_PROTOTEXT = "softwares.prototext";
	
	private static final String
		SOFTWARE = "software";
	
	public static final String 
		EMPTY = "";
	
	private static Software
	createSoftware(String id, String count) {
		return createSoftware(id, count, EMPTY, EMPTY, EMPTY, EMPTY);
	}

	public static Software 
	createSoftware(String id, String count, String command, String workingDirectory,
			String dataset, String run) {
		Software.Builder sb = Software.newBuilder();
		sb.setId(id);
		sb.setCount(count);
		sb.setCommand(command);
		sb.setWorkingDirectory(workingDirectory);
		sb.setDataset(dataset);
		sb.setRun(run);
		sb.setDeleted(false);
		String date = new Date().toString();
		sb.setCreationDate(date);
		sb.setLastEditDate(date);
		return sb.build();
	}

	private static File
	getSoftwaresPrototext(String task, String userName)
	throws IOException, ServletException {
		return getOrCreateSoftwaresPrototext(task, userName, null, false);
	}
	
	private static File
	getOrCreateSoftwaresPrototext(
		String task, String userName, ServletContext sc, boolean create)
	throws IOException, ServletException {
		File softwareDir = new File(Directories.SOFTWARES_MODEL, task);
		File userDir = new File(softwareDir, userName);
		if (create && !userDir.exists() && sc != null) {
			String command = String.format(CommandLineExecutor.CMD_MKDIR_AS_TIRA,
					userDir.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		File softwares = new File(userDir, FILE_NAME_SOFTWARES_PROTOTEXT);
		if (create && !softwares.exists() && sc != null) {
			String command = String.format(CommandLineExecutor.CMD_TOUCH_AS_TIRA, 
					softwares.getAbsolutePath());
			CommandLineExecutor.executeCommand(command, sc);
		}
		return softwares;
	}
	
	public static Software
	findSoftware(String taskId, String userName, String softwareId)
	throws IOException, ServletException {
		Softwares softwares = readSoftwares(taskId, userName, false);
		for (Software s : softwares.getSoftwaresList()) {
			if (s.getId().equals(softwareId)) {
				return s;
			}
		}
		return null;
	}
	
	public static void
	addSoftware(String task, String userName, ServletContext sc)
	throws IOException, ServletException {
		Softwares.Builder sb = 
				Softwares.newBuilder(readSoftwares(task, userName, true));
		String count = Integer.toString(sb.getSoftwaresCount() + 1);
		String id = SOFTWARE + count;
		Software s = createSoftware(id, count);
		sb.addSoftwaresBuilder().mergeFrom(s);
		File softwares = getOrCreateSoftwaresPrototext(task, userName, sc, true);
		saveSoftwares(sb.build(), softwares);
	}

	public static void
	saveSoftware(String task, String userName, Software s)
	throws IOException, ServletException {
		Softwares.Builder sb = 
				Softwares.newBuilder(readSoftwares(task, userName, true));
		for (Software.Builder sb2 : sb.getSoftwaresBuilderList()) {
			if (sb2.getId().equals(s.getId())) {
				sb2.mergeFrom(s);
				sb2.setLastEditDate(new Date().toString());
				break;
			}
		}
		File softwares = getSoftwaresPrototext(task, userName);
		saveSoftwares(sb.build(), softwares);
	}

	private static void 
	saveSoftwares(Softwares s, File softwares)
	throws IOException {
		FileWriter writer = new FileWriter(softwares);
		TextFormat.print(s, writer);
		writer.close();
	}
	
	public static void 
	deleteSoftware(String task, String userName, String softwareId)
	throws IOException, ServletException {
		Softwares.Builder sb = 
				Softwares.newBuilder(readSoftwares(task, userName, true));
		for (Software.Builder sb2 : sb.getSoftwaresBuilderList()) {
			if (sb2.getId().equals(softwareId)) {
				sb2.setDeleted(true);
				sb2.setLastEditDate(new Date().toString());
				break;
			}
		}
		File softwares = getSoftwaresPrototext(task, userName);
		saveSoftwares(sb.build(), softwares);
	}
	
	public static Softwares
	readSoftwares(String task, String userName)
	throws IOException, ServletException {
		return readSoftwares(task, userName, false);
	}

	public static Softwares
	readSoftwares(String task, String userName, boolean create)
	throws IOException, ServletException {
		File softwares = getSoftwaresPrototext(task, userName);
		if (!softwares.exists()) return Softwares.newBuilder().build();
		return readSoftwares(softwares);
	}

	private static Softwares
	readSoftwares(File softwares)
	throws IOException {
		Softwares.Builder sb = Softwares.newBuilder();
		if (softwares.exists()) {
			String encoding = Charsets.UTF_8.name();
			String prototext;
			prototext = FileUtils.readFileToString(softwares, encoding);
			TextFormat.merge(prototext, sb);
		}
		Softwares s = sb.build();
		return s;
	}

	public static Evaluator
	getEvaluator(Task t, String evaluatorId)
	throws IOException {
		String virtualMachineId = t.getVirtualMachineId();
		VirtualMachine vm = VirtualMachinesStore.getVirtualMachine(virtualMachineId);
		List<Evaluator> evaluators = vm.getEvaluatorsList();
		for (Evaluator evaluator : evaluators) {
			if (evaluator.getEvaluatorId().equals(evaluatorId)) {
				return evaluator;
			}
		}
		return null;
	}
}
