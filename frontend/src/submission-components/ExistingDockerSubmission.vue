<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-card class="px-5">
      <div :class="$vuetify.display.mdAndUp ? 'w-100 d-flex justify-end mt-4' : 'w-100 d-flex justify-space-evenly mt-4'">
          <edit-submission-details
              type='docker'
              :id="docker_software_id"
              :user_id="user_id"
              :is_ir_task="is_ir_task"
              @edit="updateDockerSoftwareDetails"
          />
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

      <v-card-subtitle class="my-4">{{ docker_software_details.description }}</v-card-subtitle>
      <v-form id="docker-submission-readonly-input">
        <v-text-field label="Previous Stages (Immutable for Reproducibility)" v-if="docker_software_details.previous_stages" v-model="docker_software_details.previous_stages" readonly/>

        <div v-if="docker_software_details.mount_hf_model_display && docker_software_details.mount_hf_model_display[0].href != 'loading...'">
        This software mounts the Hugging Face models 
        <span v-for="hf_model in docker_software_details.mount_hf_model_display">
          <a :href="hf_model.href" target="_blank">{{hf_model.display_name}}</a>&nbsp;
        </span>
        into the Docker image.
        </div>

        <v-text-field label="Docker Image (Immutable for Reproducibility)" v-model="docker_software_details.user_image_name" readonly/>
        <v-text-field label="Command (Immutable for Reproducibility)" v-model="docker_software_details.command" readonly/>
      </v-form>

      <v-divider></v-divider>
      
      <v-card-title>Run the Software</v-card-title>
      <v-form ref="form" v-model="valid">
        <v-autocomplete v-model="selectedResource" :items="allResources" label="Resources" item-title="display_name" item-value="resource_id" :rules="[v => !!(v && v.length) || 'Please select the resources for the execution.']" />
        <v-autocomplete v-model="selectedDataset" v-if="!docker_software_details.ir_re_ranker" :items="datasets" item-title="display_name" item-value="dataset_id" label="Dataset" :rules="[v => !!(v && v.length) || 'Please select on which dataset the software should run.']" />
        <v-autocomplete v-model="selectedRerankingDataset" v-if="docker_software_details.ir_re_ranker" :items="re_ranking_datasets" item-title="display_name" item-value="dataset_id" label="Re-ranking Dataset" :rules="[v => !!(v && v.length) || 'Please select which system your software should re-rank.']" />
        <v-btn class="mb-1" block color="primary" variant="outlined" :loading="runSoftwareInProgress" @click="runSoftware()" text="Run"/>
      </v-form>
    </v-card>

  </v-container>

  <h2>Submissions</h2>
  <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id" :docker_software_id="docker_software_id"/>
</template>

<script lang="ts">
import { inject } from 'vue'

import {Loading, RunList} from "../components"
import { get, post, reportError, reportSuccess, inject_response, extractTaskFromCurrentUrl, type UserInfo } from '../utils'
import {VAutocomplete} from 'vuetify/components'
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";

export default {
  name: "existing-docker-submission",
  components: {Loading, RunList, VAutocomplete, EditSubmissionDetails},
  emits: ['refresh_running_submissions', 'deleteDockerImage', 'modifiedSubmissionDetails'],
  props: ['user_id', 'datasets', 're_ranking_datasets', 'resources', 'docker_software_id', 'organizer', 'organizer_id', 'is_ir_task'],
  data() {
    return {loading: true, runSoftwareInProgress: false, selectedDataset: '', valid: false, selectedResource: '',
      docker_software_details: {
        'display_name': 'loading ...', 'user_image_name': 'loading', 'command': 'loading',
        'description': 'loading ...', 'previous_stages': 'loading ...', 'paper_link': 'loading ...', 'ir_re_ranker': false, 'mount_hf_model_display': [{'href': 'loading...', 'display_name': 'loading...', }]
      },
      task_id: extractTaskFromCurrentUrl(), selectedRerankingDataset: '',
      rest_url: inject("gRPC base URL"),
      userinfo: inject('userinfo') as UserInfo
    }
  },
  methods: {
    deleteDockerImage() {
      this.$emit('deleteDockerImage');
    },
    async runSoftware() {
      const { valid } = await (this.$refs.form as any).validate()
      console.log(this.selectedResource)

      if (valid) {
        this.runSoftwareInProgress = true
        var reranking_dataset = 'none'

        if (this.docker_software_details.ir_re_ranker) {
          reranking_dataset = this.selectedRerankingDataset
                
          for (const r of this.re_ranking_datasets) {
            if (reranking_dataset == r.dataset_id) {
              this.selectedDataset = r.original_dataset_id
            }
          }
        }

        post(this.rest_url + `/grpc/${this.task_id}/${this.user_id}/run_execute/docker/${this.selectedDataset}/${this.docker_software_id}/${this.selectedResource}/${reranking_dataset}`, {}, this.userinfo)
        .then(reportSuccess("Software was scheduled in the cluster. It might take a few minutes until the execution starts.", "Started run on: " + this.selectedDataset + " dataset with " + this.selectedResource))
        .catch(reportError("Problem starting the software.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.$emit('refresh_running_submissions'); this.runSoftwareInProgress = false; })
      }
    },
    showEditModal() {
      (this.$refs.editModal as any).show();
    },
    updateDockerSoftwareDetails(editedDetails: any) {
      this.docker_software_details.display_name = editedDetails.display_name
      this.docker_software_details.description = editedDetails.description
      this.docker_software_details.paper_link = editedDetails.paper_link
      this.$emit('modifiedSubmissionDetails', editedDetails)
    },
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
    get(inject("REST base URL")+'/api/docker-softwares-details/' + this.user_id + '/' + this.docker_software_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  watch: {
    details(old_value, new_value) {
    }
  }
}
</script>