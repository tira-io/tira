
/* Start a VM
After the click, do:
- disable the start button
- set state to loading
- do the ajax event
- on success, do the vm-info again.

 */
function startVM(uid, vmid) {
    disableButton('vm-power-on-button')
    setState("loading")
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_start`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                loadVmInfo(vmid) 
            }
        }
    })
}

function shutdownVM(uid, vmid) {
    disableButton('vm-shutdown-button')
    setState("loading")
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_shutdown`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                loadVmInfo(vmid)
            }
        }
    })
}

function stopVM(uid, vmid) {
    disableButton('vm-stop-button')
    setState("loading")
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_stop`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                loadVmInfo(vmid)
            }
        }
    })
}

function abortRun(uid, vmid){
    disableButton('vm-abort-run-button')
    setState("loading")
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_abort_run`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                loadVmInfo(vmid)
            }
        }
    })
}

function saveSoftware(tid, vmid, swid){
    console.log(swid);
    console.log(tid);
    $.ajax({
        type: 'POST',
        url: `/task/${tid}/vm/${vmid}/software_save/${swid}`,
        headers: {
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
        },
        //TODO: Maybe rename keys
        data: {
            command: $(`#${swid}-command-input`).val(),
            working_dir: $(`#${swid}-working-dir`).val(),
            input_dataset: $(`#${swid}-input-dataset`).val(),
            input_run: $(`#${swid}-input-run`).val(),
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function(data){
            $(`#${swid}_form_buttons a:last-of-type`).html(' <i class="fas fa-check"></i>');
            setTimeout(function() {
                $(`#${swid}_form_buttons a:last-of-type`).html('save');
            }, 5000)
            $(`#${swid}-last-edit`).text(`last edit: ${data.last_edit}`)
        }
    })
}

function addSoftware(tid, vmid){
    $.ajax({
        type: 'GET',
        url: `/task/${tid}/vm/${vmid}/software_add`,
        data: {},
        success: function(data){
            // data is the rendered html of the new software form
            // see templates/tira/software-form.html
            $('#tira-software-forms').append(data.html);
            $('#tira-software-tab').find(' > li:last-child').before(`<li><a href="#">${data.software_id}</a></li>`);
        }
        })
}


//function runSoftware(uid, vmid, swid){
//    $(`#${swid}_form_buttons a:first-child`).html(' <div uk-spinner="ratio: 0.5"></div>');
//    $(`#${swid}_form_buttons a:first-child`).prop('disabled', true);

//}
        

// Every 10s reload the content of the #vm_state div.
//function reloadVmState(url){
//    setTimeout(function() {
//        if (location.href == url){
//            console.log("Reloading VM State");
//            $('#vm_state').load(location.href + ' #vm_state>*', '');
//            reloadVmState(url);
//        }
//    }, 10000);

function disableButton(id) {
    // Console.log($('#' + id))
    $('#' + id).prop( "disabled", true)
        .removeClass('uk-button-primary')
        .removeClass('uk-button-danger')
        .removeClass('uk-button-default')
        .addClass('uk-button-disabled');
}

function enableButton(id, cls) {
    $('#' + id).prop( "disabled", false)
        .removeClass('uk-button-disabled')
        .addClass(cls);
}

function setState(state_name) {
    $('#vm-state-spinner').hide();
    $('#vm-state-running').hide();
    $('#vm-state-stopped').hide();
    $('#vm-state-sandboxed').hide();
    $('#vm-state-sandboxing').hide();

    if(state_name === 'running') {
        $('#vm-state-running').show();
    } else if(state_name === 'stopped') {
        $('#vm-state-stopped').show();
    } else if(state_name === 'sandboxed') {
        $('#vm-state-sandboxed').show();
    } else if(state_name === 'sandboxing') {
        $('#vm-state-sandboxing').show();
    } else if(state_name === 'loading') {
        $('#vm-state-ssh-open').hide();
        $('#vm-state-ssh-closed').hide();
        $('#vm-state-rdp-open').hide();
        $('#vm-state-rdp-closed').hide();
        $('#vm-state-spinner').show();
    }
}

function runDelete(dsid, vmid, rid, row) {
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/run_delete/${dsid}/${rid}`,
        data: {},
        success: function(data)
        {
            row.remove();
        }
    })
}


function loadVmInfo(vmid) {
    setState("loading")

    disableButton('vm-shutdown-button')
    disableButton('vm-power-on-button')
    disableButton('vm-stop-button')
    disableButton('vm-abort-run-button')

    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_info`,
        data: {},
        success: function(data)
        {
            console.log(data.message)
            if(data.status === 'Accepted'){
                $('#vm-info-spinner').hide()
                $('#vm-info-host').text(data.message.host)
                $('#vm-info-guestOs').text(data.message.guestOs)
                $('#vm-info-memorySize').text(data.message.memorySize)
                $('#vm-info-numberOfCpus').text(data.message.numberOfCpus)

                // logic status
                $('#vm-state-spinner').hide()
                if(data.message.state === 'running'){
                    setState('running')
                    enableButton('vm-shutdown-button', 'uk-button-primary')
                    enableButton('vm-stop-button', 'uk-button-danger')
                } else if(data.message.state === 'stopped'){
                    setState('stopped')
                    enableButton('vm-power-on-button', 'uk-button-primary')
                } else if(data.message.state === 'sandboxed'){
                    setState('sandboxed')
                    enableButton('vm-stop-button', 'uk-button-danger')
                    enableButton('vm-abort-run-button', 'uk-button-danger')
                } else if(data.message.state === 'sandboxing'){
                    setState('sandboxing')
                    enableButton('vm-stop-button', 'uk-button-danger')
                }

                // sshPortStatus
                $('#vm-state-ssh').text('port ' + data.message.sshPort)
                if(data.message.sshPortStatus) {
                    $('#vm-state-ssh-open').show()
                    $('#vm-state-ssh-closed').hide()
                } else {
                    $('#vm-state-ssh-open').hide()
                    $('#vm-state-ssh-closed').show()
                }

                // rdpPortStatus
                $('#vm-state-rdp').text('port ' + data.message.rdpPort)
                if(data.message.rdpPortStatus) {
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


function addSoftwareEvents(uid, vmid) {

    $('#vm-power-on-button').click(function() {startVM(uid, vmid)});
    $('#vm-shutdown-button').click(function() {shutdownVM(uid, vmid)});
    $('#vm-stop-button').click(function() {stopVM(uid, vmid)});
    $('#vm-abort-run-button').click(function() {abortRun(uid, vmid)});

    $('#tira-add-software').click(function() {
        var tid = window.location.pathname.split('/')[2]
        addSoftware(tid, vmid);
    });
    
    $('.software_form_buttons a:last-of-type').click(function(e) {
        var swid = e.target.parentElement.id.split('_')[0];
        var tid = window.location.pathname.split('/')[2];
        saveSoftware(tid, vmid, swid);
    })

    $('.tira-run-delete').click(function(e) {
        var row = e.target.parentElement.parentElement
        var id = row.firstElementChild.id.split("_")
        runDelete(id[0], id[1], id[2], row)
    })

//    reloadVmState(location.href);
}
