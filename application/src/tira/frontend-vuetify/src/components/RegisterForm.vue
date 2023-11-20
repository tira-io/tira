<template>
  <v-dialog width="75%" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" v-bind="props" block>Register</v-btn>
    </template>
    <template v-slot:default="{ isActive }">
      <v-card class="pa-3">
        <card-title><v-toolbar color="primary" :title="'Register to ' + task.task_id"></v-toolbar></card-title>
        <v-card-text>

          <v-form v-if="!loading && !canRegister" v-model="valid" ref="form">
            A registration is currently not possible. Maybe the registration is not yet open or already closed? This task is organized by <a :href="link_organizer">{{ task.organizer }}</a>, please do not hesitate to <a :href="contact_organizer">contact</a> the organizers to open the registration.
          </v-form>
          <v-form v-if="!loading && canRegister" v-model="valid" ref="form">
            <v-container>
              <v-row>
                <v-col v-if="task.restrict_groups" cols="12" md="12">
                  <v-select v-model="username" :rules="nameRules" label="Team Name" :items="availableTeamNames" required/>
                </v-col>
                <v-col v-if="!task.restrict_groups" cols="12" md="12">
                  <v-text-field v-model="username" :rules="nameRules" :counter="30" label="Team Name" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-text-field v-model="email" :rules="emailRules" label="Email" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-text-field v-model="affiliation" :rules="notEmptyRules" :counter="90" label="Affiliation" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-text-field v-model="country" :rules="notEmptyRules" label="Country" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-select v-model="selectedEmployment" label="I am" :items="employmentOptions" />
                </v-col>

                <v-col cols="12" md="12">
                  <v-select v-model="selectedParticipation" label="I participate for" :items="participationList" />
                </v-col>

                <v-col v-if="showInstructor" cols="12" md="12">
                  <v-text-field v-model="instructorName" label="Supervisor Name"/>
                </v-col>
                <v-col v-if="showInstructor" cols="12" md="12">
                  <v-text-field v-model="instructorEmail" label="The email of your instructor"/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-textarea v-model="team" label="Team members (that are not you). Full name, affiliation, country, email of each other team member. One team member per line."/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-textarea v-model="questions" label="Do you have any other questions?"/>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
          <div v-if="loading">
            <h2>Registration in Progress...</h2>
            <loading loading="loading"/>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-row v-if="!loading">
            <v-col cols="6"><v-btn variant="outlined" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6"><v-btn variant="outlined" color="primary" @click="submitRegistration(isActive)" block>Submit Registration</v-btn></v-col>
          </v-row>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
</template>
<script lang="ts">
import {validateEmail, validateTeamName, validateNotEmpty, post, reportError, reportSuccess, inject_response, get, get_link_to_organizer, get_contact_link_to_organizer} from "../utils"
import Loading from "./Loading.vue"


export default {
  name: "register-form",
  props: ["task", "isActive"],
  components: {Loading},
  emits: ['updateUserVmsForTask'],
  data: () => ({
      valid: false, loading: true, username: '', lastname: '', country: '', affiliation: '', instructorEmail: '',
      selectedEmployment: '', instructorName: '', team: '', questions: '', selectedParticipation: '', email: '',
      employmentOptions: ["", "Undergraduate Student", "PhD Student", "Academic Research", "Industry", "Private"],
      participationList: ["", "Course", "Thesis", "Academic Research", "Industry Research", "Private Interest"],
      showInstructorClasses: ['Undergraduate Student', 'Course', 'Thesis'],
      nameRules: [validateTeamName], notEmptyRules: [validateNotEmpty], emailRules: [validateEmail],
      remaining_team_names: ['']
    }),
  methods: {
    async submitRegistration (isActive: any) {
      const { valid } = await (this.$refs.form as any).validate()

      if (valid) {
        this.loading = true
        post('/api/registration/add_registration/vm/'+ this.task.task_id, {
          'username': this.username, 'email': this.email, 'affiliation': this.affiliation, 'country': this.country,
          'employment': this.selectedEmployment, 'group': this.username, 'participation': this.selectedParticipation,
          'instructorName': this.instructorName, 'instructorEmail': this.instructorEmail,
          'questions': this.questions, 'team': this.team
        }).then(message => {
          reportSuccess('You are now registered for the team "' + this.username + '" and can submit runs.')
          this.$emit('updateUserVmsForTask', this.username)
          isActive.value = false
          this.loading = false
        }).catch(error => {
          reportError("Problem while Saving the Review.", "This might be a short-term hiccup, please try again. We got the following error: " + error);
          this.loading = false
          this.valid = error
        })
      }
    },
  },
  computed: {
    showInstructor(){
      return this.showInstructorClasses.includes(this.selectedParticipation) || this.showInstructorClasses.includes(this.selectedEmployment)
    },
    availableTeamNames() {
      return this.task.allowed_task_teams.split('\n').filter((x: string) => x.length > 0 && this.remaining_team_names.includes(x))
    },
    canRegister() {
      if (!this.task.restrict_groups) {
        return true;
      }

      return this.availableTeamNames && this.availableTeamNames + '' !== 'undefined' && this.availableTeamNames + '' !== 'null' && this.availableTeamNames.length > 0
    },
    link_organizer() {return get_link_to_organizer(this.task.organizer_id);},
    contact_organizer() {return get_contact_link_to_organizer(this.task.organizer_id);},
  },
  beforeMount() {
    get('/api/registration_formular/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the registration formular.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
  