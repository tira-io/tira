export default {
    data() {
        return {
            addDatasetError: '',
            datasetNameInput: '',
            datasetId: '',
            selectedTask: '',
            type: 'training',
            uploadName: 'predictions.ndjson',
            evaluatorWorkingDirectory: '',
            evaluatorCommand: '',
            evaluationMeasures: '',
            isGitRunner: false,
            gitRunnerImage: '',
            gitRunnerCommand: '',
            gitRepositoryId: '',
            useExistingRepo: false,
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
                'task': this.selectedTask.task_id,
                'type': this.type,
                'upload_name': this.uploadName,
                'evaluator_working_directory': this.evaluatorWorkingDirectory,
                'evaluator_command': this.evaluatorCommand,
                'evaluation_measures': this.evaluationMeasures,
                'is_git_runner': this.isGitRunner,
                'git_runner_image': this.gitRunnerImage,
                'git_runner_command': this.gitRunnerCommand,
                'git_repository_id': this.gitRepositoryId,
                'use_existing_repository': this.useExistingRepo
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
            this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
        })
    },
    watch: {
        datasetNameInput(newName, oldName) {
            this.datasetId = this.string_to_slug(newName)
        },
        evaluatorWorkingDirectory(newName, oldName) {
            if(newName === ""){
                this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id + '/'
            }
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
            <label>Dataset Name*
            <input class="uk-input" type="text" placeholder="Name of the Dataset"
                   :class="{'uk-form-danger': (this.addDatasetError !== '' && this.datasetNameInput === '')}"
                   v-model="datasetNameInput"></label>
        </div>
        <div class="uk-width-1-3">
            <label>Task*
            <select class="uk-select" v-model="this.selectedTask"
                   :class="{'uk-form-danger': (this.addDatasetError !== '' && this.selectedTask === '')}">
                <option disabled value="">Please select a task</option>
                <option v-for="task in this.taskList" :value="task">[[ task.task_id ]]</option>
            </select></label>
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
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label>Name of uploaded run results<input type="text" class="uk-input" placeholder="predictions.ndjson"
                   v-model="uploadName" /></label>
        </div>
    </div>
    <div class="uk-margin-right">
        <h2>Evaluator</h2>
    </div>
    <div>
        <div>
            <label><input class="uk-radio" type="radio" name="radio3" :value="false" v-model="isGitRunner"> Master VM</label>&nbsp;
            <label><input class="uk-radio" type="radio" name="radio3" :value="true" v-model="isGitRunner"> Git CI</label>
        </div>
    </div>
    <div v-if="isGitRunner === false" class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label> Evaluator Working Directory
            <input type="text" class="uk-input"
                   v-model="evaluatorWorkingDirectory" /></label>
        </div>
        <div class="uk-width-1-3">
            <label>Evaluator Command
            <input type="text" class="uk-input" placeholder="Command to be run from working directory"
                   v-model="evaluatorCommand" /></label>
        </div>
        <div class="uk-width-1-3">
            <label>Master VM
            <input class="uk-input uk-disabled" type="text" placeholder="id-lowercase-with-dashes"
                   v-model="selectedTask.master_vm_id" disabled></label>
        </div>
    </div>
    <div v-if="isGitRunner === true" class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-2">
            <label> Image to be run <input type="text" class="uk-input" v-model="gitRunnerImage" /></label>
        </div>
        <div class="uk-width-1-2">
            <label>Git Runner Command <input type="text" class="uk-input" v-model="gitRunnerCommand" /></label>
        </div>
        <div class="uk-width-1-1">
            <label><input class="uk-checkbox" type="checkbox" name="checkbox-gitci" v-model="useExistingRepo"> use existing repository</label>
        </div>
        <div v-if="useExistingRepo" class="uk-width-1-1">
            <label>Git Repository ID <input type="text" class="uk-input" v-model="gitRepositoryId" ></label>
        </div>
    </div>   
     
    <div class="uk-margin-small">
        <label>Evaluation Measures
        <textarea rows="4" class="uk-textarea" placeholder="Measure Name,measure_key\nName will be displayed to the users.\nmeasure_key must be as output by the evaluation software."
               v-model="evaluationMeasures" /></label>
   </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="addDataset">Add Dataset</button>
        <span class="uk-text-danger uk-margin-small-left">[[ this.addDatasetError ]]</span>
    </div>
    *mandatory
</div>`
}