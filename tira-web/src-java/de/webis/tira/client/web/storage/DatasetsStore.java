package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.protobuf.TextFormat;
import com.google.protobuf.TextFormat.ParseException;

import de.webis.tira.client.web.generated.TiraClientWebMessages.Dataset;

public class DatasetsStore {
	
	private static final Charset
		UTF8 = Charsets.UTF_8;
	
	public static boolean
	isConfidential(String taskId, String datasetId)
	throws IOException {
		Dataset d = getDataset(taskId, datasetId);
		return d.getIsConfidential();
	}

	public static String 
	getEvaluatorId(String taskId, String datasetId)
	throws ParseException, IOException {
		Dataset d = getDataset(taskId, datasetId);
		return d.getEvaluatorId();
	}
	
	public static Dataset
	getDataset(String taskId, String datasetId)
	throws IOException {
		File datasetsDir = Directories.DATASETS_MODEL;
		File taskDir = new File(datasetsDir, taskId);
		if (!taskDir.exists() || !taskDir.isDirectory()) {
			throw new IOException("No task directory " + taskId + " exists in datasets.");
		}
		String datasetPrototextName = datasetId + ".prototext";
		File datasetPrototext = new File (taskDir, datasetPrototextName);
		if (!datasetPrototext.exists() || !datasetPrototext.isFile()) {
			throw new IOException(datasetPrototextName + " not found.");
		}
		String prototext = FileUtils.readFileToString(datasetPrototext, UTF8);
		Dataset.Builder db = Dataset.newBuilder();
		TextFormat.merge(prototext, db);
		Dataset d = db.build();
		return d;
	}
}
