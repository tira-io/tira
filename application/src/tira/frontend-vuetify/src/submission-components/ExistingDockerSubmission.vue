<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-card class="px-5">
      <div class="w-100 d-flex justify-space-between">
        <v-card-title>{{ docker_software_details.display_name }}</v-card-title>
        <div class="mt-4">
          <v-btn variant="outlined" color="#303f9f">
            <v-icon>mdi-file-edit-outline</v-icon>
            Edit
          </v-btn>
          <v-btn class="ml-4" variant="outlined" color="red" @click="deleteDockerImage()">
            <v-tooltip
                activator="parent"
                location="bottom"
            >Attention! This deletes the container and ALL runs associated with it
            </v-tooltip>
            <v-icon>mdi-delete-alert-outline</v-icon>
            Delete
          </v-btn>
        </div>
      </div>

      <v-card-subtitle>{{ docker_software_details.description }}</v-card-subtitle>
      <v-form>
        <v-text-field label="Previous Stages (Disabled for Reproducibility)" v-if="docker_software_details.previous_stages" v-model="docker_software_details.previous_stages" disabled/>
        <v-text-field label="Docker Image (Disabled for Reproducibility)" v-model="docker_software_details.user_image_name" disabled/>
        <v-text-field label="Command (Disabled for Reproducibility)" v-model="docker_software_details.command" disabled/>
      </v-form>

      <v-divider></v-divider>
      
      <v-card-title>Run the Software</v-card-title>
      <v-form ref="form" v-model="valid">
        <v-autocomplete v-model="selectedResource" :items="allResources" label="Resources" item-title="display_name" item-value="resource_id" :rules="[v => !!(v && v.length) || 'Please select the resources for the execution.']" />
        <v-autocomplete v-model="selectedDataset" :items="datasets" item-title="display_name" item-value="dataset_id" label="Dataset" :rules="[v => !!(v && v.length) || 'Please select on which dataset the software should run.']" />
        <v-btn class="mb-1" block color="primary" variant="outlined" :loading="runSoftwareInProgress" @click="runSoftware()" text="Run"/>
      </v-form>
    </v-card>

  </v-container>

  <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id" :docker_software_id="docker_software_id"/>
</template>

<script lang="ts">
import {Loading, RunList} from "../components"
import { get, reportError, inject_response, extractTaskFromCurrentUrl } from '../utils'
import {VAutocomplete} from 'vuetify/components'

export default {
  name: "existing-docker-submission",
  components: {Loading, RunList, VAutocomplete},
  props: ['user_id', 'datasets', 'resources', 'docker_software_id', 'organizer', 'organizer_id'],
  data() {
    return {loading: true, runSoftwareInProgress: false, selectedDataset: '', valid: false, selectedResource: '',
      docker_software_details: {
        'display_name': 'loading ...', 'user_image_name': 'loading', 'command': 'loading',
        'description': 'loading ...', 'previous_stages': 'loading ...'
      },
      task_id: extractTaskFromCurrentUrl()
    }
  },
  methods: {
    deleteDockerImage() {
      this.$emit('deleteDockerImage');
    },
    async runSoftware() {
      const { valid } = await (this.$refs.form as any).validate()

      if (valid) {
        this.runSoftwareInProgress = true
        setTimeout(() => {
          this.runSoftwareInProgress = false;
          window.alert('running software \n' + this.selectedDataset + ' \n' + this.selectedResource + ' \n' + this.docker_software_id + ' \n' + this.user_id)
        }, 2000)
      }
    }
  },
  computed: {
    allResources() {
      let ret = []

      for (var k of Object.keys(this.resources)) {
        ret.push({"resource_id": k, "display_name": this.resources[k]['description']})
      }
      
      return ret
    }
  },
  beforeMount() {
    this.loading = true
    get('/api/docker-softwares-details/' + this.user_id + '/' + this.docker_software_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
