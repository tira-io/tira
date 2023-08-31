import { ref } from 'vue'

let allowed_roles = new Set(['guest', 'user', 'participant', 'admin'])

export function extractTaskFromCurrentUrl() {
    let loc = ref(window.location).value.href.split('#')[0].split('?')[0]
    
    if (loc.includes('task-overview/')) {
        return loc.split('task-overview/')[1].split('/')[0]
    }
    else if (loc.includes('submit/')){
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

export function extractSubView() {
    return extracSubViewForLevel(1)
}

export function extractSubSubView() {
    return extracSubViewForLevel(2)
}

export function extracSubViewForLevel(level: number) {
    let loc = ref(window.location).value.href.split('#')[0].split('?')[0]
    let to_split = 'task-overview/' + extractTaskFromCurrentUrl() + '/'

    if (loc.includes(to_split)) {
        let ret = loc.split(to_split)[1].split('/')
        if (ret.length >= level) {
            return ret[level]
        }
    }

    return null
}

export function chanceCurrentUrlToDataset(dataset: string) {
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

export function extractCsrf(doc: Document=document) : string {
    try  {
        var ret = doc.querySelector('input[type="hidden"][name="csrfmiddlewaretoken"][value]')
        if (ret && 'value' in ret) {
            return "" + ret['value']
        }
    } catch { }

    return ''
}

export function reportSuccess(title: string="", text: string="") {
    return function (error: any) {
        console.log(error)
        if (title === '') {
            title = 'Success.'
        }
        window.push_message(title, text + ' ' + error, "Success")
    }
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

export async function get(url: string) {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status !== 0 && results.status !== '0') {
      throw new Error(`${results.message}`);
    }
    return results
}

export async function post(url: string, params: any, debug=false) {
    const headers = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': extractCsrf(),
    })
    params = JSON.stringify(params)
    if (debug) {
        console.log("Post " + params)
    }
    const response = await fetch(url, {
        method: "POST",
        headers,
        body: params
    })
    if (debug) {
        console.log("Received " + response)
    }
    if (!response.ok) {
        throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status !== 0 && results.status !== '0') {
        throw new Error(`${results.message}`);
    }
    return results
}

export function validateEmail(value: string) {
    if (!value) {
        return 'E-mail is required.'
    } else if (/.+@.+\..+/.test(value)) {
        return true
    }

    return 'E-mail must be valid.'
}

export function validateTeamName(value: string) {
    if (!value) {
        return 'Team name is required.'
    } else if (value?.length < 3) {
        return 'Team name must have 3 or more characters.'
    } else if (value?.length > 10) {
        return 'Team name must be less than 10 characters.'
    }

    return true
}

export function validateNotEmpty(value: String) {
    if (!value) {
        return 'This field is required.'
    }

    return true
}

export function filterByDisplayName(objects: Array<any>, filter: String) {
    return objects.filter(i => !filter || (i.hasOwnProperty('display_name') && i.display_name.toLowerCase().includes(filter.toLowerCase())))
}
