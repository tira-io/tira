<template>
<div>
    <a  v-if="(!requireRegistration || userIsRegistered) && userVmsForTask && userVmsForTask.length <= 1" class="uk-button uk-button-primary uk-text-large"
         uk-tooltip="title: Go to the submission page for this task;" :href="submissionLink" :disabled="!loaded">
        <font-awesome-icon icon="fas fa-terminal" class="uk-margin-right" />Submit
    </a>
    <a v-else-if="requireRegistration && userId" class="uk-button uk-text-large" uk-toggle="target: #modal-register"
          :class="{'uk-button-primary': !userIsRegistered, 'uk-button-default': userIsRegistered}"
          uk-tooltip="title: This task requires a registration;" :disabled="!loaded">

        <font-awesome-icon icon="fas fa-user-edit" :class="{'uk-margin-right': !userIsRegistered}" />
        <span v-if="!userIsRegistered">Register new Team</span>
    </a>
    <span v-else-if="!userId">Please <a href='/login'>Login to TIRA</a> to register your Team and Submit</span>

    <span v-if="(!requireRegistration || userIsRegistered) && userVmsForTask && userVmsForTask.length > 1">
        <select-team-button :user-vms-for-task="userVmsForTask" :task-id="this.taskId" rendering="long" />
    </span>


    <!--<a if="!userIsRegistered && requireRegistration" class="uk-button uk-text-large"
        :class="{'uk-button-primary': !userIsRegistered, 'uk-button-default': userIsRegistered}"
         uk-tooltip="title: This task requires a registration. Join an existing team;" :disabled="!loaded">
        <font-awesome-icon icon="fas fa-terminal" :class="{'uk-margin-right': !userIsRegistered}" />
        <span >Join existing Team</span>
    </a>-->

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

            <div class="uk-width-2-2" uk-tooltip="How the task can call your team.">
                <label>
                    Team name* 
                    <select class="uk-select" :class="{'uk-form-danger': (registrationError !== '' && group === '')}" v-model="group">
                        <option class="uk-text-muted" disabled="true" value="">Please select a team name.</option>
                        <option :class="{'uk-text-muted': g===''}" :disabled="g===''" v-for="g in groupList" :value="g">{{ g!=="" ? g : "Please select a team name." }}</option>
                    </select>
                </label>
            </div>

            <div class="uk-width-1-2" uk-tooltip="How the task organizers can call you.">
                <label>Full name* <input class="uk-input" type="text" v-model="username"
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
            <div class="uk-width-2-2">
                <label>
                    Team members (that are not you).<br>
                    Full name, affiliation, country, email of each other member of your team.<br>
                    One team member per line.
                    <textarea class="uk-input" type="textarea" v-model="team" style="height: 125px;"  />
                </label>
            </div>
            <div class="uk-width-2-2">
                <label>
                    Do you have any other questions?
                    <textarea class="uk-input" type="textarea" v-model="questions"  style="height: 125px;" />
                </label>
            </div>
            <span v-if="registrationError" class="uk-width-1-1 uk-text-danger">{{ registrationError }}</span>
        </div>
    </div>
</div>
</div>
</template>
<script>
import { get, submitPost } from "../../utils/getpost";
import SelectTeamButton from '../select-team-button.vue'

export default {
  name: "register-button",
  props: {
    taskId: String,
    userId: String,
    userVmsForTask: Array, 
    groupList: Array,
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
      questions: "",
      team: "",
      selectedEmployment: "",
      employmentList: ["", "Undergraduate Student", "PhD Student", "Academic Research", "Industry", "Private"],
      group: "",
      selectedParticipation: "",
      participationList: ["", "Course", "Thesis", "Academic Research", "Industry Research", "Private Interest"],
      instructorName: "",
      instructorEmail: "",
      showInstructorClasses: ['Undergraduate Student', 'Course', 'Thesis'],
      registrationError: "",
    }
  },
  methods: {
    submitRegistration() {
      this.registrationError = ''
      if (this.group === '') {
        this.registrationError += 'Please select a Team Name;\n'
      }
      if (this.username === '') {
        this.registrationError += 'Please provide a Full name;\n'
      }
      if (this.email === '') {
        this.registrationError += 'Please provide an Email;\n'
      }
      if (this.affiliation === '') {
        this.registrationError += 'Please provide an Affiliation;\n'
      }
      
      if (this.registrationError !== '') {
        return
      }
      
      submitPost('/api/registration/add_registration/vm/'+ this.taskId, this.csrf, {
        'username': this.username,
        'email': this.email,
        'affiliation': this.affiliation,
        'country': this.country,
        'employment': this.selectedEmployment,
        'group': this.group,
        'participation': this.selectedParticipation,
        'instructorName': this.instructorName,
        'instructorEmail': this.instructorEmail,
        'questions': this.questions,
        'team': this.team
      }).then(message => {
        this.$emit('addNotification', 'success', 'You are now registered for the team "' + this.group + '" and can submit runs.')
        this.$emit('updateUserVmsForTask', this.group)
        
        this.$emit('closeModal')
      }).catch(error => {
        console.log(error)
        this.registrationError = error
      })
    }
  },
  computed: {
    submissionLink() {
      const base = window.location.origin
    
      var team = this.userId
      if (this.userVmsForTask && this.userVmsForTask.length > 0) {
        team = this.userVmsForTask[0]
      }
      
      return `${base}/task/${this.taskId}/user/${team}`
    },
    showInstructor(){
      return this.showInstructorClasses.includes(this.selectedParticipation) || this.showInstructorClasses.includes(this.selectedEmployment)
    },
    valid(){
      return (this.username !== "" && this.email !== "" && this.affiliation !== "")
    }
  },
  emits: ['addNotification', 'updateUserVmsForTask', 'closeModal'],
  components: {SelectTeamButton},
}
</script>
