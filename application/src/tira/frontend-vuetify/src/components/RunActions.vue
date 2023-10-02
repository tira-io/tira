<template>
  <v-dialog v-if="role === 'admin'">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn class="pa0 ma0" icon="mdi-gavel" rounded density="compact" v-bind="props" />
        <v-tooltip activator="parent" location="top">Re-run the evaluation on this run</v-tooltip>
      </span>
    </template>
    <template v-slot:default="{ isActive }">
      <v-card class="pb-1">
        <card-title>
          <v-toolbar color="primary" title="Run Evaluation Again?"/>
        </card-title>
        <v-card-text>
          Please click confirm to run the evaluation on this run again, or close to cancel.
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-row>
            <v-col cols="6"><v-btn variant="outlined" :loading="start_evaluation_is_pending" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6"><v-btn variant="outlined" :loading="start_evaluation_is_pending" @click="runEvaluation(isActive)" block>Confirm</v-btn></v-col>
          </v-row>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>

  <span>
   <v-btn v-if="link_results != null && link_run == null" :href="link_results" target="_blank" class="pa0 ma0" icon="mdi-file-download-outline" rounded density="compact" />
   <v-tooltip activator="parent" location="top">Download run</v-tooltip>
  </span>
  

  <v-menu v-if="link_run != null && link_results != null" transition="slide-y-transition">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn v-bind="props" class="pa0 ma0" icon="mdi-file-download-outline" rounded density="compact"/>
        <v-tooltip activator="parent" location="top">Download run</v-tooltip>
      </span>
    </template>
    <v-list>
      <v-list-item>
        <v-btn :href="link_run" target="_blank" class="mx-2">
          <v-icon>mdi-file-chart-check-outline</v-icon>
          Download run
        </v-btn>
        <v-btn :href="link_results" target="_blank" class="mx-2">
          <v-icon>mdi-file-download-outline</v-icon>
          Download results
        </v-btn>
      </v-list-item>
    </v-list>
  </v-menu>

  <span>
    <v-btn v-if="link_serp != null" icon="mdi-search-web" :href="link_serp" target="_blank" class="pa0 ma0" rounded density="compact"/>
    <v-tooltip activator="parent" location="top">Show SERP in new tab</v-tooltip>
  </span>

  <span v-if="role === 'admin' || run['owned_by_user']">
    <run-review-window :run_id="run.run_id" :vm_id="run.vm_id" :dataset_id_from_props="run.dataset_id"/>
    <v-tooltip activator="parent" location="top">Review</v-tooltip>
  </span>

  <v-dialog v-if="run['owned_by_user']">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn icon="mdi-delete" :disabled="!can_delete" class="pa0 ma0" rounded density="compact" v-bind="props"/>
        <v-tooltip activator="parent" location="top" v-if="!can_delete">You can not delete runs that are published and/or valid. Please contact the organizer to delete this run.</v-tooltip>
        <v-tooltip activator="parent" location="top" v-if="can_delete">Attention, this will delete this run.</v-tooltip>
      </span>
    </template>
    <template v-slot:default="{ isActive }">
      <v-card class="pb-1">
        <card-title><v-toolbar color="primary" title="Delete Run"/></card-title>
        <v-card-text>Please click confirm to delete this run, or close to cancel.
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-row>
            <v-col cols="6"><v-btn variant="outlined" :loading="delete_is_pending" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6"><v-btn variant="outlined" :loading="delete_is_pending" @click="deleteRun(isActive)" block>Confirm</v-btn></v-col>
          </v-row>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>

</template>
<script lang="ts">
import { extractRole, get, reportSuccess, reportError } from '../utils'
import RunReviewWindow from './RunReviewWindow.vue'

export default {
  name: "run-actions",
  props: ['run'],
  components: { RunReviewWindow },
  data() { return {
    role: extractRole(),
    start_evaluation_is_pending: false,
    delete_is_pending: false,
  }},
  computed: {
    link_serp() {
      return this.run && 'link_serp' in this.run ? this.run['link_serp'] : null;
    },
    link_results() {
      return this.run && 'link_results_download' in this.run ? this.run['link_results_download'] : null;
    },
    link_run() {
      return this.run && 'link_run_download' in this.run ? this.run['link_run_download'] : null;
    },
    can_delete() {
      return this.run && 'published' in this.run && !this.run['published'] && 'review_state' in this.run && this.run['review_state'] != 'valid'
    },
  },
  methods: {
    runEvaluation(isActive: any) {
      this.start_evaluation_is_pending = true;
      get(`/grpc/${this.run.vm_id}/run_eval/${this.run.dataset_id}/${this.run.run_id}`)
      .then(reportSuccess('Successfully started the evaluation of run with id ' + this.run.run_id))
      .catch(reportError('Failed to start the evaluation of run with id ' + this.run.run_id, 'Maybe this is a short hiccupp, please try again.'))
      .then(() => { this.start_evaluation_is_pending = false;  isActive.value = false})
    },
    deleteRun(isActive: any) {
      this.delete_is_pending = true;
      get(`/grpc/${this.run.vm_id}/run_delete/${this.run.dataset_id}/${this.run.run_id}`)
      .then(reportSuccess('Successfully deleted the run with id ' + this.run.run_id))
      .catch(reportError('Failed to delete the run with id ' + this.run.run_id, 'Maybe this is a short hiccupp, please try again.'))
      .then(() => { this.delete_is_pending = false;  isActive.value = false})
    }
  }
}
</script>
  