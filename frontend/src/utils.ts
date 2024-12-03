import { inject, ref } from 'vue'

export interface TaskInfo {
    task_name: string;
}

export interface DatasetInfo {
    dataset_id: string;
    id: string;
    ir_datasets_id: string | undefined | string[];
    chatnoir_id: string | undefined;
    is_confidential: boolean;
    display_name: string;
    default_task: string | undefined;
    default_task_name: string | undefined;
    mirrors: Record<string, string>;
}

export interface UploadGroupInfo {
    id: string;
    display_name: string
}

export interface ClaimSubmissionInfo {
    uuid: string;
    dataset_id: string;
    created: string;
}

export interface UserContext {
    user_id: string;
}

export interface UserInfo {
    role: string;
    organizer_teams: Object[];
    context: UserContext;
    csrf: string;
}

export interface SystemInfo {
    name: string;
    team: string;
    tasks: string;
}


export interface ServerInfo {
    version: string;
    restApiVersion: string;
    publicSystemCount: number;
    datasetCount: number;
    taskCount: number;
    supportedFormats: string[];
}

export interface WellKnownAPI {
    api: string;
    grpc: string;
    archived: string;
    login: string;
    logout: string;
    notifications: string;
    disraptorURL: string;
}

export function irDatasetsUrls(dataset: DatasetInfo | undefined): Record<string, string> {
    if (!dataset || !dataset.ir_datasets_id) {
        return {}
    }

    let dataset_ids: string[] = []

    if (typeof (dataset.ir_datasets_id) == 'string') {
        dataset_ids = [dataset.ir_datasets_id]
    } else {
        dataset_ids = dataset.ir_datasets_id
    }

    let ret: Record<string, string> = {}
    for (let ir_dataset_id of dataset_ids) {
        ret[ir_dataset_id] = 'https://ir-datasets.com/' + ir_dataset_id.split('/')[0] + '.html#' + ir_dataset_id
    }

    return ret
}

export function chatNoirUrl(dataset: DatasetInfo | undefined, document_id: string | undefined = undefined) {
    if (!dataset || !dataset.chatnoir_id) {
        return undefined
    } else if (document_id) {
        return 'https://chatnoir-webcontent.web.webis.de/?index=' + dataset.chatnoir_id + '&trec-id=' + document_id
    }
    else {
        return 'https://chatnoir.web.webis.de/?index=' + dataset.chatnoir_id
    }
}

export function extractTaskFromCurrentUrl() {
    let loc = ref(window.location).value.href.split('#')[0].split('?')[0]

    if (loc.includes('task-overview/')) {
        return loc.split('task-overview/')[1].split('/')[0]
    } if (loc.includes('task/')) {
        return loc.split('task/')[1].split('/')[0]
    }
    else if (loc.includes('submit/')) {
        return loc.split('submit/')[1].split('/')[0]
    }

    return null;
}

