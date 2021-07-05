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

    reloadVmState(location.href);
}
