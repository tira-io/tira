package de.webis.tira.client.web.storage;

import java.io.File;

public class Directories {
	
	private static final String
		_TIRA_NFS         = "/mnt/nfs/tira",
		
		_DATA             = "data",
		_LOG              = "log",
		_MODEL            = "model",
		_STATE            = "state",
		
		_ERRORS           = "errors",
		_ORGANIZERS       = "organizers",
		_RUNS             = "runs",
		_DATASETS         = "datasets",
		_SOFTWARES        = "softwares",
		_TASKS            = "tasks",
		_USERS            = "users",
		_VIRTUAL_MACHINES = "virtual-machines",
		
    	_SUPERVISOR_CONFS = "/etc/supervisor/conf.d/tira",
		_SUPERVISOR_LOGS  = "/var/log/supervisor/tira";
	
	public static final File
		TIRA_NFS         = new File(_TIRA_NFS),
		
		DATA             = new File(TIRA_NFS, _DATA),
		LOG              = new File(TIRA_NFS, _LOG),
		MODEL            = new File(TIRA_NFS, _MODEL),
		STATE            = new File(TIRA_NFS, _STATE),
		
		ORGANIZERS       = new File(MODEL, _ORGANIZERS),
		RUNS             = new File(DATA, _RUNS),
		ERRORS           = new File(LOG, _ERRORS),
		DATASETS_MODEL   = new File(MODEL, _DATASETS),
		SOFTWARES_MODEL  = new File(MODEL, _SOFTWARES),
		SOFTWARES_STATE  = new File(STATE, _SOFTWARES),
		TASKS            = new File(MODEL, _TASKS),
		USERS            = new File(MODEL, _USERS),
		VIRTUAL_MACHINES_MODEL = new File(MODEL, _VIRTUAL_MACHINES),
		VIRTUAL_MACHINES_STATE = new File(STATE, _VIRTUAL_MACHINES),
		
		SUPERVISOR_CONFS = new File(_SUPERVISOR_CONFS),
		SUPERVISOR_LOGS  = new File(_SUPERVISOR_LOGS);

	private Directories() {}
	
}
