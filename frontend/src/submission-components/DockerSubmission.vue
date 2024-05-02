<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
  <v-row v-if="!loading && role !== 'guest'">
    <v-col :cols="$vuetify.display.mdAndUp ? '9' : '12'">
      <v-autocomplete clearable auto-select-first label="Choose software &hellip;" prepend-inner-icon="mdi-magnify" :items="allSoftwareSubmissions" item-title="display_name" item-value="docker_software_id"
                    variant="underlined" v-model="tab"/>
      </v-col>
      <v-col v-if="!$vuetify.display.smAndDown" :cols="$vuetify.display.mdAndUp ? '3' : '0'">
        <v-btn color="primary" v-if="!$vuetify.display.mdAndUp" icon="mdi-plus" @click="this.tab = 'newDockerImage'"/>
        <v-btn color="primary" v-if="$vuetify.display.mdAndUp" prepend-icon="mdi-plus" size="large" @click="this.tab = 'newDockerImage'" block>New Submission</v-btn>
      </v-col>
  </v-row>
  <v-row v-if="$vuetify.display.smAndDown">
    <v-col :cols="12">
        <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="this.tab = 'newDockerImage'" block rounded>New Submission</v-btn>
    </v-col>
  </v-row>

  <v-window v-model="tab" v-if="!loading && role !== 'guest'" :touch="{left: null, right: null}">
    <v-window-item v-for="ds in this.docker.docker_softwares" :value="ds.docker_software_id">
      <existing-docker-submission @deleteDockerImage="handleDeleteDockerImage" @modifiedSubmissionDetails="v => handleModifiedSubmission(v, this.docker.docker_softwares)"
                                  :user_id="user_id_for_submission"
                                  :datasets="datasets"
                                  :re_ranking_datasets="re_ranking_datasets"
                                  :is_ir_task="is_ir_task"
                                  :resources="resources" :docker_software_id="ds.docker_software_id"
                                  :organizer="organizer" :organizer_id="organizer_id"
                                  @refresh_running_submissions="$emit('refresh_running_submissions')"/>
    </v-window-item>
    <v-window-item value="newDockerImage">
      <new-docker-submission @add-new-docker-image="handleAddNewDockerImage" :is_ir_task="is_ir_task" :user_id_for_submission="user_id_for_submission"
                                  :step_prop="step" :docker_softwares="this.docker.docker_softwares"
                                  :organizer="organizer" :organizer_id="organizer_id"/>
    </v-window-item>
  </v-window>

</template>

<script>
import { inject } from 'vue'

import {VAutocomplete} from 'vuetify/components'
import { get, reportError, extractRole, extractTaskFromCurrentUrl, extractUserFromCurrentUrl, inject_response, filterByDisplayName, handleModifiedSubmission } from "@/utils";
import {Loading, LoginToSubmit, ExistingDockerSubmission, NewDockerSubmission} from "@/components";

export default {
  name: "docker-submission",
  components: {Loading, LoginToSubmit, VAutocomplete, ExistingDockerSubmission, NewDockerSubmission},
  emits: ['refresh_running_submissions'],
  props: ['step_prop', 'organizer', 'organizer_id', 'is_ir_task'],
  data() {
    return {
      tab: null,
      role: extractRole(),
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_submission: extractUserFromCurrentUrl(),
      runCommand: null,
      step: this.step_prop,
      loading: true,
      docker: {
        "images": [{"id": null, "display_name": 'loading...'}],
        "docker_softwares": [{'display_name': 'loading', 'docker_software_id': '1'}],
        "docker_software_help": "loading...",
      },
      selectedResources: '',
      resources: ["loading..."],
      selectedDataset: '',
      datasets: [{"dataset_id": null,"display_name": "loading..."}],
      re_ranking_datasets: [{"dataset_id": null,"display_name": "loading..."}],
    }
  },
  computed: {
    allSoftwareSubmissions() {
      let ret = []

      if (this.tab === 'newDockerImage') {
        ret = ret.concat([{'docker_software_id': 'newDockerImage', 'display_name': ' '}])
      }

      return ret.concat(this.docker.docker_softwares)
    }
  },
  methods: {
    updateUrlToCurrentStep() {
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    load_re_ranking_datasets() {
      if (this.is_ir_task) {
        get(inject("REST base URL")+'/api/re-ranking-datasets/' + this.task_id)
          .then(inject_response(this))
          .catch(reportError("Problem While Loading the re-rankign datasets for " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
      }
    },
    handleDeleteDockerImage() {
      get(inject("REST base URL")+`/task/${this.task_id}/vm/${this.user_id_for_submission}/delete_software/docker/${this.tab}`)
          .then(message => {
            this.docker.images = this.docker.images.filter(i => i.id != this.docker.images.find(i => i.display_name === this.tab).id)
            this.tab = this.docker.images.length > 0 ? this.docker.images[0].display_name : null
            this.showUploadForm = false
          })
          .catch(reportError("Problem While Deleting Docker Image.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    handleAddNewDockerImage(new_software) {
        this.docker.docker_softwares.push(new_software)
        this.tab = new_software.docker_software_id
    },
    handleModifiedSubmission
  },
  beforeMount() {
    get(inject("REST base URL")+'/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_submission + '/docker')
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading the Docker Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.load_re_ranking_datasets()
    this.step === '' ? this.tab = this.docker.docker_softwares[0].display_name : this.tab = "newDockerImage"
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    },
    is_ir_task(old_value, new_value) {
      this.load_re_ranking_datasets()
    }
  }
}
</script>