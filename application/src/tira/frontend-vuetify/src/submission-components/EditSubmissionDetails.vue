<template>
  <v-btn variant="outlined" color="#303f9f" @click="showEditModal()">
  <v-dialog v-model="showModal" width="auto" scrollable>
    <v-card>
      <loading :loading="loading" />
      <v-toolbar color="primary">
      <v-card-title > {{ component_name }}</v-card-title>
      </v-toolbar>

      <v-card-text v-if="!loading">
        <v-form>
          <v-text-field v-model="display_name" label="Name"></v-text-field>
          <v-textarea v-model="description" label="Description"></v-textarea>
          <v-text-field v-model="paper_link" label="Link your Paper"></v-text-field>
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
      showModal: false, loading: true, submit_in_progress: false,
      task_id: extractTaskFromCurrentUrl(), display_name: 'loading ...',
      description: 'loading ...', paper_link: 'loading...',
    }
  },
  computed: {
    component_name() {return this.type === 'docker' ? 'Edit Software' : 'Edit Upload Group'},
  },
  methods: {
    showEditModal() {
      this.loading = true
      let url = null
      if (this.type === 'docker') {
        url = '/api/docker-softwares-details/' + this.user_id + '/' + this.id
      }
      if (this.type === 'upload') {
        url = `/api/upload-group-details/${this.task_id}/${this.user_id}/${this.id}`
      }

      get(url)
          .then(inject_response(this, {'loading': false}, false, ['docker_software_details', 'upload_group_details']))
          .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
      this.showModal = true;
    },

    cancelEdit() {
      this.showModal = false
    },
    submitEdit() {
      this.submit_in_progress = true;
      const url = this.type === 'docker' ? `/task/${this.task_id}/vm/${this.user_id}/save_software/docker/${this.id}` : `/task/${this.task_id}/vm/${this.user_id}/save_software/upload/${this.id}`

      post(url, {
            'display_name': this.display_name,
            'description': this.description,
            'paper_link': this.paper_link,
      }, true)
      .then(() => {
        this.$emit('edit', {'id': this.id, 'display_name': this.display_name, 'description': this.description, 'paper_link': this.paper_link})
        this.showModal = false
      })
      .catch(reportError("Problem while Saving Submission Details.", "This might be a short-term hiccup, please try again. We got the following error: "))
      .then(() => { this.submit_in_progress = false })
    },
  }
};
</script>
