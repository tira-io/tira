<template>
<span class="uk-text-danger uk-margin-small-left" v-if="this.taskError !== ''">{{ this.taskError }}</span>
<div class="uk-card uk-card-small uk-card-default uk-card-body uk-width-1-1">
    <div class="uk-grid-small uk-margin-small" uk-grid>

      <h3 class="uk-card-title uk-width-1-1">
        <div class="uk-grid-small uk-margin-small" uk-grid>
          <span class="uk-text-muted">ID: {{ this.task_id }}</span>
          <div class="uk-width-expand"></div>
          <div>
            <div class="uk-button uk-button-primary uk-button-small" @click="saveTask"><font-awesome-icon icon="fas fa-save" /></div>
            <delete-confirm
              tooltip="Attention! This deletes the task and everything in it."
              @confirmation="() => deleteTask()"/>
          </div>
        </div>
      </h3>
      <div class="uk-width-2-5">
          <label>Task Name*
          <input class="uk-input" type="text" placeholder="Name of the Task"
                 :class="{'uk-form-danger': (this.taskError !== '' && this.taskNameInput === '')}"
                 v-model="taskNameInput" /></label>
      </div>
      <div class="uk-width-1-5">
          <label>Organizer*
          <select id="host-select" class="uk-select" v-model="this.selectedOrganizer"
                 :class="{'uk-form-danger': (this.taskError !== '' && this.selectedOrganizer === '')}">
              <option disabled value="">Please select an organizer</option>
              <option v-for="organizer in this.organizerList" :value="organizer">{{ organizer.name }}</option>
          </select></label>
      </div>
      <div class="uk-width-1-5">
          <label>Website
          <input id="website-input" class="uk-input" type="text" placeholder="Website URL"
                 v-model="websiteInput" /></label>
      </div>
      <div class="uk-margin-small uk-grid-small uk-width-1-1 uk-child-width-auto uk-grid">
          <label>Featured
              <input type="checkbox" class="uk-checkbox uk-margin-small-right" v-model="featured" />
          </label>
          <label uk-tooltip="title: When checked, users must register before submission.
            They must provide their name, email, and affiliation. You can view the registration data afterwards.">
            With Registration&nbsp;
            <input type="checkbox" class="uk-checkbox uk-margin-small-right" v-model="requireRegistration" />
          </label>
          <label uk-tooltip="title: When checked, users must register in a group.
            Their runs will be displayed with the group's name. Other users can join these groups." >Require Groups&nbsp;
            <input type="checkbox" class="uk-checkbox uk-margin-small-right" v-model="requireGroups" />
          </label>
          <label uk-tooltip="title: When checked, users can not create (and name) their own groups.
            They can only sign up to groups provided by you. You can create groups on the task page in edit mode." >Restrict Groups&nbsp;
            <input type="checkbox" class="uk-checkbox uk-margin-small-right" v-model="restrictGroups" />
          </label>
      </div>

      <div class="uk-margin-small uk-width-5-5">
          <label>Task Description*
          <textarea id="task-description-input" rows="3" class="uk-textarea" placeholder="Task Description"
                 :class="{'uk-form-danger': (this.taskError !== '' && this.taskDescription === '')}"
                 v-model="taskDescription" /> </label>
      </div>
      <div class="uk-margin-small uk-width-5-5">
          <label> Help Command
          <input type="text" class="uk-input" placeholder="mySoftware -c $inputDataset -r $inputRun -o $outputDir"
                 v-model="helpCommand" /></label>
      </div>
      <div class="uk-margin-small uk-width-5-5">
          <label> Help Text<textarea rows="6" class="uk-textarea" placeholder="Available variables: \n<code>$inputDataset</code>, \n<code>$inputRun</code>, \n<code>$outputDir</code>, \n<code>$dataServer</code>, and \n<code>$token</code>."
                 v-model="helpText" /></label>
      </div>
      <div class="uk-margin-small">
        <label>Allowed Teams for Task (leave empty if all teams are allowed)
        <textarea id="task-teams-input" rows="3" class="uk-textarea" placeholder=""
               v-model="taskTeams" /></label>
      </div>
    
      <div class="uk-width-1-1">
        <label><input class="uk-checkbox" type="checkbox" name="checkbox-gitci" v-model="isIrTask"> The task is an information retrieval task (configure the ir_datasets integration) </label>
      </div>
      <div v-if="isIrTask" class="uk-width-1-1">
        <label>IR-Datasets Re-Ranking Image <input type="text" class="uk-input" v-model="irdsReRankingImage" ></label>
      </div>
      <div v-if="isIrTask" class="uk-width-1-1">
        <label>IR-Datasets Re-Ranking Command <input type="text" class="uk-input" v-model="irdsReRankingCommand" ></label>
      </div>
      <div v-if="isIrTask" class="uk-width-1-1">
          <label>IR-Datasets Resources for Execution <input type="text" class="uk-input" v-model="irdsReRankingResources" ></label>
      </div>

    </div>
