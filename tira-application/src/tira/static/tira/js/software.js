function startVM(uid, vmid) {
    $.ajax({
        type: 'GET',
        url: `/user/${uid}/vm/${vmid}/vm_start`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                $('#vm_power_button button:first-child').text('Shut Down');
                $('#vm_power_button button:first-child').addClass('uk-button-danger');
                $('#vm_power_button button:first-child').off('click').click(function() {shutdownVM(uid, vmid)})
                $('#stop_vm_button button:first-child').addClass('uk-button-primary');
                $('#stop_vm_button button:first-child').prop('disabled', false);
                $('#abort_run_button button:first-child').addClass('uk-button-primary');
                $('#abort_run_button button:first-child').prop('disabled', false);

            }
        }
    })
}

function shutdownVM(uid, vmid) {
    $.ajax({
        type: 'GET',
        url: `/user/${uid}/vm/${vmid}/vm_stop`,
        data: {},
        success: function(data)
        {
            if(data.status === 'Accepted'){
                $('#vm_power_button button:first-child').text('Power On');
                $('#vm_power_button button:first-child').removeClass('uk-button-danger');
                $('#vm_power_button button:first-child').off('click').click(function() {startVM(uid, vmid)})
                $('#stop_vm_button button:first-child').removeClass('uk-button-primary');
                $('#stop_vm_button button:first-child').prop('disabled', true);
                $('#abort_run_button button:first-child').removeClass('uk-button-primary');
                $('#abort_run_button button:first-child').prop('disabled', true);
            }
        }
    })
}

function stopVM() {

}

function abortRun(){

}

function saveSoftware(uid, vmid, swid){
    $.ajax({
        type: 'POST',
        url: `/user/${uid}/vm/${vmid}/software_save/${swid}`,
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
        }
    })
}

//function runSoftware(uid, vmid, swid){
//    $(`#${swid}_form_buttons a:first-child`).html(' <div uk-spinner="ratio: 0.5"></div>');
//    $(`#${swid}_form_buttons a:first-child`).prop('disabled', true);

//}
        

// Every 10s reload the content of the #vm_state div.
function reloadVmState(url){
    setTimeout(function() {
        if (location.href == url){
            console.log("Reloading VM State");
            $('#vm_state').load(location.href + ' #vm_state>*', '');
            reloadVmState(url);
        }
    }, 10000);
}

function addSoftwareEvents(uid, vmid) {
    if($('#vm_power_button button:first-child').text() == 'Power On') {
        $('#vm_power_button button:first-child').click(function() {startVM(uid, vmid)});
    } else {
        $('#vm_power_button button:first-child').click(function() {shutdownVM(uid, vmid)});
    }

    $('.software_form_buttons a:last-of-type').click(function(e) {
        var swid = e.target.parentElement.id.split('_')[0]
        saveSoftware(uid, vmid, swid);
    })

    reloadVmState(location.href);
}
