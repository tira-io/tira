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
                $('#vm_power_button button:first-child').off('click').click(function() {stopVM(uid, vmid)})
            }
        }
    })
}

function stopVM(uid, vmid) {
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
            }
        }
    })
}

function addSoftwareEvents(uid, vmid) {
    if($('#vm_power_button button:first-child').text() == 'Power On') {
        $('#vm_power_button button:first-child').click(function() {startVM(uid, vmid)});
    } else {
        $('#vm_power_button button:first-child').click(function() {stopVM(uid, vmid)});
    }
}
