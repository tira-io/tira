export default {
    data() {
        return {
            taskError: '',
            taskNameInput: '',
            selectedOrganizer: '',
            websiteInput: '',
            masterVmId: '',
            taskDescription: '',
            helpCommand: '',
            helpText: '',
            organizerList: [],
        }
    },
    emits: ['addnotification', 'updatetask'],
    props: ['csrf', 'task_id'],
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
        async submitPost(url, params) {
            const headers = new Headers({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrf})

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
        },
        deleteTask() {
            this.get(`/tira-admin/delete-task/${this.task_id}`).then(message => {
                window.location.replace("/");
            }).catch(error => {
                this.$emit('addnotification', 'error', error)
            })
        },
        saveTask() {
            this.taskError = ''
            if (this.selectedOrganizer === '') {
                this.taskError += 'Please select an Organizer;\n'
            }
            if (this.taskNameInput === '') {
                this.taskError += 'Please provide a name for your task;\n'
            }
            if (this.masterVmId === '') {
                this.taskError += 'Please provide a master vm;\n'
            }
            if (this.taskDescription === '') {
                this.taskError += 'Please provide a description for you task;\n'
            }
            if (this.taskError !== '') {
                return
            }
            this.submitPost(`/tira-admin/edit-task/${this.task_id}`, {
                'name': this.taskNameInput,
                'master_vm_id': this.masterVmId,
                'organizer': this.selectedOrganizer.organizer_id,
                'website': this.websiteInput,
                'description': this.taskDescription,
                'help_text': this.helpText,
                'help_command': this.helpCommand,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
                this.$emit('updatetask', JSON.parse(message.context))
            }).catch(error => {
                this.$emit('addnotification', 'error', error)
                this.taskError = error
            })
        },
        getOrganizerByName(name){
            for (const org of this.organizerList) {
                if (org.name === name){
                    return org
                }
            }
            return {}
        }
    },
    watch: {
        websiteInput(newWebsite, oldWebsite) {
            if (!(newWebsite.startsWith('http://') || newWebsite.startsWith('https://'))) {
                this.websiteInput = `https://${newWebsite}`
            }
        }
    },
    beforeMount() {
        this.get(`/api/organizer-list`).then(message => {
            this.organizerList = message.context.organizer_list
            this.get(`/api/task/${this.task_id}`).then(message => {
                let task = message.context.task
                this.taskNameInput = task.task_name
                this.websiteInput = task.web
                this.masterVmId = task.master_vm_id
                this.selectedOrganizer = this.getOrganizerByName(task.organizer)
                this.taskDescription = task.task_description
                this.helpCommand = task.command_placeholder
                this.helpText = task.command_description
            }).catch(error => {
                this.$emit('addnotification', 'error', `Error loading task: ${error}`)
            })
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading organizer list: ${error}`)
        })
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Edit Task <span class="uk-text-lead uk-text-muted">ID: [[ this.task_id ]]</span></h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label>Task Name*
            <input class="uk-input" type="text" placeholder="Name of the Task"
                   :class="{'uk-form-danger': (this.taskError !== '' && this.taskNameInput === '')}"
                   v-model="taskNameInput" /></label>
        </div>
        <div class="uk-width-1-3">
            <label>Organizer*
            <select id="host-select" class="uk-select" v-model="this.selectedOrganizer"
                   :class="{'uk-form-danger': (this.taskError !== '' && this.selectedOrganizer === '')}">
                <option disabled value="">Please select an organizer</option>
                <option v-for="organizer in this.organizerList" :value="organizer">[[ organizer.name ]]</option>
            </select></label>
        </div>
        <div class="uk-width-1-3">
            <label>Website
            <input id="website-input" class="uk-input" type="text" placeholder="Website URL"
                   v-model="websiteInput" /></label>
        </div>
    </div>
    <div class="uk-margin-small">
        <label>Master VM ID*
        <input type="text" class="uk-input" v-model="masterVmId" /></label>
    </div>
    <div class="uk-margin-small">
        <label>Task Description*
        <textarea id="task-description-input" rows="3" class="uk-textarea" placeholder="Task Description"
               :class="{'uk-form-danger': (this.taskError !== '' && this.taskDescription === '')}"
               v-model="taskDescription" /> </label>
    </div>
    <div class="uk-margin-small">
        <label> Help Command
        <input type="text" class="uk-input" placeholder="mySoftware -c $inputDataset -r $inputRun -o $outputDir"
               v-model="helpCommand" /></label>
    </div>
    <div class="uk-margin-small">
        <label> Help Text<textarea rows="6" class="uk-textarea" placeholder="Available variables: \n<code>$inputDataset</code>, \n<code>$inputRun</code>, \n<code>$outputDir</code>, \n<code>$dataServer</code>, and \n<code>$token</code>."
               v-model="helpText" /></label>
    </div>
    <div class="uk-margin-small uk-grid-collapse" uk-grid>
        <div class="uk-width-expand">
            <span class="uk-text-danger uk-margin-small-left">[[ this.taskError ]]</span>
        </div>
        <div>
            <button class="uk-button uk-button-primary" @click="saveTask">Save</button>
            <button class="uk-button uk-button-danger" @click="deleteTask">Delete Task</button>
        </div>
    </div>
</div>`
}