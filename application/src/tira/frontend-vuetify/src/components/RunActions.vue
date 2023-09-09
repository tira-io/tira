<template>
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

  <span v-if="role == 'admin'">
    <run-review-window :run_id="run.run_id" :vm_id="run.vm_id"/>
    <v-tooltip activator="parent" location="top">Review</v-tooltip>
  </span>

  <span>
    <v-btn icon="mdi-delete" :disabled="!can_delete" class="pa0 ma0" rounded density="compact"/>
    <v-tooltip activator="parent" location="top" v-if="!can_delete">You can not delete runs that are published and/or valid. Please contact the organizer to delete this run.</v-tooltip>
    <v-tooltip activator="parent" location="top" v-if="can_delete">Attention, this will delete this run.</v-tooltip>
  </span>
</template>
<script lang="ts">
import { extractRole } from '../utils'
import RunReviewWindow from './RunReviewWindow.vue'

export default {
  name: "run-actions",
  props: ['run'],
  components: { RunReviewWindow },
  data() { return {
    role: extractRole()
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
    }
  },
}
</script>
  