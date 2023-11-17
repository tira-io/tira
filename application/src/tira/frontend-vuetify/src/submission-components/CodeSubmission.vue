<template>
  <v-card class="mt-10">
    <v-card-item v-if="loading"><loading :loading="loading"/></v-card-item>
    <v-card-item v-if="!loading">
      <v-card-text v-if="!repo_url">
        <v-form ref="form" v-model="valid">
          <v-row class="d-flex align-center justify-center">
            <v-col cols="6"><v-text-field v-model="new_git_account" label="Your GitHub Account" :rules="[v => !!(v && v.length) || 'Please select your GitHub account.']"/></v-col>
          </v-row>
          <v-row class="d-flex align-center justify-center">
            <v-col cols="6"><v-btn block color="primary" :loading="submit_in_progress" @click="connectToCodeRepo()" text="Add Code Repository"/></v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-text v-if="repo_url">
        <p class="mb-5">Code submissions allow you to automatically create Docker submissions from your GitHub repository via prepared GitHub actions that build, test, and upload your code as Docker image to TIRA. Your github repository is <a :href="repo_url">{{repo_url}}</a> owned by <a :href="owner_url">{{owner_url}}</a> (please contact this owner if additional accounts need access to this repository). If you have some problems, please do not hesitate to contact your organizers <a :href="organizer_link">{{organizer}}</a>.</p>

        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>Step 1: Upload your Code to your repository</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>Merge existing repo</p>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>Step 2: Build your Docker image via GitHub Actions</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>step by step description</p>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>Step 3:Execute your Docker image in TIRA</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>step by step description</p>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card-item>
  </v-card>
</template>

<script lang="ts">
import {get, post, inject_response, reportError, reportSuccess, get_link_to_organizer} from "@/utils";
import {Loading} from '../components'

export default {
  name: "code-submission",
  components: {Loading},
  props: ['organizer', 'organizer_id', 'user_id', 'task_id'],
  data() {
    return {
        loading: true,
        new_git_account: '',
        valid: false,
        submit_in_progress: false,
        repo_url: '',
        owner_url: ''
    }
  },
  methods: {
    async connectToCodeRepo() {
      const { valid } = await (this.$refs.form as any).validate()

      if (!valid) {
        return
      }

      this.submit_in_progress = true
      post(`/api/add_software_submission_git_repository/${this.task_id}/${this.user_id}`, {"external_owner": this.new_git_account})
        .then(reportSuccess('Your git repository was created.'))
        .then(message => {
          this.repo_url = message.context.repo_url
          this.owner_url = message.context.owner_url
        })
        .catch(reportError("Problem while adding your git repository.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.submit_in_progress = false})
    },
  },
  beforeMount() {
    get(`/api/get_software_submission_git_repository/${this.task_id}/${this.user_id}`)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem loading the data of the task.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  computed: {
    organizer_link() {return get_link_to_organizer(this.organizer_id)}
  }
}
</script>