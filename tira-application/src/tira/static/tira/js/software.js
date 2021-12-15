let pollingState=false;
let pollingSoftware=false;
let pollingEvaluation=false;

function setupPollingAfterPageLoad(vmid) {
    $('.run-evaluate-spinner').hide()
    setState()
    loadVmInfo(vmid)
    pollRunningEvaluations(vmid)
    pollRunningSoftware(vmid)
}

function loadVmInfo(vmid) {
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_info`,
        data: {},
        success: function (data) {
            if (data.status === 'Accepted') {
                setInfo(data.message.host, data.message.guestOs,
                        data.message.memorySize, data.message.numberOfCpus);

                setState(data.message.state);
                setPorts(data.message.sshPort, data.message.sshPortStatus,
                         data.message.rdpPort, data.message.rdpPortStatus,);

                if (isTransitionState(data.message.state) && pollingState === false){
                    pollingState=true;
                    pollVmState(vmid);
                } else if (data.message.state === 1 && (!data.message.sshPortStatus || !data.message.rdpPortStatus) ) {
                    pollingState=true;
                    pollVmState(vmid);
                }

            } else {
                setConnectionError(data.message)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Loading VM info", throwError, jqXHR.responseJSON)
            setConnectionError(jqXHR.responseJSON.message)
        }
    })
}

function setConnectionError(msg) {
    setInfo(msg, null, null, null, true);
    setState(0);
    setPorts(null, false, null,false);
}

/*
** VM STATE CONTROL
 */
function startVM(vmid) {
    disableButton('vm-power-on-button')
    setState(0)
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_start`,
        data: {},
        success: function (data) {
            //in this case, the host accepted our request and we are powering on.
            if (data.status === 0) {
                setState(3)
                pollVmState(vmid)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Starting VM", throwError, jqXHR.responseJSON)
            loadVmInfo(vmid)
        }
    })
}

function shutdownVM(vmid) {
    disableButton('vm-shutdown-button')
    setState(0)
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_shutdown`,
        data: {},
        success: function (data) {
            if (data.status === 0) {
                setState(4)
                pollVmState(vmid)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Shutting VM down", throwError, jqXHR.responseJSON)
            loadVmInfo(vmid)
        }
    })
}

function stopVM(vmid) {
    disableButton('vm-stop-button')
    setState(0)
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_stop`,
        data: {},
        success: function (data) {
            if (data.status === 0) {
                setState(4)
                pollVmState(vmid)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Stopping VM", throwError, jqXHR.responseJSON)
            loadVmInfo(vmid)
        }
    })
}

function pollVmState(vmid, pollTimeout=5000) {
    setTimeout(function () {
        // TODO handle on fail.
        $.ajax({
            type: 'GET',
            url: `/grpc/${vmid}/vm_state`,
            data: {},
            success: function (data) {
                if (isTransitionState(data.state)){
                    setState(data.state);
                    pollVmState(vmid);
                } else {
                    pollingState = false
                    loadVmInfo(vmid)
                }
            },
            error: function (jqXHR, textStatus, throwError) {
                console.log("Polling vm state", throwError, jqXHR.responseJSON)
            }
        })
    }, pollTimeout);
}

function pollRunningSoftware(vmid) {
    setTimeout(function () {
        // TODO handle on fail.
        $.ajax({
            type: 'GET',
            url: `/grpc/${vmid}/vm_state`,
            data: {},
            success: function (data) {
                if (isTransitionState(data.state)){
                    if (isSoftwareRunningState(data.state)){
                        pollingSoftware=true;
                    }
                    setState(data.state);
                    pollRunningSoftware(vmid);
                } else {
                    // Note: It's easiest to reload the page here instead of adding the runs to the table via JS.
                    if (pollingSoftware === true) location.reload();
                }
            },
            error: function (jqXHR, textStatus, throwError) {
                console.log("Polling running softwares", throwError, jqXHR.responseJSON)
            }
        })
    }, 10000);
}

