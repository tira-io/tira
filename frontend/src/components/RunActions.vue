<template>
  <div :class="!$vuetify.display.mdAndUp? ' d-flex flex-column w-100 justify-space-evenly' : 'd-flex'">
  <v-dialog v-if="role === 'admin'">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" icon="mdi-gavel" rounded density="compact" v-bind="props"/>
        <v-btn class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" prepend-icon="mdi-gavel" rounded density="compact" min-width="180" v-bind="props"><p>Re-evaluate</p></v-btn>
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
    <v-btn v-if="link_results != null && link_run == null" :href="link_results" target="_blank" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" icon="mdi-file-download-outline" rounded density="compact"/>
   <v-btn v-if="link_results != null && link_run == null" :href="link_results" target="_blank" class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" min-width="180" prepend-icon="mdi-file-download-outline" rounded density="compact"><p>Download run</p></v-btn>
   <v-tooltip activator="parent" location="top">Download run</v-tooltip>
  </span>
  

  <v-menu v-if="link_run != null && link_results != null" transition="slide-y-transition">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn v-bind="props" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" icon="mdi-file-download-outline" rounded density="compact"/>
        <v-btn v-bind="props" class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" prepend-icon="mdi-file-download-outline" min-width="180" rounded density="compact"><p>Download run</p></v-btn>
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
    <v-btn v-if="link_serp != null" icon="mdi-search-web" :href="link_serp" target="_blank" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" rounded density="compact"/>
    <v-btn v-if="link_serp != null" prepend-icon="mdi-search-web" :href="link_serp" target="_blank" class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" min-width="180" rounded density="compact"><p>Show SERP</p></v-btn>
    <v-tooltip activator="parent" location="top">Show SERP in new tab</v-tooltip>
  </span>

  <span>
    <v-btn v-if="link_code != null" icon="mdi-code-json" :href="link_code" target="_blank" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" rounded density="compact"/>
    <v-btn v-if="link_code != null" prepend-icon="mdi-code-json" :href="link_code" target="_blank" class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" min-width="180" rounded density="compact"><p>Show Code</p></v-btn>
    <v-tooltip activator="parent" location="top">Show Code in new tab</v-tooltip>
  </span>

  <span v-if="role === 'admin' || run['owned_by_user']">
    <run-review-window :run_id="run.run_id" :vm_id="run.vm_id" :dataset_id_from_props="run.dataset_id" @reviewRun="(i: any) => $emit('review-run', i)"/>
    <v-tooltip activator="parent" location="top">Review</v-tooltip>
  </span>

  <v-dialog v-if="run['owned_by_user']">
    <template v-slot:activator="{ props }">
      <span>
        <v-btn icon="mdi-delete" :disabled="!can_delete" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" rounded density="compact" v-bind="props"/>
        <v-btn prepend-icon="mdi-delete" :disabled="!can_delete" class="pa0 ma0 d-md-none d-flex justify-space-between" min-width="180" rounded density="compact" v-bind="props"><p>Delete run</p></v-btn>
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
</div>
</template>
<script lang="ts">
import { extractRole, get, reportSuccess, reportError } from '../utils'
import RunReviewWindow from './RunReviewWindow.vue'

export default {
  name: "run-actions",
  props: ['run'],
  components: { RunReviewWindow },
  emits: ['review-run'],
  data() { return {
    role: extractRole(),
    start_evaluation_is_pending: false,
    delete_is_pending: false,
  }},
  computed: {
    link_code() {
      return this.run && 'link_code' in this.run ? this.run['link_code'] : null;
    },
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
