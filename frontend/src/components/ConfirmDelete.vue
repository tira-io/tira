<template>
    <v-dialog>
      <template v-slot:activator="{ props }">
        <v-btn :disabled="disabled" color="primary" prepend-icon="mdi-delete" size="large" v-bind="props" />
      </template>
      <template v-slot:default="{ isActive }">
        <v-card class="pb-1">
          <card-title>
            <v-toolbar color="primary" :title="label"/>
          </card-title>
        
          <v-card-text>
            Please click confirm to delete the selected record, or close to cancel.
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-row>
            <v-col cols="6"><v-btn variant="outlined" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6"><v-btn variant="outlined" @click="$emit('delete-confirmed', to_delete); isActive.value = false" block>Confirm</v-btn></v-col>
          </v-row>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
    </template>
        
<script lang="ts">
    export default {
      name: "confirm-delete",
      emits: ['delete-confirmed'],
      props: ['label', 'disabled', 'to_delete'],
    }
</script>
