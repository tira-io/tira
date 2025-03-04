<template>
  <v-card class="mt-10">
    <v-card-item v-if="loading"><loading :loading="loading"/></v-card-item>
    <v-card-item v-if="!loading && disabled">
    <v-card-text>
      You can submit to TIRA from your source code repository via GitHub actions that dockerize your code, test the docker image, and upload it to TIRA. This way, you don't need to install Docker on your machine, and our prepared Github action sends the metadata (i.e., the commit hash, the branch, the repository, etc.) to TIRA to ensure that the submission can be linked to the code that produced it. Please do not hesitate to contact your organizers <a :href="organizer_link">{{organizer}}</a> or the <a href="https://www.tira.io/categories">forum</a> in case of questions or problems.

      <br><br>
      You can setup a software submission in three steps:
      <br>

      <v-stepper :items="['Setup Your Git Repository', 'Add the Github Action', 'Submit']" flat :border=false>
        <template v-slot:item.1>
          <v-card title="" flat>
            <h3>Create your Git repository</h3>
            Please create your git repository with your code. The repository can be private or public.
            <br><br>
            <h3>Add the TIRA_CLIENT_TOKEN secret to your Git repository</h3>
            In your repository, go to "Settings" -> "Secrets and variables" -> "Actions" and add a new repository secret with the name TIRA_CLIENT_TOKEN and the value:
            <br><br>
            <code-snippet title="TIRA_CLIENT_TOKEN" :code="token" expand_message=""/>
          </v-card>
        </template>

        <template v-slot:item.2>
          <v-card title="" flat>
            Please download the Github action <a :href="'/data-download/git-repo-template/' + user_id + '/' + task_id + '.zip'" target="_blank">here</a>.
            <br>
            This zip directory contains the github action in the file ".github/workflows/upload-software-to-tira.yml" that you can add to your git repository. The rest of the zip directory shows exemplary how to connect the code of your repository to your repository, see the README.md in the zip for more details.
          </v-card>
        </template>

        <template v-slot:item.3>
          <v-card title="" flat>
            After you have added the Github action (e.g., ".github/workflows/upload-software-to-tira.yml") to your Github repository, please run it by clicking on "Actions" -> "Upload Software to TIRA" -> "Run workflow".
            <br><br>
            After successful completion of the Github action, your new submission appears under the "Docker" tab above where you can select and run your new submission.
          </v-card>
        </template>
      </v-stepper>
    </v-card-text>
    </v-card-item>
    <v-card-item v-if="!loading && !disabled">
      <v-card-text v-if="!repo_url">
        <v-form ref="form" v-model="valid">

          <v-row class="d-flex align-center justify-center">
            <v-col cols="6"><v-checkbox v-model="allow_public_repo" label="Allow Public Github Repository (You can change this later. Using a public Github repository has the advantage that Github Actions are free, otherwise, they count towards the bill of organizers.)" /></v-col>
          </v-row>
          <v-row class="d-flex align-center justify-center">
            <v-col cols="6"><v-text-field @keydown.enter.prevent="connectToCodeRepo()" v-model="new_git_account" label="Your GitHub Account" :rules="[v => !!(v && v.length) || 'Please select your GitHub account.']"/></v-col>
          </v-row>
          <v-row class="d-flex align-center justify-center">
            <v-col cols="6"><v-btn block color="primary" :loading="submit_in_progress" @click="connectToCodeRepo()" text="Add Code Repository"/></v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-card-text v-if="repo_url">
        <p class="mb-5">Code submissions allow you to automatically create Docker submissions from your GitHub repository via prepared GitHub actions that build, test, and upload your code as Docker image to TIRA. Your github repository is <a :href="http_repo_url" target="_blank">{{repo_url}}</a> owned by <a :href="http_owner_url" target="_blank">{{owner_url}}</a> (please contact this owner if additional accounts need access to this repository). If you have some problems, please do not hesitate to contact your organizers <a :href="organizer_link">{{organizer}}</a>.</p>

        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>Step 1: Upload your Code to your repository</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>Your  <a :href="http_repo_url" target="_blank">prepared Github repository</a> already contains all secrets to build and upload your code as Docker image to TIRA and makes it easier for us to help you in case of problems because we can access the code.</p>
              
              <p>If you start from scratch, you can just <a :href="http_repo_url" target="_blank">clone your repository</a>.</p>
              
              <code-snippet title="Merge your existing repository (intended as second upstream)" :code="code_for_merging" expand_message="If you already have a git repository, please merge it with the tira repository that is intended as second remote/upstream."/>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>Step 2: Build your Docker image via GitHub Actions</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>Please go to your <a :href="http_repo_url" target="_blank">prepared Github repository</a> and upload your code to the repository. Upon initialization, your repository contains a jupyter notebook
              <a :href="http_repo_url + '/blob/main/jupyter-notebook-submissions/pyterrier-notebook.ipynb'" target="_blank">Jupyter notebook</a> together with <a :href="http_repo_url +'/tree/main/jupyter-notebook-submissions'" target="_blank">a detailed README on how to submit together with background information</a>.</p>
              
              <p>In short, navigate to "Actions" -> "upload-notebook-submission" in <a :href="http_repo_url" target="_blank">your Github repository</a> and click on "Run workflow" to start the Github action that builds, tests, and uploads your submission.</p>

              <p>You can also watch the <a href="https://conf.fmi.uni-leipzig.de/playback/presentation/2.3/9d654239893aee5d164d92e3b2263ab510249eea-1700482128152" target="_blank">recording of the tutorial</a> from the IR lab in Leipzig from teh 20.11.2023.</p>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>Step 3:Execute your Docker image in TIRA</v-expansion-panel-title>
            <v-expansion-panel-text>
              <p>After your Github action was successfull, it prints out the name under which your software was added to TIRA as Docker submission (at the very bottom of the step "Build, test, and upload image" of your Github action). Click on the Docker tab and select your newly added software (maybe reload the page). Select the dataset on which you want to execute your software together with the execution instance (e.g., 1CPU + 10GB of RAM) and click on RUN to start your submission. Admins will review your submission (might take up to one day) and reach out to you in case there are problems with the execution.</p>

              <p>You can also watch the <a href="https://conf.fmi.uni-leipzig.de/playback/presentation/2.3/9d654239893aee5d164d92e3b2263ab510249eea-1700482128152" target="_blank">recording of the tutorial</a> from the IR lab in Leipzig from teh 20.11.2023.</p>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card-item>
  </v-card>
