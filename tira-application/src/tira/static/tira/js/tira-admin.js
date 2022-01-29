function reloadData(model_object) {
    let icon = null
    let uri = null
    switch (model_object) {
        case 'all':
            icon = $('#reload-website-data-icon')
            uri = "/tira-admin/reload-data"
            break
        case 'vms':
            icon = $('#reload-vms-data-icon')
            uri = "/tira-admin/reload-vms"
            break
        case 'datasets':
            icon = $('#reload-datasets-data-icon')
            uri = "/tira-admin/reload-datasets"
            break
        case 'tasks':
            icon = $('#reload-tasks-data-icon')
            uri = "/tira-admin/reload-tasks"
            break
    }
    icon.html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: uri,
        data:{},
        success: function( data )
        {
            if (data.status === 1) {
                icon.html(' <i class="fas fa-check"></i>')
            } else {
                icon.html(' <i class="fas fa-times"></i>')
                warningAlert("Create Group",  "Undefined", data.message)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            icon.html(' <i class="fas fa-times"></i>')
            warningAlert("Reload failed for " + model_object, throwError, jqXHR.responseJSON)
        }
    })
}

function string_to_slug (str) {
    str = str.replace(/^\s+|\s+$/g, ''); // trim
    str = str.toLowerCase();

    // remove accents, swap ñ for n, etc
    var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
    var to   = "aaaaeeeeiiiioooouuuunc------";
    for (var i=0, l=from.length ; i<l ; i++) {
        str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
    }

    str = str.replace(/\./g, '-')
        .replace(/[^a-z0-9 -]/g, '') // remove invalid chars
        .replace(/\s+/g, '-') // collapse whitespace and replace by -
        .replace(/-+/g, '-'); // collapse dashes

    return str;
}

function submitCreateVmForm(){
    $('#create-vm-form-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"POST",
        url: "/tira-admin/create-vm",
        headers: {
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
        },
        data:{
            bulk_create:$('#id_bulk_create').val(),
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function( data )
        {
            document.getElementById("create-vm-form").reset();
            $('#create-vm-form-icon').html('');
            $('#create-vm-form-error').text(data['create_vm_form_error']);
            $('#create-vm-form-results').text(data)
        }
    })
}

function submitCreateGroup(){
    $('#create-group-form-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    let vm_id = $('#id_vm_id').val()
    let token = $('input[name=csrfmiddlewaretoken]').val()
    let endpoint = "/tira-admin/create-group/" + vm_id
    $.ajax({
        type:"POST",
        url: endpoint,
        headers: {
            'X-CSRFToken':token
        },
        data:{
            vm_id:vm_id,
            csrfmiddlewaretoken:token,
            action: 'post'
        },
        success: function( data )
        {
            document.getElementById("create-group-form").reset();
            if (data.status === 1) {
                $('#create-group-form-icon').html(' <i class="fas fa-check"></i>')
                UIkit.modal.dialog('<div class="uk-section uk-section-default"><div class="uk-container">' +
                    '<h2>Invite for VM ' +
                    vm_id +
                    '</h2><p>' +
                    data.message +
                    '</p></div></div>');
            } else {
                $('#create-group-form-icon').html('')
                $('#create-group-form-error').text(data['create_group_form_error']);
                warningAlert("Create Group", "Undefined", data.message)
            }
        },
        error: function (jqXHR, textStatus, throwError) {
            warningAlert("Create Group", throwError, jqXHR.responseJSON)
        }
    })
}

function addTiraAdminHandlers() {
    $('#reload-website-data').click(function() {reloadData('all')})
    $('#reload-vms-data').click(function() {reloadData('vms')})
    $('#reload-datasets-data').click(function() {reloadData('datasets')})
    $('#reload-tasks-data').click(function() {reloadData('tasks')})
    $('#create-vm-form').submit(function(e) {
        e.preventDefault();
        submitCreateVmForm()
    })
    $('#create-group-form').submit(function(e) {
        e.preventDefault();
        submitCreateGroup()
    })

    $('#id_dataset_name').keyup(function() {
        let name = this.val()
        this.val(string_to_slug(name))
    }).keydown(function() {
        let name = this.val()
        this.val(string_to_slug(name))
    })
}

