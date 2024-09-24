<template>
  <div v-if="items.length != 0">
    <h2>Import Submission from Other Task</h2>
    <v-row>
      <v-col cols="9">
        <v-autocomplete label="Submission to Import" :items="items" v-model="selectedImport" item-value="id" item-title="title" clearable block/>
      </v-col>
      <v-col cols="3">
        <v-btn :disabled="selectedImport + '' === 'undefined' || selectedImport + '' === ''" @click="importDataset" block>Import</v-btn>
      </v-col>
    </v-row>
  </div>
</template>

<script lang="ts">
import { inject } from 'vue'

import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, reportError, inject_response } from '../utils'
import { VAutocomplete } from "vuetify/components"

export default {
  name: "import-submission",
  props: ['submission_type'],
  emits: ['addEntry'],
  components: { VAutocomplete },
  data() { return {
    task_id: extractTaskFromCurrentUrl(),
    submissions_of_user: [{'task_id': 'loading', 'title': 'loading', 'type': 'loading', 'id': 'loading'}],
    selectedImport: undefined, user_id_for_submission: extractUserFromCurrentUrl(),
  }},
  computed: {
    items() {
      return this.submissions_of_user.filter((i) => i['type'] == this.submission_type && i['task_id'] != this.task_id);
    }
  },
  methods: {
    importDataset() {
        get(inject("REST base URL")+'/api/import-submission/' + this.task_id + '/' + this.user_id_for_submission + '/' + this.submission_type + '/' + this.selectedImport)
    }
  },
  beforeMount() {
    get(inject("REST base URL")+'/api/submissions-of-user/' + this.user_id_for_submission)
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading Existing Submissions.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
