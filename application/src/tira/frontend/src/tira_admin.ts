import NotificationBar from './components/notificationbar.vue'
import CreateVm from './components/createvm.vue'
import AddTask from './components/addtask.vue'
import AddDataset from './components/adddataset.vue'
import ModifyVm from './components/modifyvm.vue'

import {createApp} from 'vue'

const app = createApp({
    data() {
        return {
            role: '{{ role|safe }}',
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
    watch: {},
    computed: {},  // for values that should be computed when accessed
})
app.mount("#tira-admin-mount")


