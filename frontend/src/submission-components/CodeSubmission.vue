<template>

  <v-row v-if="!loading && userinfo.role !== 'guest'">
    <v-col :cols="$vuetify.display.mdAndUp ? '9' : '12'">
      <v-autocomplete clearable auto-select-first label="Choose software &hellip;" prepend-inner-icon="mdi-magnify"
        :items="allSoftwareSubmissions" item-title="display_name" item-value="docker_software_id" variant="underlined"
        v-model="tab" />
    </v-col>
    <v-col v-if="!$vuetify.display.smAndDown" :cols="$vuetify.display.mdAndUp ? '3' : '0'">
      <v-btn color="primary" v-if="!$vuetify.display.mdAndUp" icon="mdi-plus" @click="tab = 'newDockerImage'" />
      <v-btn color="primary" v-if="$vuetify.display.mdAndUp" prepend-icon="mdi-plus" size="large"
        @click="tab = 'newDockerImage'" block>New Submission</v-btn>
    </v-col>
  </v-row>
  <v-row v-if="$vuetify.display.smAndDown">
    <v-col :cols="12">
      <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="tab = 'newDockerImage'" block rounded>New
        Submission</v-btn>
    </v-col>
  </v-row>

  <v-skeleton-loader type="card" v-if="loading"/>

  <v-window v-model="tab" v-if="!loading && userinfo.role !== 'guest'" :touch="{ left: undefined, right: undefined }">
    <v-window-item v-for="ds in softwares" :value="ds.docker_software_id">
      <existing-docker-submission @deleteDockerImage="handleDeleteDockerImage"
        @modifiedSubmissionDetails="v => handleModifiedSubmission(v, softwares)"
        :user_id="user_id_for_submission" :datasets="datasets" :re_ranking_datasets="re_ranking_datasets"
        :is_ir_task="is_ir_task" :resources="resources" :docker_software_id="ds.docker_software_id"
        :organizer="organizer" :organizer_id="organizer_id"
        @refresh_running_submissions="$emit('refresh_running_submissions')" />
    </v-window-item>
    <v-window-item value="newDockerImage">
      <v-card class="mt-10" title="Make a new submission">
        <v-card-item v-if="loading"><loading :loading="loading"/></v-card-item>
        <v-card-item v-if="!loading && disabled">
        <v-card-text>

          <p>
            Code submissions are the recommended form of submitting to TIRA. Code submissions are compatible with CI/CD systems like <a href="https://github.com/features/actions" target="_blank">Github Actions</a> and build a Docker image from a git repository while collecting important experimental metadata to improve transparency and reproducibility. Please read how to <a href="https://docs.tira.io/participants/participate.html#prepare-your-submission" target="_blank">prepare your submission</a>.
          </p>

          <br>  
          <p>
            The steps below will guide you to make a new code submissions. Please do not hesitate to contact your organizers <a :href="organizer_link">{{organizer}}</a> or the <a href="https://www.tira.io/categories">forum</a> in case of questions or problems.
          </p>

          <br><br>
          You can setup a code submission in four steps:
          <br>

          <v-stepper :items="stepper_items" flat :border=false>
            <template v-slot:item.1>
              <v-card title="" flat>
                <h3>How do you want to submit your code?</h3>
                <v-radio-group v-model="code_configuration">
                  <v-radio label="I want to submit from my local machine" value="code-configuration-1" />
                  <v-radio label="I want to submit via CI/CD such as Github Actions" value="code-configuration-2" />
                </v-radio-group>
              </v-card>
            </template>

            <template v-slot:item.2>
              <v-card title="" flat>
                <h3>Create your Git repository</h3>
                Please create your git repository with your code. The repository can be private or public. We recommend to use <a href="https://github.com/" target="_blank">GitHub</a>.
                <br><br>
                <div v-if="code_configuration == 'code-configuration-2'">
                  <h3>Add the TIRA_CLIENT_TOKEN secret to your Git repository</h3>
                  In your repository, go to "Settings" -> "Secrets and variables" -> "Actions" and add a new repository secret with the name TIRA_CLIENT_TOKEN and the value:
                  <br><br>
                  <code-snippet title="TIRA_CLIENT_TOKEN" :code="token" expand_message=""/>
                </div>
              </v-card>
            </template>

            <template v-slot:item.3>
              <v-card title="" flat>

                <div v-if="code_configuration == 'code-configuration-1'">
                  First, please ensure that you have an up-to-date tira client installed:
                  <code-snippet title="Install" code="pip3 install --upgrade tira" expand_message=""/>

                  Then, please authenticate your TIRA client:
                  <code-snippet title="Authenticate" :code="'tira-cli login --token ' + token" expand_message=""/>

                  Lastly, please check that your TIRA client installation is valid:

                  <code-snippet title="Install" code="tira-cli verify-installation" expand_message=""/>

                  If the verification above does not show any errors, you can continue. If you want to resolve warnings or face errors, please have a look at the <a href="https://docs.tira.io/participants/python-client.html" target="_blank">installation documentation</a> for more detailed help.
                </div>
                <div v-if="code_configuration == 'code-configuration-2'">
                  Please download the Github action <a :href="'/data-download/git-repo-template/' + user_id + '/' + task_id + '.zip'" target="_blank">here</a>.
                  <br>
                  This zip directory contains the github action in the file ".github/workflows/upload-software-to-tira.yml" that you can add to your git repository. The rest of the zip directory shows exemplary how to connect the code of your repository to your repository, see the README.md in the zip for more details.
                </div>
              </v-card>
            </template>

            <template v-slot:item.4>
              <v-card title="" flat>
                <div v-if="code_configuration == 'code-configuration-1'">
                  Assumed that you have your code in a directory "my-submission" that is under version control, please first ensure that your git repository is clean:

                  <code-snippet title="Ensure the git repository is clean" code="git status" expand_message=""/>

                  <br>
                  This should report "nothing to commit, working tree clean".
                  <br>
                  Then, you can submit via:

                  <code-snippet title="Install" :code="'tira-cli code-submission --path my-submission --task ' + task_id" expand_message=""/>

                  You can modify the parameters accordingly, please see the <a href="https://docs.tira.io/participants/participate.html#submitting-your-submission" target="_blank">correspoding documentation</a> or help for more details:

                  <code-snippet title="Install" code="tira-cli code-submission --help" expand_message=""/>
                </div>
                <div v-if="code_configuration == 'code-configuration-2'">
                  After you have added the Github action (e.g., ".github/workflows/upload-software-to-tira.yml") to your Github repository, please run it by clicking on "Actions" -> "Upload Software to TIRA" -> "Run workflow".
                  <br><br>
                  After successful completion of the Github action, your new submission appears under the "Docker" tab above where you can select and run your new submission.
                </div>
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
    </v-window-item>
  </v-window>
