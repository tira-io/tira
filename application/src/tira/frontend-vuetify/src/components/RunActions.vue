<template>
  <v-btn v-if="link_results != null && link_run == null" :href="link_results" target="_blank" class="mx-2">
    <v-icon>mdi-file-download-outline</v-icon>
    <v-tooltip activator="parent" location="top">Download results</v-tooltip>
  </v-btn>
  <v-btn v-if="link_run != null && link_results == null" :href="link_run" target="_blank" class="mx-2">
    <v-icon>mdi-file-chart-check-outline</v-icon>
    <v-tooltip activator="parent" location="top">Download run</v-tooltip>
  </v-btn>

  <v-menu v-if="link_run != null && link_results != null" transition="slide-y-transition">
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" class="mx-2">
        <v-icon>mdi-file-download-outline</v-icon>
        <v-tooltip activator="parent" location="top">Download run</v-tooltip>
      </v-btn>
    </template>
    <v-list>
      <v-list-item>
        <v-btn :href="link_run" target="_blank" class="mx-2">
          <v-icon>mdi-file-chart-check-outline</v-icon>
          <v-tooltip activator="parent" location="top">Download run</v-tooltip>
        </v-btn>
        <v-btn :href="link_results" target="_blank" class="mx-2">
          <v-icon>mdi-file-download-outline</v-icon>
          <v-tooltip activator="parent" location="top">Download results</v-tooltip>
        </v-btn>
      </v-list-item>
    </v-list>
  </v-menu>

  <v-btn v-if="link_serp != null" :href="link_serp" target="_blank" class="mr-2">
    <v-icon>mdi-search-web</v-icon>
    <v-tooltip activator="parent" location="top">Show SERP in new tab</v-tooltip>
  </v-btn>
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
  