export const slugify = (str: string) => {
    str = str.replace(/^\s+|\s+$/g, ''); // trim
    str = str.toLowerCase();

    // remove accents, swap ñ for n, etc
    var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
    var to = "aaaaeeeeiiiioooouuuunc------";
    for (var i = 0, l = from.length; i < l; i++) {
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

export function extractDatasetFromCurrentUrl(options: Array<any> = [], default_choice: string = '') {
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

export async function fetchServerInfo(endpoint: string): Promise<ServerInfo> {
    const response = await fetch(endpoint + '/info')

    let result: ServerInfo = await response.json()
    return result
}

export async function api_csrf_token(): Promise<string> {
    let headers = new Headers({ 'Accept': 'application/json' })
    const response = await fetch(inject("REST base URL") + 'session/csrf', { headers, credentials: 'include' })
    return (await response.json()).csrf

}

export async function logout(username: string): Promise<Boolean> {
    let endpoints = await fetchWellKnownAPIs()
    let csrf_token = await api_csrf_token()

    const headers = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
    })
    console.log(csrf_token)
    console.log(document.cookie)
    console.log(await fetch(endpoints.logout + 'session/' + username, { headers, credentials: 'include', method: 'DELETE' }))
    return Promise.resolve(true)
}

export async function fetchUserInfo(endpoint: string): Promise<UserInfo> {
    try {
        const response = await fetch(endpoint + '/api/role', { credentials: 'include' })
        // TODO: better error handling (to be implemented with the new REST API with problem+json; and the overhauled UI)
        if (!response.ok) {
            return Promise.resolve({ role: 'guest', organizer_teams: [], csrf: '', context: { user_id: 'guest' } } as UserInfo)
        }
        // TODO: maybe check here if the response json is actually valid
        return Promise.resolve(await response.json() as UserInfo)
    } catch (Exception) {
        return Promise.resolve({ role: 'guest', organizer_teams: [], csrf: '', context: { user_id: 'guest' } } as UserInfo)
    }
}

export async function fetchWellKnownAPIs(endpoint: string | undefined = undefined): Promise<WellKnownAPI> {
    const url = endpoint ? endpoint : ''
    const response = await fetch(url + '/.well-known/tira/client')

    let _well_known = await response.json() as WellKnownAPI
    return Promise.resolve(_well_known)
}

export function reportSuccess(title: string = "", text: string = "") {
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

export function reportError(title: string = "", text: string = "") {
    return function (error: any) {
        if (title === '') {
            title = 'Error.'
        }
        window.push_message(title, text + ' ' + error, "error")
        console.log(error)

        return error
    }
}

export function vm_id(vm_ids: any, vm: any, user_vms_for_task: any, additional_vms: any, user_id: any, task: any) {
    if (!vm_ids && vm) {
        return vm
    } else if (user_vms_for_task && user_vms_for_task.length == 1) {
        return user_vms_for_task[0]
    } else if (additional_vms && additional_vms.length > 0 && additional_vms[0]) {
        return additional_vms[0]
    } else if (!vm_ids && user_id && !task.require_groups && !task.restrict_groups) {
        return user_id + '-default'
    }

    return null;
}

export function extractUserFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/'
    let user = ''
    if (url.includes(to_split)) {
        user = url.split(to_split)[1].split('/')[0]
    }
    return user
}

export function compareArrays(a: string[] | null, b: string[] | null): boolean {
    return JSON.stringify(a) === JSON.stringify(b);
}

export function extractComponentTypesFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'components/'
    let component_types = null
    let component_types_array: string[] | [] = []


    if (url.includes(to_split)) {
        component_types = url.split(to_split)[1].split('/')[0].toLowerCase()

        if (component_types !== null && component_types.includes(',')) {
            component_types_array = component_types.split(',')
        }
        else {
            component_types_array = [component_types]
        }
        for (let i = 0; i < component_types_array.length; i++) {
            component_types_array[i] = component_types_array[i].charAt(0).toUpperCase() + component_types_array[i].slice(1)
            component_types_array[i] = component_types_array[i].replace(/tirex/i, 'TIREx')
        }
    }
    return compareArrays(component_types_array, []) || compareArrays(component_types_array, ['']) ? [] : component_types_array
}

export function extractFocusTypesFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split: string = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/'
    let focus_type = null
    let focus_types_array: string[] | [] = []

    if (url.includes(to_split)) {
        focus_type = url.split(to_split)[1].split('/')[0].toLowerCase()
        if (focus_type !== null && focus_type.includes(',')) {
            focus_types_array = focus_type.split(',')
        }
        else {
            focus_types_array = [focus_type]
        }
        for (let i = 0; i < focus_types_array.length; i++) {
            focus_types_array[i] = focus_types_array[i].charAt(0).toUpperCase() + focus_types_array[i].slice(1)
        }
    }
    return compareArrays(focus_types_array, []) || compareArrays(focus_types_array, ['']) ? [] : focus_types_array
}

