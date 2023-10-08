<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
  <v-row v-if="!loading && role !== 'guest'">
    <v-responsive class="mt-10" min-width="220px" id="task-search">
      <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
                    variant="underlined" v-model="software_filter"/>
    </v-responsive>
  </v-row>
  <v-row v-if="!loading && role !== 'guest'">
    <v-col cols="10">
      <v-tabs v-model="tab" fixed-tabs class="mb-10">
        <v-tab variant="outlined" v-for="ds in this.filteredSoftwares" :value="ds.docker_software_id">
          {{ ds.display_name }}
        </v-tab>
      </v-tabs>
    </v-col>
    <v-col cols="2">
      <v-tabs v-model="tab" fixed-tabs class="mb-10">
        <v-tab value="newDockerImage" color="primary" style="max-width: 100px;" variant="outlined">
          <v-icon>mdi-plus</v-icon>
        </v-tab>
      </v-tabs>
    </v-col>
  </v-row>

  <v-window v-model="tab" v-if="!loading && role !== 'guest'">
    <v-window-item v-for="ds in this.docker.docker_softwares" :value="ds.docker_software_id">
      <existing-docker-submission @deleteDockerImage="handleDeleteDockerImage" @modifiedSubmissionDetails="v => handleModifiedSubmission(v, this.docker.docker_softwares)"
                                  :user_id="user_id_for_submission"
                                  :datasets="datasets"
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
      software_filter: null,
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
      resources: [
        "loading..."
      ],
      selectedDataset: '',
      datasets: [{
        "dataset_id": null,
        "display_name": "loading...",
      }
      ],
    }
  },
  computed: {
    filteredSoftwares() {
      return filterByDisplayName(this.docker.docker_softwares, this.software_filter)
    },
  },
  methods: {
    updateUrlToCurrentStep() {
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    handleDeleteDockerImage() {
      get(`/task/${this.task_id}/vm/${this.user_id_for_submission}/delete_software/docker/${this.tab}`)
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
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_submission + '/docker')
        .then(inject_response(this, {'loading': false}, true))
        .catch(reportError("Problem While Loading the Docker Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.tab = this.docker.images[0].display_name
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>