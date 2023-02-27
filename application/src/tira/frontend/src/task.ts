import NotificationBar from './components/elements/notification-bar.vue'
import Leaderboard from './components/runs/leaderboard.vue'
import ReviewAccordion from './components/elements/review-accordion.vue'
import EditTask from './components/data-edit-forms/edit-task.vue'
import EditDataset from './components/data-edit-forms/edit-dataset.vue'
import AddDataset from './components/data-edit-forms/add-dataset.vue'
import ImportDataset from './components/data-edit-forms/import-dataset.vue'
import RegisterButton from './components/participant-management/register-button.vue'

import Vue from 'vue'
import {createApp} from 'vue'
import UIkit from 'uikit'
// Fontawesome Icons
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { faCheck, faTimes, faUserSlash, faUsers, faUsersSlash, faLevelUpAlt, faUser, faSearch, faDownload, faSave,
    faTrashAlt, faCog, faPlus, faSort, faSortUp, faSortDown, faSortAmountUp, faSortAlphaUp,
    faSortNumericUp, faSortAmountDown, faSortAlphaDown, faSortNumericDown, faEye, faEyeSlash, faSignInAlt, faFileImport } from '@fortawesome/free-solid-svg-icons'

library.add(faCheck, faTimes, faUserSlash, faUsers, faUsersSlash, faLevelUpAlt, faUser, faSearch, faDownload, faSave,
    faTrashAlt, faCog, faPlus, faSort, faSortUp, faSortDown, faSortAmountUp, faSortAlphaUp,
    faSortNumericUp, faSortAmountDown, faSortAlphaDown, faSortNumericDown, faEye, faEyeSlash, faSignInAlt, faFileImport)

// CSS
require('../../static/tira/css/tira-style.css');

