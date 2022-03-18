export default {
    data() {
        return {
            taskError: '',
            taskNameInput: '',
            masterVmInput: '',
            selectedOrganizer: '',
            websiteInput: '',
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
                this.taskError += 'Please provide an id for the new VM;\n'
            }
            if (this.taskDescription === '') {
                this.taskError += 'Please provide a description for you task;\n'
            }
            if (this.taskError !== '') {
                return
            }
            this.submitPost('/tira-admin/edit-task', {
                'task_id': this.task_id,
                'name': this.taskNameInput,
                'master_id': this.masterVmInput,
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
    beforeMount() {
        this.get(`/api/organizer-list`).then(message => {
            this.organizerList = message.context.organizer_list
            this.get(`/api/task/${this.task_id}`).then(message => {
                let task = message.context.task
                this.taskNameInput = task.task_name
                this.websiteInput = task.web
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
        <h2>Edit Task</h2>
    </div>
</div>
<div class="uk-margin-small">
    Task ID: [[ this.task_id ]]
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-4">
            <label for="task-name-input">Task Name</label>
            <input id="task-name-input" class="uk-input" type="text" placeholder="Name of the Task"
                   :class="{'uk-form-danger': (this.taskError !== '' && this.taskNameInput === '')}"
                   v-model="taskNameInput">
        </div>
        <div class="uk-width-1-4">
            <label for="master-vm-input">Master VM</label>
            <input id="master-vm-input" class="uk-input" type="text" placeholder="id-lowercase-with-dashes"
                   v-model="masterVmInput">
        </div>
        <div class="uk-width-1-4">
            <label for="host-select">Organizer</label>
            <select id="host-select" class="uk-select" v-model="this.selectedOrganizer"
                   :class="{'uk-form-danger': (this.taskError !== '' && this.selectedOrganizer === '')}">
                <option disabled value="">Please select an organizer</option>
                <option v-for="organizer in this.organizerList" :value="organizer">[[ organizer.name ]]</option>
            </select>
        </div>
        <div class="uk-width-1-4">
            <label for="website-input">Website</label>
            <input id="website-input" class="uk-input" type="text" placeholder="Website URL"
                   v-model="websiteInput">
        </div>
    </div>
    <div class="uk-margin-small">
        <label for="task-description-input">Task Description*</label>
        <textarea id="task-description-input" rows="3" class="uk-textarea" placeholder="Task Description"
               :class="{'uk-form-danger': (this.taskError !== '' && this.taskDescription === '')}"
               v-model="taskDescription" />
    </div>
    <div class="uk-margin-small">
        <label for="help-command-input">Help Command</label>
        <input id="help-command-input" type="text" class="uk-input" placeholder="mySoftware -c $inputDataset -r $inputRun -o $outputDir"
               v-model="helpCommand" />
    </div>
    <div class="uk-margin-small">
        <label for="help-text-input">Help Text</label>
        <textarea id="help-text-input" rows="6" class="uk-textarea" placeholder="Available variables: \n<code>$inputDataset</code>, \n<code>$inputRun</code>, \n<code>$outputDir</code>, \n<code>$dataServer</code>, and \n<code>$token</code>."
               v-model="helpText" />
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