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
</template>
<script lang="ts">
import { tSExpressionWithTypeArguments } from '@babel/types';

  
export default {
  name: "run-actions",
  props: ['run'],
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
  },
}
</script>
  