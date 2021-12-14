
function reloadData() {
    $('#reload-website-data-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: "/tira-admin/reload-data",
        data:{},
        success: function( data )
        {
            $('#reload-website-data-icon').html(' <i class="fas fa-check"></i>')
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

function warningAlert(action, error, response) {
    if (response.status === '1') {
        UIkit.notification('Warning: ' + action + ' failed. If you think this is a TIRA problem, please contact the support.' +
            '<br>' +
            '<span class="uk-text-small">' + error + ' ' + JSON.stringify(response) + '.</span>', 'warning');
    } else if (response.status === '2') {
        UIkit.notification('Critical: ' + action + ' failed. Please contact the support.' +
            '<br>' +
            '<span class="uk-text-small">' + error + ' ' + JSON.stringify(response) + '.</span>', 'danger');
    } else {
        UIkit.notification(action + ' responded with: <span class="uk-text-small">' +
        error + ' ' + JSON.stringify(response) + '</span>', 'primary');
    }

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
    let endpoint = "/tira-admin/create-group/" + $('#id_vm_id').val()
    $.ajax({
        type:"POST",
        url: endpoint,
        headers: {
            'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val()
        },
        data:{
            vm_id:$('#id_vm_id').val(),
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function( data )
        {
            document.getElementById("create-group-form").reset();
            if (data.status === 1) {
                $('#create-group-form-icon').html(' <i class="fas fa-check"></i>')
                UIkit.modal.dialog('<p>' + data.message + '</p>');
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
    $('#reload-website-data').click(function() {reloadData()})
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

