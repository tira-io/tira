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