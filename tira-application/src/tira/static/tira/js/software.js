function loadVmInfo(vmid) {
    setState(0)

    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_info`,
        data: {},
        success: function (data) {
            console.log(data.message)
            if (data.status === 'Accepted') {
                $('#vm-info-spinner').hide()
                $('#vm-info-host').text(data.message.host)
                $('#vm-info-guestOs').text(data.message.guestOs)
                $('#vm-info-memorySize').text(data.message.memorySize)
                $('#vm-info-numberOfCpus').text(data.message.numberOfCpus)

                // logic status
                $('#vm-state-spinner').hide();
                setState(data.message.state);

                // sshPortStatus
                $('#vm-state-ssh').text('port ' + data.message.sshPort)
                if (data.message.sshPortStatus) {
                    $('#vm-state-ssh-open').show()
                    $('#vm-state-ssh-closed').hide()
                } else {
                    $('#vm-state-ssh-open').hide()
                    $('#vm-state-ssh-closed').show()
                }

                // rdpPortStatus
                $('#vm-state-rdp').text('port ' + data.message.rdpPort)
                if (data.message.rdpPortStatus) {
                    $('#vm-state-rdp-open').show()
                    $('#vm-state-rdp-closed').hide()
                } else {
                    $('#vm-state-rdp-open').hide()
                    $('#vm-state-rdp-closed').show()
                }

            } else {
                $('#vm-info-spinner').hide()
                $('#vm-state-spinner').hide()
                $('#vm-info-host').text('Error contacting host: ' + data.message)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            $('#vm-info-spinner').hide()
            $('#vm-state-spinner').hide()
            console.log(jqXHR)
            $('#vm-info-host').text(throwError)
        }
    })
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
        }
    })
}

function pollVmState(vmid) {
    setTimeout(function () {
        console.log("Polling VM State");
        // TODO handle on fail.
        $.ajax({
            type: 'GET',
            url: `/grpc/${vmid}/vm_state`,
            data: {},
            success: function (data) {
                console.log(data.state);
                if (isTransitionState(data.state)){
                    setState(data.state);
                    pollVmState(vmid);
                } else {
                    loadVmInfo(vmid)
                }
            }
        })
    }, 5000);
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
        }
    })
}

function deleteSoftware(tid, vmid, swid, form) {
    $.ajax({
        type: 'GET',
        url: `/task/${tid}/vm/${vmid}/software_delete/${swid}`,
        //TODO: Maybe rename keys
        data: {},
        success: function (data) {
            form.remove();
            $('#tira-software-tab').find('.uk-active')[0].remove()
        }
    })
}

function saveSoftware(taskId, vmId, softwareId) {
    $.ajax({
        type: 'POST',
        url: `/task/${taskId}/vm/${vmId}/software_save/${softwareId}`,
        headers: {
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
        },
        //TODO: Maybe rename keys
        data: {
            command: $(`#${softwareId}-command-input`).val(),
            working_dir: $(`#${softwareId}-working-dir`).val(),
            input_dataset: $(`#${softwareId}-input-dataset`).val(),
            input_run: $(`#${softwareId}-input-run`).val(),
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function (data) {
            $(`#${softwareId}_form_buttons a:nth-of-type(2)`).html(' <i class="fas fa-check"></i>');
            setTimeout(function () {
                $(`#${softwareId}_form_buttons a:nth-of-type(2)`).html('save');
            }, 5000)
            $(`#${softwareId}-last-edit`).text(`last edit: ${data.last_edit}`)
        },
        error: function () {
            $(`#${softwareId}_form_buttons a:nth-of-type(2)`).html(' <i class="fas fa-times"></i>');
            setTimeout(function () {
                $(`#${softwareId}_form_buttons a:nth-of-type(2)`).html('save');
            }, 2000)

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

    $('#tira-add-software').click(function () {
        addSoftware(taskId, vmId);
    });

    $('.software_form_buttons a:nth-of-type(2)').click(function (e) {
        let softwareId = e.target.parentElement.id.split('_')[0];
        saveSoftware(taskId, vmId, softwareId);
    })

    $('.software_form_buttons a:nth-of-type(3)').click(function (e) {
        let form = e.target.parentElement.parentElement
        let softwareId = e.target.parentElement.id.split('_')[0];
        deleteSoftware(taskId, vmId, softwareId, form);
    })

    $('.tira-run-delete').click(function (e) {
        let row = e.target.parentElement.parentElement
        let id = row.firstElementChild.id.split("_")
        runDelete(id[0], id[1], id[2], row)
    })
}


/*
** RUN MANAGEMENT
 */
function abortRun(uid, vmId) {
    disableButton('vm-abort-run-button')
    setState(0)
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmId}/vm_abort_run`,
        data: {},
        success: function (data) {
            if (data.status === 0) {
                loadVmInfo(vmId)
            }
        }
    })
}

function runDelete(datasetId, vmId, runId, row) {
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmId}/run_delete/${datasetId}/${runId}`,
        data: {},
        success: function (data) {
            row.remove();
        }
    })
}


