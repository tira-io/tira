
function reloadData() {
    $('#reload-website-data-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: "/tira/admin/reload-data",
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

function add_slug() {

}


function submitCreateVmForm(){
    $('#create-vm-form-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"POST",
        url: "/tira/admin/create-vm",
        data:{
            bulk_create:$('#id_bulk_create').val(),
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function( data )
        {
            document.getElementById("create-vm-from").reset();
            $('#create-vm-from-icon').html('');
            $('#create-vm-form-error').text(data['create_vm_form_error']);
            $('#create-vm-form-results').text(data)
        }
    })
}

function addTiraAdminHandlers() {
    $('#reload-website-data').click(function() {reloadData()})
    $('#create-vm-from').submit(function(e) {
        e.preventDefault();
        submitCreateVmForm()
    })
    $('#id_dataset_name').keyup(function() {
        let name = $('#id_dataset_name').val()
        $('#id_dataset_id_prefix').val(string_to_slug(name))
    })
    $('#id_dataset_name').keydown(function() {
        let name = $('#id_dataset_name').val()
        $('#id_dataset_id_prefix').val(string_to_slug(name))
    })
}