</template>

<script lang="ts">
import { inject } from 'vue'

import {get, post, inject_response, reportError, reportSuccess, get_link_to_organizer, handleModifiedSubmission, extractUserFromCurrentUrl, type UserInfo} from "@/utils";
import {Loading, CodeSnippet, ExistingDockerSubmission} from '../components'

export default {
  name: "code-submission",
  components: {Loading, CodeSnippet, ExistingDockerSubmission},
  props: ['organizer', 'organizer_id', 'user_id', 'task_id', 'is_ir_task'],
  data() {
    return {
        loading: true,
        new_git_account: '',
        allow_public_repo: true,
        valid: false,
        user_id_for_submission: extractUserFromCurrentUrl(),
        submit_in_progress: false,
        repo_url: '',
        http_repo_url: '',
        ssh_repo_url: '',
        owner_url: '',
        http_owner_url: '',
        disabled: false,
        tab: '',
        code_configuration: 'code-configuration-1',
        token: '<ADD-YOUR-TOKEN-HERE>',
        userinfo: inject('userinfo') as UserInfo,
        rest_url: inject("REST base URL"),
        datasets: [],
        re_ranking_datasets: [{ "dataset_id": null, "display_name": "loading..." }],
        softwares: [{ 'display_name': 'loading', 'docker_software_id': '1' }],
        resources: ["loading..."],
    }
  },
  methods: {
    async connectToCodeRepo() {
      const { valid } = await (this.$refs.form as any).validate()

      if (!valid) {
        return
      }

      this.submit_in_progress = true
      post(this.rest_url + `/api/add_software_submission_git_repository/${this.task_id}/${this.user_id}`, {"external_owner": this.new_git_account, "allow_public_repo": this.allow_public_repo}, this.userinfo)
        .then(reportSuccess('Your git repository was created.'))
        .then(inject_response(this))
        .catch(reportError("Problem while adding your git repository.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.submit_in_progress = false})
    },
    handleDeleteDockerImage() {
      get(this.rest_url + `/task/${this.task_id}/vm/${this.user_id_for_submission}/delete_software/docker/${this.tab}`)
        .then(message => {
          this.softwares = this.softwares.filter(i => i.docker_software_id != this.softwares.find(i => i.display_name === this.tab)?.docker_software_id)
          this.tab = this.softwares.length > 0 ? this.softwares[0].display_name : 'newDockerImage'
        })
        .catch(reportError("Problem While Deleting Docker Image.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    load_re_ranking_datasets() {
      if (this.is_ir_task) {
        get(this.rest_url + '/api/re-ranking-datasets/' + this.task_id)
          .then(inject_response(this))
          .catch(reportError("Problem While Loading the re-rankign datasets for " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
      }
    },
    handleModifiedSubmission
  },
  beforeMount() {
    /*get(this.rest_url + `/api/get_software_submission_git_repository/${this.task_id}/${this.user_id}`)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem loading the data of the task.", "This might be a short-term hiccup, please try again. We got the following error: "))*/
      get(this.rest_url + '/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_submission + '/code')
      .then((result) => { this.$data.softwares = result.context.code.submissions; this.datasets = result.context.datasets; this.resources = result.context.resources; this.loading = false;})
        .catch(reportError("Problem While Loading the code submissions.", "This might be a short-term hiccup, please try again. We got the following error: "))
    
    this.disabled = true
    this.load_re_ranking_datasets()
    get(this.rest_url + '/api/token/' + this.user_id)
      .then(inject_response(this))
  },
  computed: {
    organizer_link() {return get_link_to_organizer(this.organizer_id)},
    stepper_items() {
      if (this.code_configuration == 'code-configuration-1') {
        return ['How?', 'Setup Your Git Repository', 'Prepare Your Environment', 'Submit']
      } else {
        return ['How?', 'Setup Your Git Repository', 'Add the Github Action', 'Submit']
      }
    },
    code_for_merging() {
      return '#Please make first sure that all changes in your repository are committed to your remote.\ngit remote add tira ' + this.ssh_repo_url + '\ngit config pull.rebase true\ngit pull tira main\ngit push tira main'
    },
    allSoftwareSubmissions() {
      let ret:any[] = []

      if (this.tab === 'newDockerImage') {
        ret = ret.concat([{ 'docker_software_id': 'newDockerImage', 'display_name': ' ' }])
      }

      return ret.concat(this.softwares)
    }
  }
}
</script>