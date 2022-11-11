<template>
<a v-if="!requireRegistration || userIsRegistered" class="uk-button uk-button-primary uk-text-large"
     uk-tooltip="title: Go to the submission page for this task;"
     :href="submissionLink" :disabled="!loaded">
    <font-awesome-icon icon="fas fa-terminal" class="uk-margin-right" />Submit
</a>
<a v-else-if="requireRegistration" class="uk-button uk-text-large" uk-toggle="target: #modal-register"
     :class="{'uk-button-primary': !userIsRegistered, 'uk-button-default': userIsRegistered}"
     uk-tooltip="title: This task requires a registration;" :disabled="!loaded">
    <font-awesome-icon icon="fas fa-user-edit" :class="{'uk-margin-right': !userIsRegistered}" />
    <span v-if="!userIsRegistered">Register</span>
</a>

<div id="modal-register" class="uk-container uk-container-expand" data-uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-width-xlarge">
        <button class="uk-modal-close-default" type="button" data-uk-close></button>
        <div class="uk-grid-small uk-margin-small" uk-grid>
            <h3 class="uk-width-1-1">
                <div class="uk-grid-small uk-margin-small" uk-grid>
                    <span>Register for {{ taskId }}</span>
                    <div class="uk-width-expand"></div>
                    <div>
                        <div class="uk-button uk-button-primary uk-button-small" @click="submitRegistration" :disabled="!valid">
                            <span v-if="!userIsRegistered" class="uk-margin-small-right">Submit Registration</span>
                            <font-awesome-icon icon="fas fa-save" />
                        </div>
                    </div>
                </div>
            </h3>

            <div class="uk-width-1-2" uk-tooltip="How the task organizers can call you.">
                <label>Name* <input class="uk-input" type="text" v-model="username"
                       :class="{'uk-form-danger': (registrationError !== '' && username === '')}" />
                </label>
            </div>
            <div class="uk-width-1-2" uk-tooltip="How the task organizers can contact you.">
                <label>Email* <input class="uk-input" type="text" v-model="email"
                       :class="{'uk-form-danger': (registrationError !== '' && email === '')}" />
                </label>
            </div>
            <div class="uk-width-1-2" uk-tooltip="Your organizational affiliation.">
                <label>Affiliation* <input class="uk-input" type="text" v-model="affiliation"
                       :class="{'uk-form-danger': (registrationError !== '' && affiliation === '')}" />
                </label>
            </div>
            <div class="uk-width-1-2" uk-tooltip="Your (or your affiliations) country of operation.">
                <label>Country <input class="uk-input" type="text" v-model="country" />
                </label>
            </div>
    <!--      dropdown with options - color mute for "select" entries -->
            <div class="uk-width-1-2">
                <label>I am <select class="uk-select" v-model="selectedEmployment" >
                    <option :class="{'uk-text-muted': employment===''}" v-for="employment in employmentList" :value="employment" :disabled="employment===''">{{ employment!=="" ? employment : "Please select a reason" }}</option>
                </select></label>
            </div>
            <div class="uk-width-1-2">
                <label>I participate for <select class="uk-select" v-model="selectedParticipation" >
                    <option :class="{'uk-text-muted': participation===''}" v-for="participation in participationList" :value="participation" :disabled="participation===''">{{ participation!=="" ? participation : "Please select a reason" }}</option>
                </select></label>
            </div>
            <div v-if="showInstructor" class="uk-width-1-2" uk-tooltip="Your instructor">
                <label>Supervisor Name <input class="uk-input" type="text" v-model="instructorName" />
                </label>
            </div>
            <div v-if="showInstructor" class="uk-width-1-2" uk-tooltip="The email of your instructor">
                <label>Supervisor Email <input class="uk-input" type="text" v-model="instructorEmail" />
                </label>
            </div>
            <span v-if="registrationError" class="uk-width-1-1 uk-text-danger">{{ registrationError }}</span>
        </div>
    </div>
<!--  TODO group selector -->
<!--  TODO toggle new group / join other group via ID -->
</div>
</template>
<script>
import { get, submitPost } from "../../utils/getpost";

export default {
  name: "register-button",
  props: {
    taskId: String,
    userId: String,
    requireRegistration: Boolean,
    userIsRegistered: Boolean,
    csrf: String,
  },
  data() {
    return {
      username: "",
      email: "",
      affiliation: "",
      country: "",
      selectedEmployment: "",
      employmentList: ["", "Undergraduate Student", "PhD Student", "Academic Research", "Industry", "Private"],
      selectedParticipation: "",
      participationList: ["", "Course", "Thesis", "Academic Research", "Industry Research", "Private Interest"],
      instructorName: "",
      instructorEmail: "",
      showInstructorClasses: ['Undergraduate Student', 'Course', 'Thesis'],
      registrationError: "",
      loaded: false,
    }
  },
  methods: {
    submitRegistration() {

    }
  },
  computed: {
    submissionLink() {
      return `task/${this.taskId}/user/${this.userId}`
    },
    showInstructor(){
      return this.showInstructorClasses.includes(this.selectedParticipation) || this.showInstructorClasses.includes(this.selectedEmployment)
    },
    valid(){
      return (this.username !== "" && this.email !== "" && this.affiliation !== "")
    }
  },
  watch: {
    userId(newId, oldId) {
      this.username = newId.replace('-default', '')
    }
  },
  emits: ['addNotification', 'updateReview'],
  mounted() {
    this.loaded=true
  },
  beforeMount() {
    // this.get(`/api/dataset/${this.dataset_id}`).then(message => {
    //       const dataset = message.context.dataset
    //       const evaluator = message.context.evaluator
    //       this.datasetNameInput = dataset.display_name
    //       this.publish = !dataset.is_confidential
    //       this.uploadName = dataset.default_upload_name
    //       this.evaluatorWorkingDirectory = evaluator.working_dir
    //       this.evaluatorCommand = evaluator.command
    //       this.evaluationMeasures = evaluator.measures
    //       this.isGitRunner = evaluator.is_git_runner
    //       this.gitRunnerImage = evaluator.git_runner_image
    //       this.gitRunnerCommand = evaluator.git_runner_command
    //       this.gitRepositoryId = evaluator.git_repository_id
    //       this.selectedTask = this.getTaskById(dataset.task)
    //   }).catch(error => {
    //       this.$emit('addnotification', 'error', `Error loading task: ${error}`)
    //   })
  }
}
</script>
