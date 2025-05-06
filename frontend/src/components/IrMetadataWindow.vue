<template>
  <v-dialog width="auto" scrollable>
    <template v-slot:activator="{ props }">
        <v-btn icon="mdi-code-json" v-bind="props" :class="!$vuetify.display.mdAndUp ? 'pa0 ma0 d-none' : 'pa0 ma0'" rounded density="compact" />
      <v-btn prepend-icon="mdi-code-json"
        class="pa0 ma0 mb-2 d-md-none d-flex justify-space-between" v-bind="props" min-width="180" rounded density="compact">
        <p>Show ir_metadata</p>
      </v-btn>
      <v-tooltip activator="parent" location="top">View ir_metadata</v-tooltip>

    </template>
    <template v-slot:default="{ isActive }">
        <v-card>
          <card-title>
            <v-toolbar color="primary" :title="'Browse ir_metadata of run ' + run.run_id">
            </v-toolbar>
          </card-title>
        
          <v-card-text>
            <ir-metadata-browser :items="run.valid_formats.ir_metadata" :dataset_id="run.dataset_id" :vm_id="run.vm_id" :run_id="run.run_id" :task_id="task_id" uuid="does-not-exist"/>
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-btn variant="text" @click="isActive.value = false">Close</v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
  </template>
<script lang="ts">

import IrMetadataBrowser from './IrMetadataBrowser.vue';

export default {
  name: "ir-metadata-window",
  components: {IrMetadataBrowser},
  props: ['run', 'task_id'],
}
</script>