</div>
</template>
<script>
import DeleteConfirm from "../elements/delete-confirm";
import { get, submitPost } from "../../utils/getpost"


export default {
  data() {
    return {
      taskError: '',
      taskNameInput: '',
      taskTeams: '',
      selectedOrganizer: '',
      websiteInput: '',
      masterVmId: '',
      taskDescription: '',
      helpCommand: '',
      helpText: '',
      featured: false,
      requireRegistration: false,
      requireGroups: false,
      restrictGroups: false,
      organizerList: [],
      isIrTask: false,
      irdsReRankingImage: '',
      irdsReRankingCommand: '',
      irdsReRankingResources: '',
    }
  },
  components: { DeleteConfirm },
  emits: ['addnotification', 'updatetask'],
  props: ['csrf', 'task_id'],
  methods: {
    deleteTask() {
        get(`/tira-admin/delete-task/${this.task_id}`).then(message => {
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
        this.taskError += 'Please provide a name for your task;\n'
      }
      if (this.taskDescription === '') {
        this.taskError += 'Please provide a description for you task;\n'
      }
      if (this.taskError !== '') {
        return
      }
      submitPost(`/tira-admin/edit-task/${this.task_id}`, this.csrf, {
        'name': this.taskNameInput,
        'master_vm_id': this.masterVmId,
        'organizer': this.selectedOrganizer.organizer_id,
        'featured': this.featured,
        'website': this.websiteInput,
        'description': this.taskDescription,
        'help_text': this.helpText,
        'help_command': this.helpCommand,
        'require_registration': this.requireRegistration,
        'require_groups': this.requireGroups,
        'restrict_groups': this.restrictGroups,
        'task_teams': this.taskTeams,
        'is_information_retrieval_task': this.isIrTask,
        'irds_re_ranking_image': this.irdsReRankingImage,
        'irds_re_ranking_command': this.irdsReRankingCommand,
        'irds_re_ranking_resource': this.irdsReRankingResources,
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
  watch: {
    websiteInput(newWebsite, oldWebsite) {
      if (!(newWebsite.startsWith('http://') || newWebsite.startsWith('https://'))) {
        this.websiteInput = `https://${newWebsite}`
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
  },
  beforeMount() {
    get(`/api/organizer-list`).then(message => {
      this.organizerList = message.context.organizer_list
      get(`/api/task/${this.task_id}`).then(message => {
        let task = message.context.task
        this.taskNameInput = task.task_name
        this.websiteInput = task.web
        this.featured = task.featured
        this.masterVmId = task.master_vm_id
        this.selectedOrganizer = this.getOrganizerByName(task.organizer)
        this.taskDescription = task.task_description
        this.helpCommand = task.command_placeholder
        this.helpText = task.command_description
        this.requireRegistration = task.require_registration
        this.requireGroups = task.require_groups
        this.restrictGroups = task.restrict_groups
        this.taskTeams = task.allowed_task_teams
        this.isIrTask = task.is_information_retrieval_task
        this.irdsReRankingImage = task.irds_re_ranking_image
        this.irdsReRankingCommand = task.irds_re_ranking_command
        this.irdsReRankingResources = task.irds_re_ranking_resource
      }).catch(error => {
        this.$emit('addnotification', 'error', `Error loading task: ${error}`)
      })
    }).catch(error => {
      this.$emit('addnotification', 'error', `Error loading organizer list: ${error}`)
    })
  }
}
</script>
