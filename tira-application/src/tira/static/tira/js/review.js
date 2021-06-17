let vm_id = null;
let dataset_id = null;
let run_id = null;

// change view when blind state changes
function setBlindButton(blinded){
    if ( blinded === false ) {
        $('#blind-button').show()
        $('#blind-text').show()
        $('#unblind-button').hide()
        $('#unblind-text').hide()
    } else {
        $('#blind-button').hide()
        $('#blind-text').hide()
        $('#unblind-button').show()
        $('#unblind-text').show()
    }
}

// change view when published state changes
function setPublishButton(published){
    if ( published === true ) {
        $('#publish-button').hide();
        $('#publish-text').hide();
        $('#unpublish-button').show();
        $('#unpublish-text').show();
    } else {
        $('#publish-button').show();
        $('#publish-text').show();
        $('#unpublish-button').hide();
        $('#unpublish-text').hide();
    }
}

// when publish state changes: notify server and update view if successful
function publish(bool) {
    $.ajax({
        type:"GET",
        url: "/publish/" + vm_id + "/" + dataset_id + "/" + run_id + "/" + bool,
        data: {},
        success: function( data )
        {
            if(data.status === "success"){
                setPublishButton(data.published)
            }
        }
    })
}

// when blind state changes: notify server and update view if successful
function blind(bool) {
    $.ajax({
        type:"GET",
        url: "/blind/" + vm_id + "/" + dataset_id + "/" + run_id + "/" + bool,
        data:{},
        success: function( data )
        {
            if(data.status === "success"){
                setBlindButton(data.blinded)
            }
        }
    })
}

/* Init state and events for this page
*  - initial state of blind, publish, and review
*  - events for publishing and blinding
*  - events to uncheck checkboxes
*/
function addReviewEvents(p, b, vid, did, rid) {
    vm_id = vid;
    dataset_id =did;
    run_id = rid;
    p = p !== "False";  // Convert booleans to JS style
    b = b !== "False";
    setPublishButton(p)
    setBlindButton(b)

    $('#blind-button').click(function () {
        blind(true)
    })
    $('#unblind-button').click(function () {
        blind(false)
    })
    $('#publish-button').click(function () {
        publish(true)
    })
    $('#unpublish-button').click(function () {
        publish(false)
    })
    $('#no-error-checkbox').change(function () {
        if(this.checked) {
            $('#software-error-checkbox').prop('checked', false);
            $('#output-error-checkbox').prop('checked', false);
        }
    })
    $('#software-error-checkbox').change(function () {
        if(this.checked) {
            $('#no-error-checkbox').prop('checked', false);
        }
    })
    $('#output-error-checkbox').change(function () {
        if(this.checked) {
            $('#no-error-checkbox').prop('checked', false);
        }
    })
}