<template>
<span v-if="this.importDatasetError !== ''" class="uk-text-danger uk-margin-small-left">{{ this.importDatasetError }}</span>
<div class="uk-card uk-card-small uk-card-default uk-card-body uk-width-1-1">
  <div class="uk-grid-small uk-margin-small" uk-grid>

    <h3 class="uk-card-title uk-width-1-1">
      <div class="uk-grid-small uk-margin-small" uk-grid>
        <span class="uk-text-muted">ID: {{ this.datasetId }}</span>
        <div class="uk-width-expand"></div>
        <div>
          <div class="uk-button uk-button-small"
              :class="{ 'uk-button-default': importInProgress, 'uk-button-primary': !importInProgress}"
              @click="addDataset">import IRDS dataset <font-awesome-icon icon="fas fa-play" /></div>
        </div>
      </div>
    </h3>
    <div class="uk-width-1-5">
          <label>Dataset Name (IRDS-ID)*
          <input class="uk-input" type="text" placeholder="Name of the Dataset (must be the irds-id)"
                 :class="{'uk-form-danger': (this.importDatasetError !== '' && this.datasetNameInput === '')}"
                 v-model="datasetNameInput"></label>
    </div>
      
    <div class="uk-width-1-5">
        <label>Docker Image*
            <input class="uk-input" type="text" placeholder="Docker Image" :class="{'uk-form-danger': (this.importDatasetError !== '' && this.dockerImage === '')}" v-model="dockerImage">
        </label>
    </div>
      
      <div class="uk-width-1-5">
          <label>Task*
          <select class="uk-select" v-model="this.selectedTask"
                 :class="{'uk-form-danger': (this.importDatasetError !== '' && this.selectedTask === '')}">
              <option disabled value="">Please select a task</option>
              <option v-for="task in this.taskList" :value="task">{{ task.task_id }}</option>
          </select></label>
      </div>
      <div class="uk-width-1-5 uk-margin-remove-bottom uk-padding-small">
          <div>
              <label><input class="uk-radio" type="radio" name="radio2" value="training" v-model="type"> training</label>
          </div>
          <div>
              <label><input class="uk-radio" type="radio" name="radio2" value="test" v-model="type"> test</label>
          </div>
      </div>

  </div>
</div>
</template>
<script charset="utf-8">
import { get, submitPost } from "../../utils/getpost";
import { slugify } from "../../utils/stringprocessing";

export default {
  data() {
      return {
            importDatasetError: '',
            datasetNameInput: '',
            dockerImage: '',
            datasetId: '',
            selectedTask: '',
            type: 'training',
            importInProgress: false,
            taskList: [],
      }
  },
  emits: ['addnotification', 'adddataset'],
  props: ['csrf', 'task_id'],
  methods: {
      addDataset() {
          console.log('add dataset')
          this.importDatasetError = ''
          if (this.selectedTask === '') {
              this.importDatasetError += 'Please select a Task;\n'
          }
          if (this.datasetNameInput === '') {
              this.importDatasetError += 'Please provide a name for the new Dataset;\n'
          }
          if (this.dockerImage === '') {
              this.importDatasetError += 'Please provide a docker image for the import;\n'
          }
          if (this.importDatasetError !== '') {
              return
          }
          
          if(this.importInProgress) {
              return
          }
          
          this.importInProgress = true
          submitPost('/tira-admin/import-irds-dataset/' + this.selectedTask.task_id, this.csrf, {
              'dataset_id': this.datasetId,
              'name': this.datasetNameInput,
              'image': this.dockerImage,
              'type': this.type,
          }).then(message => {
              this.$emit('addnotification', 'success', message.message)
              this.$emit('adddataset', message.context)
              this.importInProgress = false
          }).catch(error => {
              console.log(error)
              this.importDatasetError = error
              this.$emit('addnotification', 'error', error.message)
              this.importInProgress = false
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
      get(`/api/task-list`).then(message => {
          this.taskList = message.context.task_list
          this.selectedTask = this.getTaskById(this.task_id, this.taskList)
          this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id
      }).catch(error => {
          this.$emit('addnotification', 'error', `Error loading task list: ${error}`)
      })
  },
  watch: {
      datasetNameInput(newName, oldName) {
          this.datasetId = slugify(newName)
      },
      evaluatorWorkingDirectory(newName, oldName) {
          if(newName === ""){
              this.evaluatorWorkingDirectory = '/home/' + this.selectedTask.master_vm_id + '/'
          }
      }
  }
}
</script>