function pollRunningEvaluations(vmid) {
    setTimeout(function () {
        $.ajax({
            type: 'GET',
            url: `/grpc/${vmid}/vm_running_evaluations`,
            data: {},
            success: function (data) {
                if (data.running_evaluations === true ){
                    pollingEvaluation=true;
                    pollRunningEvaluations(vmid);
                } else {
                    // Note: It's easiest to reload the page here instead of adding the runs to the table via JS.
                    if (pollingEvaluation === true) location.reload();
                }
            },
            error: function (jqXHR, textStatus, throwError) {
                console.log("Polling Evaluations", throwError, jqXHR.responseJSON)
            }
        })
    }, 10000);
}

/*
** SOFTWARE MANAGEMENT
 */
function addSoftware(tid, vmid) {
    $.ajax({
        type: 'GET',
        url: `/task/${tid}/vm/${vmid}/software_add`,
        data: {},
        success: function (data) {
            // data is the rendered html of the new software form
            // see templates/tira/software-form.html
            $('#tira-software-forms').append(data.html);
            $('#tira-software-tab').find(' > li:last-child').before(`<li><a href="#">${data.software_id}</a></li>`);

            // add event listeners
            $(`#${data.software_id}-row .software-run-button`).click(function () {
                runSoftware(tid, vmid, $(this).data('tiraSoftwareId'))
            });

            $(`#${data.software_id}-row .software-save-button`).click(function () {
                saveSoftware(tid, vmid, $(this).data("tiraSoftwareId"));
            })

            $(`#${data.software_id}-row .software-delete-button`).click(function () {
                let formId = '#' + $(this).data("tiraSoftwareId") + '-row'
                deleteSoftware(tid, vmid, $(this).data("tiraSoftwareId"), $(formId));
            })
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Adding Software", throwError, jqXHR.responseJSON)
        }
    })
}

function deleteSoftware(tid, vmid, softwareId, form) {
    $.ajax({
        type: 'GET',
        url: `/task/${tid}/vm/${vmid}/software_delete/${softwareId}`,
        //TODO: Maybe rename keys
        data: {},
        success: function (data) {
            form.remove();
            $('#tira-software-tab').find('.uk-active')[0].remove()
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Deleting Software " + softwareId + " ", throwError, jqXHR.responseJSON)
        }
    })
}

function saveSoftware(taskId, vmId, softwareId) {
    let token = $('input[name=csrfmiddlewaretoken]').val()
    let command = $(`#${softwareId}-command-input`).val()
    let inputDataset = $(`#${softwareId}-input-dataset`).val()
    if (command === "" || inputDataset === "" ){

    }
    $.ajax({
        type: 'POST',
        url: `/task/${taskId}/vm/${vmId}/software_save/${softwareId}`,
        headers: {
            'X-CSRFToken': token
        },
        //TODO: Maybe rename keys
        data: {
            command: command,
            working_dir: $(`#${softwareId}-working-dir`).val(),
            input_dataset: inputDataset,
            input_run: $(`#${softwareId}-input-run`).val(),
            csrfmiddlewaretoken: token,
            action: 'post'
        },
        success: function (data) {
            $('.software-save-button').html('<i class="fas fa-check"></i>');
            setTimeout(function () {
                $('.software-save-button').html('<i class="fas fa-save"></i>');
            }, 5000)
            $(`#${softwareId}-last-edit`).text(`last edit: ${data.last_edit}`)
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Saving Software " + softwareId + " ", throwError, jqXHR.responseJSON)
            $('.software-save-button').html('<i class="fas fa-times"></i>');
            setTimeout(function () {
                $('.software-save-button').html('<i class="fas fa-save"></i>');
            }, 2000)

        }
    })
}

