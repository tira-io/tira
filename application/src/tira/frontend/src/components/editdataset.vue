<script charset="utf-8">
export default {
    data() {
        return {
            editDatasetError: '',
            datasetNameInput: '',
            selectedTask: '',
            publish: '',
            evaluatorWorkingDirectory: '',
            evaluatorCommand: '',
            evaluationMeasures: '',
            isGitRunner: false,
            gitRunnerImage: '',
            gitRunnerCommand: '',
            gitRepositoryId: '',
            useExistingRepo: true,
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
                'publish': this.publish,
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
    watch: {
        evaluatorWorkingDirectory(newName, oldName) {
            if(newName === ""){
                this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id + '/'
            }
        }
    },
    beforeMount() {
        this.get(`/api/task-list`).then(message => {
            this.taskList = message.context.task_list
            this.get(`/api/dataset/${this.dataset_id}`).then(message => {
                const dataset = message.context.dataset
                const evaluator = message.context.evaluator
                this.datasetNameInput = dataset.display_name
                this.publish = !dataset.is_confidential
                this.evaluatorWorkingDirectory = evaluator.working_dir
                this.evaluatorCommand = evaluator.command
                this.evaluationMeasures = evaluator.measures
                    this.isGitRunner = evaluator.is_git_runner
                    this.gitRunnerImage = evaluator.git_runner_image
                    this.gitRunnerCommand = evaluator.git_runner_command
                    this.gitRepositoryId = evaluator.git_repository_id
                this.selectedTask = this.getTaskById(dataset.task)
            }).catch(error => {
                this.$emit('addnotification', 'error', `Error loading task: ${error}`)
            })
        }).catch(error => {
            this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
        })
    }
}
</script>
<template>
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
        <h2>Edit Dataset <span class="uk-text-lead uk-text-muted">ID: {{ this.dataset_id }}</span></h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label>Dataset Name* <input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.datasetNameInput === '')}"
                   v-model="datasetNameInput" /></label>
        </div>
        <div class="uk-width-1-3">
            <label>Task* <select class="uk-select" v-model="this.selectedTask"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.selectedTask === '')}">
                <option v-for="task in this.taskList" :value="task">{{ task.task_id }}</option>
            </select></label>
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
        <label><textarea rows="4" class="uk-textarea" placeholder="Measure Name,measure_key\nName will be displayed to the users.\nmeasure_key must be as output by the evaluation software."
               v-model="evaluationMeasures" /> Evaluation Measures</label>
   </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary uk-margin-right" @click="saveDataset">Save</button>
        <button class="uk-button uk-button-danger" @click="deleteDataset">Delete</button>
        <span class="uk-text-danger uk-margin-small-left">{{ this.editDatasetError }}</span>
    </div>
    *mandatory
</div>
</template>