</template>

<script lang="ts">
import { inject } from 'vue'

import {get, post, inject_response, reportError, reportSuccess, get_link_to_organizer, type UserInfo} from "@/utils";
import {Loading, CodeSnippet} from '../components'

export default {
  name: "code-submission",
  components: {Loading, CodeSnippet},
  props: ['organizer', 'organizer_id', 'user_id', 'task_id'],
  data() {
    return {
        loading: true,
        new_git_account: '',
        allow_public_repo: true,
        valid: false,
        submit_in_progress: false,
        repo_url: '',
        http_repo_url: '',
        ssh_repo_url: '',
        owner_url: '',
        http_owner_url: '',
        disabled: false,
        token: '<ADD-YOUR-TOKEN-HERE>',
        userinfo: inject('userinfo') as UserInfo
    }
  },
  methods: {
    async connectToCodeRepo() {
      const { valid } = await (this.$refs.form as any).validate()

      if (!valid) {
        return
      }

      this.submit_in_progress = true
      post(inject("REST base URL")+`/api/add_software_submission_git_repository/${this.task_id}/${this.user_id}`, {"external_owner": this.new_git_account, "allow_public_repo": this.allow_public_repo}, this.userinfo)
        .then(reportSuccess('Your git repository was created.'))
        .then(inject_response(this))
        .catch(reportError("Problem while adding your git repository.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.submit_in_progress = false})
    },
  },
  beforeMount() {
    get(inject("REST base URL")+`/api/get_software_submission_git_repository/${this.task_id}/${this.user_id}`)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem loading the data of the task.", "This might be a short-term hiccup, please try again. We got the following error: "))

    get(inject("REST base URL")+'/api/token/' + this.user_id)
      .then(inject_response(this))
  },
  computed: {
    organizer_link() {return get_link_to_organizer(this.organizer_id)},
    code_for_merging() {
      return '#Please make first sure that all changes in your repository are committed to your remote.\ngit remote add tira ' + this.ssh_repo_url + '\ngit config pull.rebase true\ngit pull tira main\ngit push tira main'
    }
  }
}
</script>