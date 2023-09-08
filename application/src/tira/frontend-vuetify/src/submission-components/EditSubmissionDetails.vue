<template>
  <v-btn variant="outlined" color="#303f9f" @click="showEditModal()">
  <v-dialog v-model="showModal" width="auto" scrollable>
    <v-card>
      <loading :loading="loading" />
      <v-toolbar color="primary">
      <v-card-title >Edit Software</v-card-title>
      </v-toolbar>

      <v-card-text v-if="!loading">
        <v-form>
          <v-text-field v-model="docker_software_details.display_name" label="Name"></v-text-field>
          <v-textarea v-model="docker_software_details.description" label="Description"></v-textarea>
          <v-text-field v-model="docker_software_details.paper_link" label="Link your Paper"></v-text-field>
        </v-form>
      </v-card-text>

      <v-card-actions class="justify-end">
        <v-btn @click="cancelEdit()">Cancel</v-btn>
        <v-btn color="primary" @click="submitEdit()" v-if="!loading" :loading="submit_in_progress">Save</v-btn>
      </v-card-actions>

    </v-card>
  </v-dialog>
    <v-icon>mdi-file-edit-outline</v-icon>
    Edit
  </v-btn>
</template>

<script>
import {extractTaskFromCurrentUrl, get, inject_response, post, reportError} from "@/utils";
import {Loading} from "@/components";

export default {
  name: 'edit-submission-details',
  components: {Loading},
  props: ['type', 'id', 'user_id'],
  emits: ['edit'],
  data() {
    return {
      showModal: false,
      loading: true,
      submit_in_progress: false,
      task_id: extractTaskFromCurrentUrl(),
      docker_software_details: {
        'display_name': 'loading ...', 'description': 'loading ...', 'paper_link': 'loading...',
      },
    }
  },
  methods: {
    showEditModal() {
      this.loading = true
      let url = null
      if (this.type === 'docker') {
        url = '/api/docker-softwares-details/' + this.user_id + '/' + this.id
      }
      if (this.type === 'upload') {
        url = `/task/${this.task_id}/vm/${this.user_id}/save_software/upload/${this.id}`
      }
      get(url)
          .then(inject_response(this, {'loading': false}))
          .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
      this.showModal = true;
    },

    cancelEdit() {
      this.showModal = false
    },
    submitEdit() {
      this.submit_in_progress = true;
      post(`/task/${this.task_id}/vm/${this.user_id}/save_software/docker/${this.id}`, {
            'display_name': this.docker_software_details.display_name,
            'description': this.docker_software_details.description,
            'paper_link': this.docker_software_details.paper_link,
      }, true)
          .then(() => {
            let to_emit = {...this.docker_software_details}
            to_emit['id'] = this.id
            this.$emit('edit', to_emit)

            this.showModal = false
            })
          .catch(reportError("Problem while Saving Submission Details.", "This might be a short-term hiccup, please try again. We got the following error: "))
          .then(() => {
            this.submit_in_progress = false
          })
    },
  }
};
</script>
