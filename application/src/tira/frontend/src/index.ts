import NotificationBar from './components/elements/notification-bar.vue'
import AddTask from './components/data-edit-forms/add-task.vue'
import EditOrganization from './components/data-edit-forms/edit-organization.vue'

import {createApp} from 'vue';
import UIkit from 'uikit';

// CSS
require('../../static/tira/css/tira-style.css');

const app = createApp({
    data() {
        return {
            notifications: [],
            role: '',
            organizerTeams: [],
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        AddTask, EditOrganization, NotificationBar
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
        closeModal() {
            const addTaskModal = document.getElementById('add-task-modal')
            UIkit.modal(addTaskModal).hide();
            const editorganizationModal = document.getElementById('edit-organization-modal')
            UIkit.modal(editorganizationModal).hide();
        },
    },
    beforeMount() {
       this.get(`/api/role`).then(message => {
           this.role = message.role
           this.organizerTeams = message.organizer_teams
       }).catch(error => {
           this.addNotification('error', error)
       })
    },
})

app.mount("#vue-index-mount");
