<template>
<span v-if="this.addDatasetError !== ''" class="uk-text-danger uk-margin-small-left">{{ this.addDatasetError }}</span>
<div class="uk-card uk-card-small uk-card-default uk-card-body uk-width-1-1">
  <div class="uk-grid-small uk-margin-small" uk-grid>

    <h3 class="uk-card-title uk-width-1-1">
      <div class="uk-grid-small uk-margin-small" uk-grid>
        <span class="uk-text-muted">ID: {{ this.datasetId }}</span>
        <div class="uk-width-expand"></div>
        <div>
          <div class="uk-button uk-button-primary uk-button-small" @click="addDataset">add dataset <font-awesome-icon icon="fas fa-play" /></div>
        </div>
      </div>
    </h3>
    <div class="uk-width-2-5">
          <label>Dataset Name*
          <input class="uk-input" type="text" placeholder="Name of the Dataset"
                 :class="{'uk-form-danger': (this.addDatasetError !== '' && this.datasetNameInput === '')}"
                 v-model="datasetNameInput"></label>
      </div>
      <div class="uk-width-1-5">
          <label>Task*
          <select class="uk-select" v-model="this.selectedTask"
                 :class="{'uk-form-danger': (this.addDatasetError !== '' && this.selectedTask === '')}">
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
export default {
  data() {
      return {
            addDatasetError: '',
            datasetNameInput: '',
            datasetId: '',
            selectedTask: '',
            type: 'training',
            taskList: [],
      }
  },
  emits: ['addnotification', 'adddataset'],
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
          }).then(message => {
              this.$emit('addnotification', 'success', message.message)
              this.$emit('adddataset', message.context)
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
  }
}
</script>
