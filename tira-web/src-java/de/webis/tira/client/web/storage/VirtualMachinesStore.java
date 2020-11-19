package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.generated.TiraClientWebMessages.VirtualMachine;

public class VirtualMachinesStore {
	
	private static final Charset
		UTF8 = Charsets.UTF_8;
	
	public static VirtualMachine 
	getVirtualMachine(String virtualMachineId)
	throws IOException {
		if (virtualMachineId == null || virtualMachineId.isEmpty()) {
			throw new IOException("Virtual machine ID not specified.");
		}
		File virtualMachinesDir = Directories.VIRTUAL_MACHINES_MODEL;
		String virtualMachinePrototextName = virtualMachineId + ".prototext";
		File virtualMachinePrototext = new File(virtualMachinesDir, virtualMachinePrototextName);
		if (!virtualMachinePrototext.exists() || !virtualMachinePrototext.isFile()) {
			throw new IOException("No prototext for virtual machine exists.");
		}
		String prototext = FileUtils.readFileToString(virtualMachinePrototext, UTF8);
		VirtualMachine.Builder vmb = VirtualMachine.newBuilder();
		TextFormat.merge(prototext, vmb);
		VirtualMachine vm = vmb.build();
		return vm;
	}

}
