import NotificationBar from './components/notificationbar.vue'
import Leaderboard from './components/leaderboard.vue'
import ReviewList from './components/reviewlist.vue'
import EditTask from './components/edittask.vue'
import EditDataset from './components/editdataset.vue'
import AddDataset from './components/adddataset.vue'

import {createApp} from 'vue'
import UIkit from 'uikit'

const app = createApp({
    data() {
        return {
            task_id: "{{ task.task_id|safe }}",
            taskName: "{{ task.task_name|safe }}",
            organizerName: "{{ task.organizer|safe }}",
            website: "{{ task.web|safe }}",
            taskDescription: "{{ task.task_description|safe }}",
            datasets: JSON.parse('{{ datasets|safe }}'),
            test_ids: JSON.parse('{{ test_dataset_ids|safe }}'),
            training_ids: JSON.parse('{{ training_dataset_ids|safe }}'),
            role: '{{ role|safe }}',
            evaluations: {},
            vms: {},
            notifications: [],
            loading: false,
            selected: "{{ selected_dataset_id }}",
            hide_private: true,
            hide_reviewed: true,
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        Leaderboard, ReviewList, NotificationBar, EditTask, EditDataset, AddDataset
    },
    methods: {
        addNotification(type, message) {
            this.notifications.push({'type': type, 'message': message})
        },
        closeModal() {
            UIkit.modal(document.getElementById('add-dataset-modal')).hide();
            UIkit.modal(document.getElementById('edit-dataset-modal')).hide();
        },
        deleteDataset(dsId) {
            this.selected = ""
            delete this.datasets[dsId]
        },
        addDataset(dataset) {
            console.log(dataset)
            this.datasets[dataset.dataset_id] = dataset
            this.selected = dataset.dataset_id
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
            return `${title} (<span class="uk-text-bold">${this.datasets[dsid]["software_count"]}</span> Softwares)`
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
        }
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
        }
    },
    beforeMount() {
        if (this.selected !== "") {
            this.getEvaluations(this.selected)
            if (this.role === 'admin') {
                this.getSubmissions(this.selected)
            }
        }
    },
})
app.mount("#vue-task-mount")
