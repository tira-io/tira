export default {
    data() {
        return {
            addDatasetError: '',
            datasetNameInput: '',
            datasetId: '',
            masterVmInput: '',
            selectedTask: '',
            type: 'training',
            evaluatorWorkingDirectory: '',
            evaluatorCommand: '',
            evaluationMeasures: '',
            taskList: [],
        }
    },
    emits: ['addnotification', 'closemodal', 'adddataset'],
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
        addDataset() {
            console.log('add dataset')
            this.addDatasetError = ''
            if (this.selectedTask === '') {
                this.addDatasetError += 'Please select a Task;\n'
            }
            if (this.datasetNameInput === '') {
                this.addDatasetError += 'Please provide a name for the new Dataset;\n'
            }
            if (this.addDatasetError !== '') {
                return
            }
            this.submitPost('/tira-admin/add-dataset', {
                'dataset_id': this.datasetId,
                'name': this.datasetNameInput,
                'master_id': this.masterVmInput,
                'task': this.selectedTask.task_id,
                'type': this.type,
                'evaluator_working_directory': this.evaluatorWorkingDirectory,
                'evaluator_command': this.evaluatorCommand,
                'evaluation_measures': this.evaluationMeasures,
            }).then(message => {
                this.$emit('addnotification', 'success', message.message)
                this.$emit('adddataset', message.context)
                this.$emit('closemodal')
            }).catch(error => {
                console.log(error)
                this.addDatasetError = error
            })
        },
        string_to_slug(str) {
            str = str.replace(/^\s+|\s+$/g, ''); // trim
            str = str.toLowerCase();

            // remove accents, swap ñ for n, etc
            var from = "àáäâèéëêìíïîòóöôùúüûñç·/_,:;";
            var to = "aaaaeeeeiiiioooouuuunc------";
            for (var i = 0, l = from.length; i < l; i++) {
                str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
            }

            str = str.replace(/\./g, '-')
                .replace(/[^a-z0-9 -]/g, '') // remove invalid chars
                .replace(/\s+/g, '-') // collapse whitespace and replace by -
                .replace(/-+/g, '-'); // collapse dashes

            return str;
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
            this.selectedTask = this.getTaskById(this.task_id)
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
        })
    },
    watch: {
        datasetNameInput(newName, oldName) {
            this.datasetId = this.string_to_slug(newName)
        }
    },
    template: `
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Add Dataset <span class="uk-text-lead uk-text-muted">ID: [[ this.datasetId ]]</span></h2> 
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label><input class="uk-input" type="text" placeholder="Name of the Dataset"
                   :class="{'uk-form-danger': (this.addDatasetError !== '' && this.datasetNameInput === '')}"
                   v-model="datasetNameInput"> Dataset Name*</label>
        </div>
        <div class="uk-width-1-3">
            <label><select class="uk-select" v-model="this.selectedTask"
                   :class="{'uk-form-danger': (this.addDatasetError !== '' && this.selectedTask === '')}">
                <option disabled value="">Please select a task</option>
                <option v-for="task in this.taskList" :value="task">[[ task.task_id ]]</option>
            </select> Task*</label>
        </div>
        <div class="uk-width-1-3">
            <div>
                <label><input class="uk-radio" type="radio" name="radio2" value="training" v-model="type"> training</label>
            </div>
            <div>
                <label><input class="uk-radio" type="radio" name="radio2" value="test" v-model="type"> test</label>
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
               v-model="evaluationMeasures" />Evaluation Measures</label>
   </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="addDataset">Add Dataset</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.addDatasetError ]]</span>
    </div>
    *mandatory
</div>`
}