function runSoftware (taskId, vmId, softwareId) {
    // 0. execute save software
    saveSoftware(taskId, vmId, softwareId);
    setState(0);
    // 1. make ajax call
    $.ajax({
        type: 'POST',
        url: `/grpc/${taskId}/${vmId}/run_execute/${softwareId}`,
        headers: {
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
        },
        data: {
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function (data) {
            pollRunningSoftware(vmId)
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Running Software " + softwareId + " ", throwError, jqXHR.responseJSON)
        }
    })

}

function addSoftwareEvents(taskId, vmId) {
    $('#vm-power-on-button').click(function () {
        startVM(vmId)
    });
    $('#vm-shutdown-button').click(function () {
        shutdownVM(vmId)
    });
    $('#vm-stop-button').click(function () {
        stopVM(vmId)
    });
    $('#vm-abort-run-button').click(function () {
        abortRun(vmId)
    });

    $('#add-software').click(function () {
        addSoftware(taskId, vmId);
    });

    $('.software-run-button').click(function () {
        runSoftware(taskId, vmId, $(this).data('tiraSoftwareId'))
    });

    $('.software-save-button').click(function () {
        saveSoftware(taskId, vmId, $(this).data("tiraSoftwareId"));
    })

    $('.software-delete-button').click(function () {
        let formId = '#' + $(this).data("tiraSoftwareId") + '-row'
        deleteSoftware(taskId, vmId, $(this).data("tiraSoftwareId"), $(formId));
    })

    $('.run-delete-button').click(function () {
        deleteRun($(this).data('tiraDataset'),
            $(this).data('tiraVmId'),
            $(this).data('tiraRunId'), $(this).parent().parent())
    })

    $('.run-evaluate-button').click(function () {
        evaluateRun($(this).data('tiraDataset'),
                     $(this).data('tiraVmId'),
                     $(this).data('tiraRunId'))
    });
}


/*
** RUN MANAGEMENT
 */
function abortRun(vmId) {
    disableButton('vm-abort-run-button')
    setState(0)
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmId}/run_abort`,
        data: {},
        success: function (data) {
            if (data.status === 0) {
                pollVmState(vmId);
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Aborting the run " + runId + " ", throwError, jqXHR.responseJSON)
            loadVmInfo(vmId)
        }
    })
}

function deleteRun(datasetId, vmId, runId, row) {
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmId}/run_delete/${datasetId}/${runId}`,
        data: {},
        success: function (data) {
            row.remove();
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Deleting the run " + runId + " ", throwError, jqXHR.responseJSON)
            loadVmInfo(vmId)
        }
    })
}

function evaluateRun(datasetId, vmId, runId, row) {
    disableButton("run-evaluate-button")
    let spinner_id = 'run-evaluate-spinner-' + runId
    $('#' + spinner_id).show()

    $.ajax({
        type: 'GET',
        url: `/grpc/${vmId}/run_eval/${datasetId}/${runId}`,
        data: {},
        success: function (data) {
            pollingEvaluation=true;
            pollRunningEvaluations(vmId)
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Evaluating the run " + runId + " ", throwError, jqXHR.responseJSON)
            loadVmInfo(vmId)
            $('#run-evaluate-spinner-' + runId).hide()
            enableButton("run-evaluate-button")
        }
    })
}


/*
** UTILITY
 */
function disableButton(id) {
    $('#' + id).prop("disabled", true)
        .removeClass('uk-button-primary')
        .removeClass('uk-button-danger')
        .removeClass('uk-button-default')
        .addClass('uk-button-disabled');

    $('.' + id).prop("disabled", true)
        .removeClass('uk-button-primary')
        .removeClass('uk-button-danger')
        .removeClass('uk-button-default')
        .addClass('uk-button-disabled');
}

function enableButton(id, cls) {
    $('#' + id).prop("disabled", false)
        .removeClass('uk-button-disabled')
        .addClass(cls);

    $('.' + id).prop("disabled", false)
        .removeClass('uk-button-disabled')
        .addClass(cls);
}

