<template>
<div>
<div class="uk-grid-small uk-margin-small" uk-grid>
    <div class="uk-margin-right">
      <h2>Add Task <span class="uk-text-lead uk-text-muted">ID: {{ this.taskId }}</span></h2>
    </div>
</div>
<div class="uk-margin-small">
    <div class="uk-grid-small uk-margin-small" uk-grid>
        <div class="uk-width-1-3">
            <label>Task Name* <input class="uk-input" type="text" placeholder="Name of the Task"
                   :class="{'uk-form-danger': (this.createTaskError !== '' && this.taskNameInput === '')}"
                   v-model="taskNameInput"></label>
        </div>
        <div class="uk-width-1-3">
            <label>Organizer*
            <select class="uk-select" v-model="this.selectedOrganizer"
                   :class="{'uk-form-danger': (this.createTaskError !== '' && this.selectedOrganizer === '')}">
                <option disabled value="">Please select an organizer</option>
                <option v-for="organizer in this.organizerList" :value="organizer">{{ organizer.name }}</option>
            </select></label>
        </div>
        <div class="uk-width-1-3">
            <label>Website
            <input id="website-input" class="uk-input" type="text" placeholder="Website URL"
                   v-model="websiteInput"></label>
        </div>
    </div>
    <div class="uk-margin-small uk-grid-small uk-child-width-1-4 uk-grid uk-text-center">
        <label>Featured
            <input type="checkbox" class="uk-checkbox" v-model="featured" />
        </label>
        <label uk-tooltip="title: When checked, users must register before submission.
          They must provide their name, email, and affiliation. You can view the registration data afterwards.">
          With Registration&nbsp;
          <input type="checkbox" class="uk-checkbox" v-model="requireRegistration" />
        </label>
        <label uk-tooltip="title: When checked, users must register in a group.
          Their runs will be displayed with the group's name. Other users can join these groups." >Require Groups&nbsp;
          <input type="checkbox" class="uk-checkbox" v-model="requireGroups" />
        </label>
        <label uk-tooltip="title: When checked, users can not create (and name) their own groups.
          They can only sign up to groups provided by you. You can create groups on the task page in edit mode." >Restrict Groups&nbsp;
          <input type="checkbox" class="uk-checkbox" v-model="restrictGroups" />
        </label>
    </div>
    <div class="uk-margin-small">
        <label>Master VM ID*
        <input id="master-vm-id-input" type="text" class="uk-input" placeholder="new-task-master"
               v-model="masterVmId" /> </label>
    </div>
    <div class="uk-margin-small">
        <label>Task Description*
        <textarea id="task-description-input" rows="3" class="uk-textarea" placeholder="Task Description"
               :class="{'uk-form-danger': (this.createTaskError !== '' && this.taskDescription === '')}"
               v-model="taskDescription" /></label>
    </div>
    <div class="uk-margin-small">
        <label>Help Command
        <input id="help-command-input" type="text" class="uk-input" placeholder="mySoftware -c $inputDataset -r $inputRun -o $outputDir"
               v-model="helpCommand" /> </label>
    </div>
    <div class="uk-margin-small">
        <label>Help Text
        <textarea id="help-text-input" rows="6" class="uk-textarea" placeholder="Available variables: \n<code>$inputDataset</code>, \n<code>$inputRun</code>, \n<code>$outputDir</code>, \n<code>$dataServer</code>, and \n<code>$token</code>."
               v-model="helpText" /> </label>
    </div>
    <div class="uk-margin-small">
        <label>Allowed Teams for Task (leave empty if all teams are allowed)
        <textarea id="task-teams-input" rows="3" class="uk-textarea" placeholder=""
               v-model="taskTeams" /></label>
    </div>
    <div class="uk-margin-small">
        <button class="uk-button uk-button-primary" @click="createTask">Add Task</button>
        <span class="uk-text-danger uk-margin-small-left">{{ this.createTaskError }}</span>
    </div>
    *mandatory
</div>
</div>
</template>
<script>
import { slugify } from "../../utils/stringprocessing"
import { get, submitPost } from "../../utils/getpost"

export default {
  data() {
    return {
      createTaskError: '',
      taskNameInput: '',
      taskTeams: '',
      taskId: '',
      masterVmId: '',
      selectedOrganizer: '',
      websiteInput: '',
      taskDescription: '',
      helpCommand: '',
      helpText: '',
      featured: false,
      requireRegistration: false,
      requireGroups: false,
      restrictGroups: false,
      organizerList: [],
    }
  },
  emits: ['addnotification', 'closemodal'],
  props: ['csrf'],
  methods: {
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
      if (this.masterVmId === '') {
        this.createTaskError += 'Please provide a master vm for you task;\n'
      }
      if (this.createTaskError !== '') {
        return
      }
      submitPost('tira-admin/create-task', this.csrf, {
        'task_id': this.taskId,
        'name': this.taskNameInput,
        'featured': this.featured,
        'master_vm_id': this.masterVmId,
        'organizer': this.selectedOrganizer.organizer_id,
        'website': this.websiteInput,
        'description': this.taskDescription,
        'help_text': this.helpText,
        'help_command': this.helpCommand,
        'require_registration': this.requireRegistration,
        'require_groups': this.requireGroups,
        'restrict_groups': this.restrictGroups,
        'task_teams': this.taskTeams,
      }).then(message => {
        this.$emit('addnotification', 'success', message.message)
        this.$emit('closemodal')
      }).catch(error => {
        console.log(error)
        this.createTaskError = error
      })
    }
  },
  beforeMount() {
    get(`/api/organizer-list`).then(message => {
      this.organizerList = message.context.organizer_list
    }).catch(error => {
      this.$emit('addnotification', 'error', `Error loading organizer list: ${error}`)
    })
  },
  watch: {
    taskNameInput(newName, oldName) {
      this.taskId = slugify(newName)
    },
    websiteInput(newWebsite, oldWebsite) {
      if (!(newWebsite.startsWith('http://') || newWebsite.startsWith('https://'))) {
        this.websiteInput = `https://${newWebsite}`
      }
    }
  },
  requireRegistration(newCheck, oldCheck) {
    if (!newCheck){
      this.requireGroups = false
      this.restrictGroups = false
    }
  },
  requireGroups(newCheck, oldCheck) {
    if (newCheck){
      this.requireRegistration = true
    } else {
      this.restrictGroups = false
    }
  },
  restrictGroups(newCheck, oldCheck) {
    if (newCheck){
      this.requireGroups = true
      this.requireRegistration = true
    }
  }
}
</script>
