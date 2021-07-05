function startVM(uid, vmid) {
    $.ajax({
        type: 'GET',
        url: `/grpc/${vmid}/vm_start`,
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
        url: `/grpc/${vmid}/vm_stop`,
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

function loadVmInfo(vmid) {

    $('#vm-state-running').hide()
    $('#vm-state-stopped').hide()
    $('#vm-state-sandboxed').hide()
    $('#vm-state-ssh-open').hide()
    $('#vm-state-ssh-closed').hide()
    $('#vm-state-rdp-open').hide()
    $('#vm-state-rdp-closed').hide()

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
                    $('#vm-state-running').show()
                    $('#vm-state-stopped').hide()
                    $('#vm-state-sandboxed').hide()
                } else if(data.message.state === 'stopped'){
                    $('#vm-state-running').hide()
                    $('#vm-state-stopped').show()
                    $('#vm-state-sandboxed').hide()
                } else if(data.message.state === 'sandboxed'){
                    $('#vm-state-running').hide()
                    $('#vm-state-stopped').hide()
                    $('#vm-state-sandboxed').show()
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
    if($('#vm_power_button button:first-child').text() == 'Power On') {
        $('#vm_power_button button:first-child').click(function() {startVM(uid, vmid)});
    } else {
        $('#vm_power_button button:first-child').click(function() {stopVM(uid, vmid)});
    }
}
