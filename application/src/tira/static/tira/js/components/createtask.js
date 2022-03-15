export default {
    data() {
        return {
            createTaskError: '',
            taskNameInput: '',
            taskId: '',
            masterVmInput: '',
            selectedOrganizer: '',
            websiteInput: '',
            taskDescription: '',
            helpCommand: '',
            helpText: '',
            organizerList: [],
        }
    },
    emits: ['addnotification'],
    props: ['csrf'],
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
        createTask() {
            this.createTaskError = ''
            if (this.selectedOrganizer === '') {
                this.createTaskError += 'Please select an Organizer;\n'
            }
            if (this.taskNameInput === '') {
                this.createTaskError += 'Please provide an id for the new VM;\n'
            }
            if (this.taskDescription === '') {
                this.createTaskError += 'Please provide a description for you task;\n'
            }
            if (this.createTaskError !== '') {
                return
            }
            this.submitPost('tira-admin/create-task', {
                'task_id': this.taskId,
                'name': this.taskNameInput,
                'master_id': this.masterVmInput,
                'organizer': this.selectedOrganizer.organizer_id,
                'website': this.websiteInput,
                'description': this.taskDescription,
                'help_text': this.helpText,
                'help_command': this.helpCommand,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
            }).catch(error => {
                console.log(error)
                this.createTaskError = error
            })
        },
        string_to_slug (str) {
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
        },
    },
    beforeMount() {
        this.get(`/api/organizer-list`).then(message => {
            this.organizerList = message.context.organizer_list
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading organizer list: ${error}`)
        })
    },
    watch: {
        taskNameInput(newName, oldName) {
            this.taskId = this.string_to_slug(newName)
        }
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Create Task</h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-width-1-5">
        Task ID: [[ this.taskId ]] 
    </div>
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-4">
            <label for="task-name-input">Task Name*</label>
            <input id="task-name-input" class="uk-input" type="text" placeholder="Name of the Task"
                   :class="{'uk-form-danger': (this.createTaskError !== '' && this.taskNameInput === '')}"
                   v-model="taskNameInput">
        </div>
        <div class="uk-width-1-4">
            <label for="master-vm-input">Master VM*</label>
            <input id="master-vm-input" class="uk-input" type="text" placeholder="id-lowercase-with-dashes"
                   :class="{'uk-form-danger': (this.createTaskError !== '' && this.masterVmInput === '')}"
                   v-model="masterVmInput">
        </div>
        <div class="uk-width-1-4">
            <label for="host-select">Organizer*</label>
            <select id="host-select" class="uk-select" v-model="this.selectedOrganizer"
                   :class="{'uk-form-danger': (this.createTaskError !== '' && this.selectedOrganizer === '')}">
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
               :class="{'uk-form-danger': (this.createTaskError !== '' && this.taskDescription === '')}"
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
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="createTask">Create Task</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.createTaskError ]]</span>
    </div>
    *mandatory
</div>`
}