export function extractSearchQueryFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/' + extractFocusTypesFromCurrentUrl().join() + '/'
    let search_query = ''
    if (url.includes(to_split)) {
        search_query = url.split(to_split)[1].split('/')[0]
    }
    if (search_query !== null && search_query.includes("%20")) {
        search_query = search_query.replaceAll("%20", " ")
    }
    return search_query ? search_query.toLowerCase() : search_query
}

export function extractSoftwareIdFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/' + extractUserFromCurrentUrl() + '/'

    if (url.includes(to_split)) {
        url = url.split(to_split)[1]
    } else {
        return null
    }

    if (url.includes('upload-submission/')) {
        url = url.split('upload-submission/')[1].split('/')[0].split('?')[0].split('#')[0]
    }

    return parseInt(url) > 0 ? parseInt(url) : null
}

export function extractSubmissionTypeFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/' + extractUserFromCurrentUrl() + '/'
    let submission_type = null

    if (url.includes(to_split)) {
        submission_type = url.split(to_split)[1].split('/')[0]
    }
    return submission_type === '' ? null : submission_type
}

export function extractCurrentStepFromCurrentUrl() {
    let url = ref(window.location).value.href
    let to_split = 'submit/' + extractTaskFromCurrentUrl() + '/user/' + extractUserFromCurrentUrl() + '/' + extractSubmissionTypeFromCurrentUrl()
    let step = null
    if (url.includes(to_split)) {
        step = url.split(to_split)[1].split('/')[1] === undefined ? null : url.split(to_split)[1].split('/')[1]
    }
    return step === '' ? null : step
}

export function changeCurrentUrlToDataset(dataset: string) {
    var loc = ref(window.location).value.href

    if (loc.includes('task-overview/')) {
        loc = loc.split('task-overview/')[0] + 'task-overview/' + loc.split('task-overview/')[1].split('/')[0] + '/' + dataset
        history.replaceState({ 'url': loc }, 'TIRA', loc)
    }
}

export function inject_response(obj: any, default_values: any = {}, debug = false, subpaths: string | Array<string> = '') {
    let object_to_inject_data = obj.$data
    return function (message: any) {
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

/* TODO: credentials=true can be called the legacy behavior when frontend and backend were on the same URL. This should maybe be limited more */
export async function get(url: string, credentials = true) {
    const response = await fetch(url, { credentials: credentials ? 'include' : 'omit' })
    if (!response.ok) {
        throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
    }
    let results = await response.json()
    if (results.status !== undefined && results.status !== 0 && results.status !== '0') {
        throw new Error(`${results.message}`);
    }
    return results
}

/* TODO: credentials=true can be called the legacy behavior when frontend and backend were on the same URL. This should maybe be limited more */
export async function post(url: string, params: any, user: UserInfo, debug = false, credentials = true) {
    const headers = new Headers({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': user.csrf,
    })
    params = JSON.stringify(params)

    return post_raw(url, headers, params, debug, credentials)
}

/* TODO: credentials=true can be called the legacy behavior when frontend and backend were on the same URL. This should maybe be limited more */
export async function post_file(url: string, params: any, user: UserInfo, debug = false, credentials = true) {
    const headers = new Headers({
        'Accept': 'application/json',
        'X-CSRFToken': user.csrf,
    })

    return post_raw(url, headers, params, debug, credentials)
}

/* TODO: credentials=true can be called the legacy behavior when frontend and backend were on the same URL. This should maybe be limited more */
export async function post_raw(url: string, headers: any, params: any, debug = false, credentials = true) {
    if (debug) {
        console.log("Post " + params)
    }

    const response = await fetch(url, {
        method: "POST",
        headers,
        body: params,
        credentials: credentials ? 'include' : 'omit',
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

export function handleModifiedSubmission(modified_data: any, objects: Array<any>) {
    for (let i of objects) {
        if (i.hasOwnProperty('docker_software_id') && i['docker_software_id'] === modified_data['id']) {
            i['display_name'] = modified_data['display_name']
        }
        if (!i.hasOwnProperty('docker_software_id') && i['id'] === modified_data['id']) {
            i['display_name'] = modified_data['display_name']
        }
    }

    return objects
}
