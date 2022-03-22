export default {
    data() {
        return {
            editDatasetError: '',
            datasetNameInput: '',
            masterVmInput: '',
            selectedTask: '',
            publish: '',
            evaluatorWorkingDirectory: '',
            evaluatorCommand: '',
            evaluationMeasures: '',
            taskList: [],
        }
    },
    emits: ['addnotification', 'closemodal', 'deletedataset', 'editdataset'],
    props: ['csrf', 'dataset_id'],
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
                'X-CSRFToken': this.csrf
            })

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
        saveDataset() {
            console.log('save dataset')
            this.editDatasetError = ''
            if (this.selectedTask === '') {
                this.editDatasetError += 'Please select a Task;\n'
            }
            if (this.datasetNameInput === '') {
                this.editDatasetError += 'Please provide a name for the new Dataset;\n'
            }
            if (this.editDatasetError !== '') {
                return
            }
            this.submitPost(`/tira-admin/edit-dataset/${this.dataset_id}`, {
                'name': this.datasetNameInput,
                'task': this.selectedTask.task_id,
                'master_id': this.masterVmInput,
                'publish': this.publish,
                'evaluator_working_directory': this.evaluatorWorkingDirectory,
                'evaluator_command': this.evaluatorCommand,
                'evaluation_measures': this.evaluationMeasures,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
                this.$emit('closemodal')
                this.$emit('editdataset', message.context)
            }).catch(error => {
                console.log(error)
                this.editDatasetError = error
            })
        },
        deleteDataset() {
            this.get(`/tira-admin/delete-dataset/${this.dataset_id}`).then(message => {
                this.$emit('deletedataset', dataset_id)
                this.$emit('closemodal')
            }).catch(error => {
                this.$emit('addnotification', 'error', error)
            })
        },
        getTaskById(task_id){
            for (const task of this.taskList) {
                if (task.task_id === task_id){
                    return task
                }
            }
            return {}
        }
    },
    beforeMount() {
        this.get(`/api/task-list`).then(message => {
            this.taskList = message.context.task_list
            this.get(`/api/dataset/${this.dataset_id}`).then(message => {
                const dataset = message.context.dataset
                const evaluator = message.context.evaluator
                this.datasetNameInput = dataset.display_name
                this.masterVmInput = evaluator.vm_id
                this.publish = !dataset.is_confidential
                this.evaluatorWorkingDirectory = evaluator.working_dir
                this.evaluatorCommand = evaluator.command
                this.evaluationMeasures = evaluator.measures
                this.selectedTask = this.getTaskById(dataset.task)
            }).catch(error => {
                this.$emit('addnotification', 'error', `Error loading task: ${error}`)
            })
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
        })
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Edit Dataset <span class="uk-text-lead uk-text-muted">ID: [[ this.datasetId ]]</span></h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.datasetNameInput === '')}"
                   v-model="datasetNameInput"> Dataset Name*</label>
        </div>
        <div class="uk-width-1-3">
            <label><select class="uk-select" v-model="this.selectedTask"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.selectedTask === '')}">
                <option v-for="task in this.taskList" :value="task">[[ task.task_id ]]</option>
            </select> Task*</label>
        </div>
        <div class="uk-width-1-3">
            <div>
                <label><input class="uk-checkbox" type="checkbox" name="checkbox-publish" v-model="publish"> Public Dataset</label>
            </div>
        </div>
    </div>
    <div class="uk-margin-right">
        <h2>Evaluator</h2>
    </div>
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label><input type="text" class="uk-input" placeholder="/path/to/directory - Defaults to home."
                   v-model="evaluatorWorkingDirectory" /> Evaluator Working Directory</label>
        </div>
        <div class="uk-width-1-3">
            <label><input type="text" class="uk-input" placeholder="Command to be run from working directory"
                   v-model="evaluatorCommand" /> Evaluator Command</label>
        </div>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text" placeholder="id-lowercase-with-dashes"
                   v-model="masterVmInput">Master VM</label>
        </div>
    </div>
    <div class="uk-margin-small">
        <label><textarea rows="4" class="uk-textarea" placeholder="Measure Name,measure_key\nName will be displayed to the users.\nmeasure_key must be as output by the evaluation software."
               v-model="evaluationMeasures" /> Evaluation Measures</label>
   </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="saveDataset">Save</button>
        <button class="uk-button uk-button-danger" @click="deleteDataset">Delete</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.editDatasetError ]]</span>
    </div>
    *mandatory
</div>`
}