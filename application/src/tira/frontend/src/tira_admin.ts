import NotificationBar from './components/elements/notification-bar.vue'
import CreateVm from './components/utility/createvm.vue'
import AddTask from './components/data-edit-forms/add-task.vue'
import AddDataset from './components/data-edit-forms/add-dataset.vue'
import ModifyVm from './components/utility/modifyvm.vue'

import {createApp} from 'vue'

// CSS
require('../../static/tira/css/tira-style.css');

const app = createApp({
    data() {
        return {
            role: '',
            selected: "overview",
            reloading: [],
            notifications: [],
            createGroupError: '',
            createGroupId: '',
            batchInput: '',
            csrf: (<HTMLInputElement>document.querySelector('[name=csrfmiddlewaretoken]')).value
        }
    },
    components: {
        NotificationBar, CreateVm, AddTask, AddDataset, ModifyVm
    },
    methods: {
        async apiCall(url) {
            console.log(url)
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`${await response.text()}`);
            }
            let results = await response.json()
            console.log(results)
            if (results.status === 0) {
                return results.message
            }
            throw new Error(results.message);
        },
        setSelected(sel) {
            this.selected = sel
        },
        reload(selection) {
            this.reloading.push(selection)
            this.reload = selection
            this.apiCall(`/tira-admin/reload/${selection}`).then(results => {
                this.addNotification('success', results.message)
            }).catch(error => {
                this.addNotification('error', error.message)
            }).finally(() => {
                this.reloading = this.reloading.filter(function (ele) {
                    return ele !== selection
                })
            })
        },
        addNotification(type, message) {
            this.notifications.push({'type': type, 'message': message})
        },
        createGroup() {
            // spinner
            this.apiCall(`/tira-admin/create-group/${this.createGroupId}`).then(results => {
                this.addNotification('success', results.message)
                this.createGroupId = ''
            }).catch(error => {
                this.createGroupError = error.message
            })
        },
    },
    beforeMount() {
        this.apiCall(`/api/role`).then(message => {
            this.role = message.role
        }).catch(error => {
            this.addNotification('error', error)
        })
    },
    watch: {},
    computed: {},  // for values that should be computed when accessed
})

app.config.compilerOptions.delimiters = ['[[', ']]']
app.mount("#tira-admin-mount")


