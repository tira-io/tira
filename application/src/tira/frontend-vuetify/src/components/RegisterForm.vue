<template>
  <v-dialog width="75%" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn variant="outlined" v-bind="props" block>Register</v-btn>
    </template>
    <template v-slot:default="{ isActive }">
      <v-card class="pa-3">
        <card-title><v-toolbar color="primary" :title="'Register to ' + task.task_id"></v-toolbar></card-title>
        <v-card-text>
          <v-form v-if="!loading" v-model="valid" ref="form">
            <v-container>
              <v-row>
                <v-col cols="12" md="12">
                  <v-text-field v-model="username" :rules="nameRules" :counter="10" label="Team Name" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-text-field v-model="email" :rules="emailRules" label="Email" required/>
                </v-col>

                <v-col cols="12" md="12">
                  <v-text-field v-model="affiliation" :rules="notEmptyRules" :counter="60" label="Affiliation" required/>
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
import {validateEmail, validateTeamName, validateNotEmpty} from "../utils"
import Loading from "./Loading.vue"

export default {
  name: "register-form",
  props: ["task", "isActive"],
  components: {Loading},
  data: () => ({
      valid: false,
      loading: false,
      username: '',
      lastname: '',
      country: '',
      affiliation: '',
      selectedEmployment: '',
      instructorName: '',
      team: '',
      questions: '',
      employmentOptions: ["", "Undergraduate Student", "PhD Student", "Academic Research", "Industry", "Private"],
      selectedParticipation: "",
      participationList: ["", "Course", "Thesis", "Academic Research", "Industry Research", "Private Interest"],
      showInstructorClasses: ['Undergraduate Student', 'Course', 'Thesis'],
      instructorEmail: "",
      nameRules: [validateTeamName],
      email: '',
      notEmptyRules: [validateNotEmpty],
      emailRules: [validateEmail],
    }),
  methods: {
    async submitRegistration (isActive: any) {
      const { valid } = await (this.$refs.form as any).validate()

      if (valid) {
        this.loading = true
        isActive.value = false
        console.log("Submit...")
      }
    },
  },
  computed: {
    showInstructor(){
      return this.showInstructorClasses.includes(this.selectedParticipation) || this.showInstructorClasses.includes(this.selectedEmployment)
    },
  }
}
</script>
  