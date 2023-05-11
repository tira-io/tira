<template>
  <v-btn href="#" target="_blank" class="mr-2">
    <v-icon>mdi-search-web</v-icon>
    <v-tooltip activator="parent" location="top">Show SERP in new tab</v-tooltip>
  </v-btn>
  <v-btn href="#" target="_blank" class="mx-2">
    <v-icon>mdi-file-download-outline</v-icon>
    <v-tooltip activator="parent" location="top">Download results</v-tooltip>
  </v-btn>
  <v-btn href="#" target="_blank" class="mx-2">
    <v-icon>mdi-file-chart-check-outline</v-icon>
    <v-tooltip activator="parent" location="top">Download run</v-tooltip>
  </v-btn>
</template>
<script lang="ts">
  
export default {
  name: "run-actions",
  props: ['run_id'],
  data() {
    return {}
  }
}
</script>
  