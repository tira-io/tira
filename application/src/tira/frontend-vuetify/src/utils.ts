import { ref } from 'vue'

let allowed_roles = new Set(['guest', 'user', 'participant', 'admin'])

export function extractTaskFromCurrentUrl() {
    let loc = ref(window.location).value.href.split('#')[0].split('?')[0]
    
    if (loc.includes('task-overview/')) {
        return loc.split('task-overview/')[1].split('/')[0]
    }
    else if(loc.includes('submit/')) {
        return loc.split('submit/')[1].split('/')[0]
    }

    return null;
}

export function get_link_to_organizer(organizer_id: string) {
    return 'https://www.tira.io/g/tira_org_' + organizer_id;
}

export function get_contact_link_to_organizer(organizer_id: string) {
    return 'https://www.tira.io/new-message?username=tira_org_' + organizer_id + '&title=Request%20&body=message%20body'
}

export function extractDatasetFromCurrentUrl(options: Array<any> = [], default_choice: string='') {
    var loc = ref(window.location).value.href.split('#')[0].split('?')[0]
    var dataset_from_url = ''
    let to_split = 'task-overview/' + extractTaskFromCurrentUrl() + '/'
    
    if (loc.includes(to_split)) {
        dataset_from_url = loc.split(to_split)[1].split('/')[0]
    }

    if (options.length === 0) {
        return dataset_from_url
    }

    if (default_choice !== '') {
        for (var dataset of options) {
            if (default_choice === dataset['dataset_id']) {
                return dataset['dataset_id']
            }
        }
    }

    var ret = ''

    for (var dataset of options) {
        if ((dataset_from_url !== '' && dataset_from_url === dataset['dataset_id']) || ret === '') {
            ret = dataset['dataset_id']
        }
    }

    return ret
}

export function extractUserFromCurrentUrl() {
        let url = ref(window.location).value.href
        let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/'
        let user = ''
        if(url.includes(to_split)) {
            user = url.split(to_split)[1].split('/')[0]
        }
        return user
}
export function extractSubmissionTypeFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/' + extractUserFromCurrentUrl() + '/'
    let submission_type = null

    if(url.includes(to_split)) {
        submission_type = url.split(to_split)[1].split('/')[0]
    }
    console.log(submission_type)
    return submission_type === '' ? null : submission_type
}
export function extractCurrentStepFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/' + extractUserFromCurrentUrl() + '/' + extractSubmissionTypeFromCurrentUrl()
    let step = null
    if(url.includes(to_split)) {
        step = url.split(to_split)[1].split('/')[1] === undefined ? null : url.split(to_split)[1].split('/')[1]
    }
    return step === '' ? null : step
}

export function changeCurrentUrlToDataset(dataset: string) {
    var loc = ref(window.location).value.href

    if (loc.includes('task-overview/')) {
        loc = loc.split('task-overview/')[0] + 'task-overview/' + loc.split('task-overview/')[1].split('/')[0] + '/' + dataset
        history.replaceState({'url': loc}, 'TIRA', loc)
    }
}

export function extractRole(doc: Document=document) : string {
    try {
        var ret = doc.querySelector('#user_metadata')
        if (ret) {
            ret = JSON.parse(ret.innerHTML.split('user_metadata = ')[1])['role']
            if (allowed_roles.has("" + ret)) {
                return "" + ret
            }
        }
    } catch { }
    
    return 'guest'
}

export function reportError(title: string="", text: string="") {
    return function (error: any) {
        console.log(error)
        if (title === '') {
            title = 'Error.'
        }
        window.push_message(title, text + ' ' + error, "error")
    }
}

export function inject_response(obj: any, default_values: any={}, debug=false) {
    let object_to_inject_data = obj.$data
    return function(message: any) {
      let available_keys = new Set<string>(Object.keys(message['context']))

      for (var key of Object.keys(object_to_inject_data)) {
        if (available_keys.has(key)) {
          object_to_inject_data[key] = message['context'][key]
        }
      }

      for (var key of Object.keys(default_values)) {
        object_to_inject_data[key] = default_values[key]
      }

      if (debug) {
        console.log(object_to_inject_data)
      }
    }
}

async function submitPost(url: string, params: [string: any]) {
    const csrf = ''
    const headers = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
    })
    console.log(JSON.stringify(params))
    const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(params)
    })
    if (!response.ok) {
        throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status === 1) {
        throw new Error(`${results.message}`);
    }
    return results
}

export async function get(url: string) {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status !== 0) {
      throw new Error(`${results.message}`);
    }
    return results
}