/* This function sets the State labels and the Buttons
State IDs follow the tira protocol specification (in tira_host.proto) */
function setState(state_id) {
    let spinner = $('#vm-state-spinner');
    let running = $('#vm-state-running');
    let powering_on = $('#vm-state-powering-on');
    let powering_off = $('#vm-state-powering-off');
    let stopped = $('#vm-state-stopped');
    let sandboxed = $('#vm-state-sandboxed');
    let sandboxing = $('#vm-state-sandboxing');
    let unsandboxing = $('#vm-state-unsandboxing');
    let archived = $('#vm-state-archived');
    let unarchiving = $('#vm-state-unarchiving');
    let undef = $('#vm-state-undefined');

    spinner.hide()
    running.hide()
    powering_on.hide()
    powering_off.hide()
    stopped.hide()
    sandboxed.hide()
    sandboxing.hide()
    unsandboxing.hide()
    archived.hide()
    unarchiving.hide()
    undef.hide()

    disableButton('vm-shutdown-button');
    disableButton('vm-power-on-button');
    disableButton('vm-stop-button');
    disableButton('vm-abort-run-button');
    disableButton('software-run-button');

    switch (state_id) {
        case 0:
            spinner.show();
            break;
        case 1:  // RUNNING = 1;
            running.show();
            enableButton('vm-shutdown-button', 'uk-button-primary');
            enableButton('software-run-button', 'uk-button-primary');
            break;
        case 2:  // POWERED_OFF = 2;
            stopped.show();
            enableButton('vm-power-on-button', 'uk-button-primary');
            break;
        case 3:  // POWERING_ON = 3;
            powering_on.show();
            enableButton('vm-stop-button', 'uk-button-danger');
            break;
        case 4:  // POWERING_OFF = 4;
            powering_off.show();
            enableButton('vm-stop-button', 'uk-button-danger');
            break;
        case 5:  // SANDBOXING = 5;
            sandboxing.show();
            enableButton('vm-abort-run-button', 'uk-button-danger');
            break;
        case 6:  // UNSANDBOXING = 6
            unsandboxing.show();
            enableButton('vm-abort-run-button', 'uk-button-danger');
            break;
        case 7:  // EXECUTING = 7;
            sandboxed.show();
            enableButton('vm-abort-run-button', 'uk-button-danger');
            break;
        case 8: // ARCHIVED = 8
            archived.show();
            break;
        case 9:
            unarchiving.show();
            break;
        case 10:  // Host Unavailable
            undef.show()
            break;
        default:
            break;
    }
}
/* This function sets the Ports and Port labels and the Buttons */
function setPorts(ssh, ssh_status, rdp, rdp_status) {
    let ssh_text = $('#vm-state-ssh');
    let ssh_open = $('#vm-state-ssh-open');
    let ssh_closed = $('#vm-state-ssh-closed');
    let rdp_text = $('#vm-state-rdp');
    let rdp_open = $('#vm-state-rdp-open');
    let rdp_closed = $('#vm-state-rdp-closed');

    ssh !== null ? ssh_text.text('port ' + ssh) : ssh_text.text("")
    if (ssh_status){
        ssh_open.show()
        ssh_closed.hide()
    } else {
        ssh_open.hide()
        ssh_closed.show()
    }

    rdp !== null ? rdp_text.text('port ' + rdp) : rdp_text.text("")
    if (rdp_status) {
        rdp_open.show()
        rdp_closed.hide()
    } else {
        rdp_open.hide()
        rdp_closed.show()
    }
}

/* This function sets the Info block Texts */
function setInfo(host, os=null, ram=null, cpu=null, warn=false) {
    let host_td = $('#vm-info-host');

    $('#vm-info-spinner').hide();

    if (host !== null) host_td.text(host);
    if (os !== null) $('#vm-info-guestOs').text(os);
    if (ram !== null) $('#vm-info-memorySize').text(ram);
    if (cpu !== null) $('#vm-info-numberOfCpus').text(cpu);
    warn ? host_td.addClass('uk-text-danger') : host_td.removeClass('uk-text-danger');
}

// Note: We use these helper functions so we can easily change what the state numbers mean.
function isTransitionState(state_id) {
    return [3, 4, 5, 6, 7].includes(state_id);
}

function isSoftwareRunningState(state_id) {
    return [5, 6, 7].includes(state_id);
}
