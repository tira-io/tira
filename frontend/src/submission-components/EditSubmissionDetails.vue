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
          <v-text-field v-model="display_name" label="Name"/>
          <v-textarea v-model="description" label="Description"/>
          <template v-if="additionalUploadFormFields.length > 0">
            <template v-for="field in additionalUploadFormFields" :key="field.name">
              <v-select
                v-if="field.type === 'select'"
                v-model="field_values[field.name]"
                :label="field.display_name"
                :items="field.options"
                item-title="display_value"
                item-value="id"
                :rules="fieldRules(field)"
              />
              <v-textarea
                v-else-if="field.type === 'textarea'"
                v-model="field_values[field.name]"
                :label="field.display_name"
                :rules="fieldRules(field)"
              />
              <v-text-field
                v-else
                v-model="field_values[field.name]"
                :label="field.display_name"
                :type="textFieldType(field)"
                :rules="fieldRules(field)"
              />
            </template>
          </template>
          <v-text-field v-model="paper_link" label="Link your Paper"/>
          <v-checkbox v-model="ir_re_ranker" label="Is this software an re-ranker?" v-if="is_ir_task && type == 'docker'"/>
          <v-checkbox v-model="ir_re_ranking_input" label="Is the output of this component a run file to be re-ranked by others?" v-if="is_ir_task"/>
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
import { inject } from 'vue'

import {extractTaskFromCurrentUrl, get, inject_response, post, reportError} from "@/utils";
import {Loading} from "@/components";

export default {
  name: 'edit-submission-details',
  components: {Loading},
  props: ['type', 'id', 'user_id', 'is_ir_task', 'upload_form_fields'],
  emits: ['edit'],
  data() {
    return {
      showModal: false, loading: true, submit_in_progress: false,
      task_id: extractTaskFromCurrentUrl(), display_name: 'loading ...',
      description: 'loading ...', paper_link: 'loading...',
      ir_re_ranker: false, ir_re_ranking_input: false,
      metadata: null, upload_metadata: null, field_values: {},
      rest_url: inject("REST base URL")
    }
  },
  computed: {
    component_name() {return this.type === 'docker' ? 'Edit Software' : 'Edit Upload Group'},
    additionalUploadFormFields() {
      if (!Array.isArray(this.upload_form_fields) || this.upload_form_fields.length === 0) {
        return []
      }

      // The Name/Description fields are always shown on their own (see the
      // template above); upload_form_fields only ever adds further fields on
      // top of those two, so any configured field reusing one of those two
      // names is dropped here to avoid showing/editing the same value twice.
      return this.upload_form_fields.filter(field =>
        field
        && typeof field.name === 'string'
        && typeof field.display_name === 'string'
        && typeof field.type === 'string'
        && field.name !== 'display_name'
        && field.name !== 'description'
        && (field.type !== 'select' || this.hasValidSelectOptions(field))
      )
    },
  },
  methods: {
    hasValidSelectOptions(field) {
      return Array.isArray(field.options)
        && field.options.length > 0
        && field.options.every(option =>
          option
          && typeof option.id === 'string'
          && option.id.trim() !== ''
          && typeof option.display_value === 'string'
          && option.display_value.trim() !== ''
        )
    },
    fieldRules(field) {
      if (field.required === false) {
        return []
      }

      if (field.type === 'select') {
        return [v => !!(v && v.toString().trim().length > 0) || `Please select ${field.display_name.toLowerCase()}.`]
      }

      return [v => !!(v && v.toString().trim().length > 0) || `Please provide ${field.display_name.toLowerCase()}.`]
    },
    textFieldType(field) {
      return field.type === 'number' || field.type === 'url' || field.type === 'email' ? field.type : 'text'
    },
    showEditModal() {
      this.loading = true
      let url = null
      if (this.type === 'docker') {
        url = this.rest_url + '/api/docker-softwares-details/' + this.user_id + '/' + this.id
      }
      if (this.type === 'upload') {
        url = this.rest_url + `/api/upload-group-details/${this.task_id}/${this.user_id}/${this.id}`
      }

      get(url)
          .then(inject_response(this, {'loading': false}, false, ['docker_software_details', 'upload_group_details']))
          .then(() => { this.initializeFieldValues() })
          .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
      this.showModal = true;
    },
    initializeFieldValues() {
      const rawMetadata = (this.type === 'docker' ? this.metadata : this.upload_metadata) || {}
      const nextValues = {}

      for (const field of this.additionalUploadFormFields) {
        nextValues[field.name] = rawMetadata[field.name] ?? ''
      }

      this.field_values = nextValues
    },

    cancelEdit() {
      this.showModal = false
    },
    submitEdit() {
      this.submit_in_progress = true;
      const url = this.type === 'docker' ? `/task/${this.task_id}/vm/${this.user_id}/save_software/docker/${this.id}` : `/task/${this.task_id}/vm/${this.user_id}/save_software/upload/${this.id}`

      const hasAdditionalFields = this.additionalUploadFormFields.length > 0
      const rawMetadata = (this.type === 'docker' ? this.metadata : this.upload_metadata) || {}
      // Name/Description are always directly editable now (see the template
      // above); upload_form_fields only ever contribute further metadata on
      // top of those two, so the metadata submitted here is the merge of
      // whatever was already there plus the (possibly empty) extra fields.
      const metadataToSubmit = hasAdditionalFields ? { ...rawMetadata, ...this.field_values } : rawMetadata

      const display_name = this.display_name
      const description = this.description

      let params = {'display_name': display_name, 'description': description, 'paper_link': this.paper_link}

      if (this.type === 'docker') {
        params['metadata'] = metadataToSubmit
      } else {
        params['upload_metadata'] = metadataToSubmit
      }

      if(this.is_ir_task) {
        params['ir_re_ranking_input'] = this.ir_re_ranking_input

        if (this.type === 'docker') {
            params['ir_re_ranker'] = this.ir_re_ranker
        }
      }

      post(url, params, true)
      .then(() => {
        this.$emit('edit', {'id': this.id, 'display_name': display_name, 'description': description, 'paper_link': this.paper_link})
        this.showModal = false
      })
      .catch(reportError("Problem while Saving Submission Details.", "This might be a short-term hiccup, please try again. We got the following error: "))
      .then(() => { this.submit_in_progress = false })
    },
  }
};
</script>