/*
** UTILITY
 */
function disableButton(id) {
    // Console.log($('#' + id))
    $('#' + id).prop("disabled", true)
        .removeClass('uk-button-primary')
        .removeClass('uk-button-danger')
        .removeClass('uk-button-default')
        .addClass('uk-button-disabled');
}

function enableButton(id, cls) {
    $('#' + id).prop("disabled", false)
        .removeClass('uk-button-disabled')
        .addClass(cls);
}

/* State IDs follow the tira protocol specification (in tira_host.proto)
UNDEFINED = 0;
RUNNING = 1;
POWERED_OFF = 2;
POWERING_ON = 3;
POWERING_OFF = 4;
SANDBOXING = 5;
UNSANDBOXING = 6;
EXECUTING = 7;  // sandboxed
ARCHIVED = 8;
 */
function setState(state_id) {
    $('#vm-state-spinner').hide();
    $('#vm-state-running').hide();
    $('#vm-state-powering-on').hide();
    $('#vm-state-powering-off').hide();
    $('#vm-state-stopped').hide();
    $('#vm-state-sandboxed').hide();
    $('#vm-state-sandboxing').hide();
    $('#vm-state-unsandboxing').hide();
    $('#vm-state-archived').hide();
    $('#vm-state-unarchiving').hide();
    $('#vm-state-undefined').hide();

    if (state_id === 1) {
        $('#vm-state-running').show();
        enableButton('vm-shutdown-button', 'uk-button-primary')
        enableButton('vm-stop-button', 'uk-button-danger')
    } else if (state_id === 2) {
        $('#vm-state-stopped').show();
        enableButton('vm-power-on-button', 'uk-button-primary')
    } else if (state_id === 3) {
        $('#vm-state-powering-on').show();
        enableButton('vm-stop-button', 'uk-button-danger')
    } else if (state_id === 4) {
        $('#vm-state-powering-off').show();
        enableButton('vm-stop-button', 'uk-button-danger')
    } else if (state_id === 5) {
        $('#vm-state-sandboxing').show();
        enableButton('vm-stop-button', 'uk-button-danger')
    } else if (state_id === 6) {
        $('#vm-state-unsandboxing').show();
        enableButton('vm-stop-button', 'uk-button-danger')
    } else if (state_id === 7) {
        $('#vm-state-sandboxed').show();
        enableButton('vm-stop-button', 'uk-button-danger')
        enableButton('vm-abort-run-button', 'uk-button-danger')
    } else if (state_id === 8) {
        $('#vm-state-archived').show();
    } else if (state_id === 8) {
        $('#vm-state-unarchiving').show();
    } else if (state_id === 0) {
        $('#vm-state-ssh-open').hide();
        $('#vm-state-ssh-closed').hide();
        $('#vm-state-rdp-open').hide();
        $('#vm-state-rdp-closed').hide();
        $('#vm-state-spinner').show();
        disableButton('vm-shutdown-button');
        disableButton('vm-power-on-button');
        disableButton('vm-stop-button');
        disableButton('vm-abort-run-button');
    }
}

function isTransitionState(state_id) {
    return [3, 4, 5, 6, 7].includes(state_id);
}
