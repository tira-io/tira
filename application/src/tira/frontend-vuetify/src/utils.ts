import { ref } from 'vue'

let allowed_roles = new Set(['guest', 'user', 'participant', 'admin'])

export function extractTaskFromCurrentUrl() {
    let loc = ref(window.location).value.href.split('#')[0].split('?')[0]
    
    if (loc.includes('task-overview/')) {
        return loc.split('task-overview/')[1].split('/')[0]
    } if (loc.includes('task/')) {
        return loc.split('task/')[1].split('/')[0]
    }
    else if (loc.includes('submit/')){
        return loc.split('submit/')[1].split('/')[0]
    }

    return null;
}

export const slugify = (str: string) => {
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

export function extractOrganizations(doc: Document=document): Array<string> {
    try {
        var ret = doc.querySelector('#user_metadata')
        if (ret) {
            return JSON.parse(ret.innerHTML.split('user_metadata = ')[1])['organizer_teams']
        }
    } catch { }
    
    return []
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
        if (title === '') {
            title = 'Success.'
        }
        if ('' + error !== 'undefined' && '' + error !== 'null' && error['message'] + '' !== 'undefined' && error['message'] + '' !== 'null') {
            text = text + ' ' + error['message']
        } else if ('' + error !== 'undefined' && '' + error !== 'null' && JSON.stringify(error) !== '{"status":0}') {
            text = text + ' ' + error
        }

        window.push_message(title, text, "success")

        return error
    }
}

export function reportError(title: string="", text: string="") {
    return function (error: any) {
        if (title === '') {
            title = 'Error.'
        }
        window.push_message(title, text + ' ' + error, "error")

        return error
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

export function compareArrays (a : string[] | null, b : string[] | null) : boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function extractComponentTypesFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'components/'
    let component_types = null
    let component_types_array : string[] | [] = []


    if(url.includes(to_split)) {
        component_types = url.split(to_split)[1].split('/')[0].toLowerCase()

        if(component_types !== null && component_types.includes(',')) {
            component_types_array = component_types.split(',')
        }
        else {
           component_types_array = [component_types]
        }
        for(let i = 0; i < component_types_array.length; i++) {
                component_types_array[i] = component_types_array[i].charAt(0).toUpperCase() + component_types_array[i].slice(1)
                component_types_array[i] = component_types_array[i].replace( /tirex/i, 'TIREx')
            }
    }
    return compareArrays(component_types_array, []) || compareArrays(component_types_array, [''])? [] : component_types_array
}

export function extractFocusTypesFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split : string = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/'
    let focus_type = null
    let focus_types_array : string[] | [] = []

    if(url.includes(to_split)) {
        focus_type = url.split(to_split)[1].split('/')[0].toLowerCase()
       if(focus_type !== null && focus_type.includes(',')) {
            focus_types_array = focus_type.split(',')
        }
        else {
           focus_types_array = [focus_type]
        }
     for(let i = 0; i < focus_types_array.length; i++) {
                focus_types_array[i] = focus_types_array[i].charAt(0).toUpperCase() + focus_types_array[i].slice(1)
            }
    }
    return compareArrays(focus_types_array, []) || compareArrays(focus_types_array, ['']) ? [] : focus_types_array
}

export function extractSearchQueryFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/' + extractFocusTypesFromCurrentUrl().join() + '/'
    let search_query = ''
    if(url.includes(to_split)) {
       search_query = url.split(to_split)[1].split('/')[0]
    }
    if(search_query !== null && search_query.includes("%20")) {
        search_query = search_query.replaceAll("%20", " ")
    }
    return search_query ? search_query.toLowerCase() : search_query
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

export function inject_response(obj: any, default_values: any={}, debug=false, subpaths: string|Array<string>='') {
    let object_to_inject_data = obj.$data
    return function(message: any) {
      subpaths = Array.isArray(subpaths) ? subpaths : [subpaths]

      for (var subpath of subpaths) {
        if (debug) {
         console.log('Process ' + subpath)
        }

        if (subpath !== '' && !message['context'].hasOwnProperty(subpath)) {
          continue
        }

        let obj = subpath === '' ? message['context'] : message['context'][subpath]
        let available_keys = new Set<string>(Object.keys(obj))

        if (debug) {
          console.log(available_keys)
        }

        for (var key of Object.keys(object_to_inject_data)) {
          if (available_keys.has(key)) {
            object_to_inject_data[key] = obj[key]
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

    return post_raw(url, headers, params, debug)
}

export async function post_file(url: string, params: any, debug=false) {
    const headers = new Headers({
        'Accept': 'application/json',
        'X-CSRFToken': extractCsrf(),
    })

    return post_raw(url, headers, params, debug)
}

export async function post_raw(url: string, headers: any, params: any, debug=false) {
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
    } else if (value?.length > 30) {
        return 'Team name must be less than 30 characters.'
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

export function handleModifiedSubmission(modified_data: any, objects: Array<any>){
    for (let i of objects){
        if(i.hasOwnProperty('docker_software_id') && i['docker_software_id'] === modified_data['id']){
            i['display_name'] = modified_data['display_name']
        }
         if(!i.hasOwnProperty('docker_software_id') && i['id'] === modified_data['id']){
            i['display_name'] = modified_data['display_name']
        }
    }

    return objects
}