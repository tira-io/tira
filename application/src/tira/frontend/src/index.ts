import NotificationBar from './components/notificationbar.vue'
import AddTask from './components/addtask.vue'
import EditOrganization from './components/editorganization.vue'

import {createApp} from 'vue';
import UIkit from 'uikit';

const app = createApp({
    data() {
        return {
            notifications: [],
            role: '{{ role|safe }}',
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        AddTask, EditOrganization, NotificationBar
    },
    methods: {
        addNotification(type, message) {
            this.notifications.push({'type': type, 'message': message})
        },
        closeModal() {
            const addTaskModal = document.getElementById('add-task-modal')
            UIkit.modal(addTaskModal).hide();
            const editorganizationModal = document.getElementById('edit-organization-modal')
            UIkit.modal(editorganizationModal).hide();
        },
    }
})

app.mount("#vue-index-mount");