const app = createApp({
    data() {
        return {
            task_id: "",
            userId: '',
            userVmsForTask: [],
            taskName: "",
            organizerName: "",
            website: "",
            taskDescription: "",
            datasets: {},
            test_ids: "",
            training_ids: "",
            role: '',
            evaluations: {},
            vms: {},
            notifications: [],
            remainingTeamNames: [],
            loading: false,
            selected: "",
            hide_private: true,
            hide_reviewed: false,
            editTaskToggle: false,
            editDatasetToggle: false,
            addDatasetToggle: false,
            importDatasetToggle: false,
            userIsRegistered: false,
            requireRegistration: false,
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        Leaderboard, ReviewAccordion, NotificationBar, EditTask, EditDataset, AddDataset, ImportDataset, RegisterButton
    },
    methods: {
        async get(url) {
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 1) {
                throw new Error(`${results.message}`);
            }
            return results
        },
        addNotification(type, message) {
            this.notifications.push({'type': type, 'message': message})
        },
        updateUserVmsForTask(newUserVm) {
            this.userVmsForTask = [newUserVm]
            this.userIsRegistered = true
        },
        deleteDataset(dsId) {
            this.editDatasetToggle = false
            delete this.datasets[dsId]
            this.selected = ""
        },
        addDataset(dataset) {
            this.datasets[dataset.dataset_id] = dataset
            this.selected = dataset.dataset_id
            this.addDatasetToggle = false
            this.editDatasetToggle = true
        },
        updateTask(message) {
            let modal = document.getElementById('task-edit-modal')
            UIkit.modal(modal).hide();
            this.taskName = message.task_name
            this.organizerName = message.organizer
            this.website = message.web
            this.taskDescription = message.task_description
        },
        get_nav_item(dsid) {
            let title = this.datasets[dsid].dataset_id
            if (this.datasets[dsid].display_name !== "") {
                title = this.datasets[dsid].display_name
            }
            return `${title} (<span class="uk-text-bold">${this.datasets[dsid]["runs_count"]}</span> Runs)`
        },
        closeModal() {
            const registerModal = document.getElementById('modal-register')
            UIkit.modal(registerModal).hide();
        },
        async getEvaluations(selected) {
            try {
                const res = await fetch(`/api/evaluations/${this.task_id}/${this.selected}`)
                let ev = await res.json()
                this.evaluations[selected] = {
                    "ev_keys": ev.context.ev_keys,
                    "evaluations": ev.context.evaluations
                }
            } catch (error) {
                console.log(error)
            }
        },
        async getSubmissions(selected) {
            try {
                const res = await fetch(`/api/submissions/${this.task_id}/${this.selected}`)
                let ev = await res.json()
                this.vms[selected] = ev.context.vms
            } catch (error) {
            }
        },
        setSelected(dsId) {
            this.selected = dsId
            let dropdown = document.getElementById('dropdownDatasetSelector')
            UIkit.dropdown(dropdown).hide(false)
        }
    },
    computed: {
        get_selected() {
            if (this.selected === "") {
                return "Select a Dataset"
            }
            if (this.datasets[this.selected].display_name !== "") {
                return this.datasets[this.selected].display_name
            }
            return this.selected
        },
    },  // for values that should be computed when accessed
    watch: {
        selected(newSelected, oldSelected) {
            if (!(newSelected in this.evaluations)) {
                this.getEvaluations(newSelected)
                if (this.role === 'admin') {
                    this.getSubmissions(newSelected)
                }

            }
        },
        website(newWebsite, oldWebsite) {
            if (!(newWebsite.startsWith('http://') || newWebsite.startsWith('https://'))) {
                this.website = `https://${newWebsite}`
            }
        },
    },
    beforeMount() {
        const url_split = window.location.toString().split('/')
        this.task_id = url_split[url_split.length - 1]
        this.get(`/api/task/${this.task_id}`).then(message => {
            this.userId = message.context.user_id
            this.userVmsForTask = message.context.user_vms_for_task
            this.taskName = message.context.task.task_name
            this.organizerName = message.context.task.organizer
            this.website = message.context.task.web
            this.taskDescription = message.context.task.task_description
            this.requireRegistration = message.context.task.require_registration
            this.userIsRegistered = message.context.user_is_registered
            this.remainingTeamNames = message.context.remaining_team_names
            console.log('user ', this.userId, ' is registered ( ', this.userIsRegistered, ' ). The task requires registration ( ', this.requireRegistration, ' ) and has vms: ', this.userVmsForTask)
        }).catch(error => {
            this.addNotification('error', error)
        })
        this.get(`/api/datasets_by_task/${this.task_id}`).then(message => {
            this.datasets = JSON.parse(message.context.datasets)
            this.test_ids = JSON.parse(message.context.test_dataset_ids)
            this.training_ids = JSON.parse(message.context.training_dataset_ids)
            this.selected_dataset_id = message.context.selected_dataset_id
            if (this.selected !== "") {
                this.getEvaluations(this.selected)
                if (this.role === 'admin') {
                    this.getSubmissions(this.selected)
                }
            } else {
                function newer(a: object, b: object): object {
                    const aSplits = a['created'].split("-")
                    const bSplits = b['created'].split("-")
                    if (parseInt(aSplits[0]) > parseInt(bSplits[0]) ||
                        (parseInt(aSplits[0]) === parseInt(bSplits[0]) && parseInt(aSplits[1]) > parseInt(bSplits[1])) ||
                        (parseInt(aSplits[0]) === parseInt(bSplits[0]) && parseInt(aSplits[1]) === parseInt(bSplits[1]) && parseInt(aSplits[2]) > parseInt(bSplits[2]))) {
                        return a
                    }
                    return b
                }
                let newest: unknown = Object.values(this.datasets).reduce(function(prev, curr) {
                        return newer((prev as object), (curr as object))
                    }
                )
                this.selected = (newest as object)['dataset_id']
            }
        }).catch(error => {
            this.addNotification('error', error)
        })
        
        if (this.role === '') {
            this.role = 'fetching...'
            console.log('Fetch API-ROLE')
            this.get('/api/role').then(message => {
                this.role = message.role
            }).catch(error => {
                this.role = ''
                this.addNotification('error', error)
            })
        }
    },
})
app.component('font-awesome-icon', FontAwesomeIcon)

app.config.compilerOptions.delimiters = ['[[', ']]']
app.mount("#vue-task-mount")
