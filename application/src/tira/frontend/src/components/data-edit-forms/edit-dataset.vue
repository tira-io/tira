<template>
<span class="uk-text-danger uk-margin-small-left" v-if="this.editDatasetError !== ''">{{ this.editDatasetError }}</span>
<div class="uk-margin-small uk-grid-small" uk-grid>
    <div class="uk-card uk-card-small uk-card-default uk-card-body uk-width-1-1">
      <div class="uk-grid-small uk-margin-small" uk-grid>

        <h3 class="uk-card-title uk-width-1-1">
          <div class="uk-grid-small uk-margin-small" uk-grid>
            <span class="uk-text-muted">ID: {{ this.dataset_id }}</span>
            <div class="uk-width-expand"></div>
            <div>
              <div class="uk-button uk-button-primary uk-button-small" @click="saveDataset">
                <font-awesome-icon icon="fas fa-save" />
              </div>
              <div class="uk-button uk-button-danger uk-button-small" @click="deleteDataset">
                <font-awesome-icon icon="fas fa-trash-alt"/>
              </div>
            </div>
          </div>
        </h3>

        <div class="uk-width-1-4">
            <label>Dataset Name* <input class="uk-input" type="text"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.datasetNameInput === '')}"
                   v-model="datasetNameInput" /></label>
        </div>
        <div class="uk-width-1-4">
            <label>Task* <select class="uk-select" v-model="this.selectedTask"
                   :class="{'uk-form-danger': (this.editDatasetError !== '' && this.selectedTask === '')}">
                <option v-for="task in this.taskList" :value="task">{{ task.task_id }}</option>
            </select></label>
        </div>
        <div class="uk-width-1-4">
            <div>
              <label>Name of uploaded run results<input type="text" class="uk-input" placeholder="predictions.ndjson"
                     v-model="uploadName" /></label>
            </div>
        </div>

        <div class="uk-width-1-4">
            <div>
              <label><input class="uk-checkbox" type="checkbox" name="checkbox-publish" v-model="publish"> Public Dataset</label>
            </div>
        </div>
    </div>
    </div>

    <div class="uk-card uk-card-small uk-card-default uk-card-body uk-width-1-1">
          <h3 class="uk-card-title uk-width-1-1">
          <div class="uk-grid-small uk-margin-small" uk-grid>
            <span>Evaluator</span>
            <div class="uk-width-expand"></div>
            <div>
              <div class="uk-button uk-button-primary uk-margin-small-right uk-button-small" @click="saveDataset">
                <font-awesome-icon icon="fas fa-save" />
              </div>
            </div>
          </div>
        </h3>
      <div class="uk-margin-small">
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
                <label> Image to be run <input type="text" class="uk-input" v-model="gitRunnerImage" placeholder="ubuntu:18.04"/></label>
            </div>
            <div class="uk-width-1-2">
                <label>Git Runner Command <input type="text" class="uk-input" v-model="gitRunnerCommand" placeholder="echo 'Hello Evaluator' "/></label>
            </div>
            <div class="uk-width-1-1">
                <label><input class="uk-checkbox" type="checkbox" name="checkbox-gitci" v-model="useExistingRepo"> use custom repository (Do only change as expert) </label>
            </div>
            <div v-if="useExistingRepo" class="uk-width-1-1">
                <label>Git Repository ID <input type="text" class="uk-input" v-model="gitRepositoryId" ></label>
            </div>
        </div>
    </div>
</div>
</template>
<script charset="utf-8">
export default {
    data() {
        return {
            editDatasetError: '',
            datasetNameInput: '',
            selectedTask: '',
            publish: '',
            uploadName: '',
            evaluatorWorkingDirectory: '',
            evaluatorCommand: '',
            isGitRunner: false,
            gitRunnerImage: '',
            gitRunnerCommand: '',
            gitRepositoryId: '',
            useExistingRepo: false,
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
            if (this.isGitRunner) {
                if (this.gitRunnerImage === '') {
                    this.editDatasetError += 'Please provide an image for the evaluator;\n'
                }
                if (this.gitRunnerCommand === '') {
                    this.editDatasetError += 'Please provide a command for the evaluator;\n'
                }
            }
            if (this.editDatasetError !== '') {
                return
            }
            this.submitPost(`/tira-admin/edit-dataset/${this.dataset_id}`, {
                'name': this.datasetNameInput,
                'task': this.selectedTask.task_id,
                'publish': this.publish,
                'upload_name': this.uploadName,
                'evaluator_working_directory': this.evaluatorWorkingDirectory,
                'evaluator_command': this.evaluatorCommand,
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
                this.$emit('deletedataset', this.dataset_id)
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
        },
        setup(){
            this.get(`/api/task-list`).then(message => {
                this.taskList = message.context.task_list
                this.get(`/api/dataset/${this.dataset_id}`).then(message => {
                    const dataset = message.context.dataset
                    const evaluator = message.context.evaluator
                    this.datasetNameInput = dataset.display_name
                    this.publish = !dataset.is_confidential
                    this.uploadName = dataset.default_upload_name
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
    },
    watch: {
        evaluatorWorkingDirectory(newName, oldName) {
            if(newName === ""){
                this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id + '/'
            }
        },
        dataset_id(newId, oldId){
            this.setup()
        }

    },
    beforeMount() {
        this.setup()
    }
}
</script>
