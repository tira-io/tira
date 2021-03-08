
function reloadData() {
    $('#tira-admin-reload-data-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: "/tira/admin/reload-data",
        data:{},
        success: function( data )
        {
            $('#tira-admin-reload-data-icon').html(' <i class="fas fa-check"></i>')
        }
    })
}

function addTiraAdminHandlers() {
    $('#tira-admin-reload-data').click(function() {reloadData()})
}

