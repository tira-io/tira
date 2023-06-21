<template>
<v-dialog transition="dialog-bottom-transition" width="auto">
  <template v-slot:activator="{ props }">
    <v-btn icon="mdi-tooltip-edit" class="pa0 ma0" @click="clicked()" rounded v-bind="props" density="compact"/>
  </template>
  <template v-slot:default="{ isActive }">
    <v-card>
      <loading :loading="loading" />
      <v-toolbar v-if="!loading" color="primary" :title="'Details of Run ' + run_id">
        <template v-slot:extension  class="mx2">
          <v-tabs v-model="tab" align-tabs="title">
            <v-tab v-for="item in items" :key="item.display_name" :value="item.run_id" >{{ item.display_name }}</v-tab>
          </v-tabs>
        </template>
      </v-toolbar>

      <v-window v-if="!loading" v-model="tab">
        <v-window-item v-for="item in items" :key="item.run_id" :value="item">
          <v-card flat>
            <v-card-text v-text="text"></v-card-text>
          </v-card>
        </v-window-item>
      </v-window>

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="isActive.value = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </template>
</v-dialog>    
</template>
  
<script lang="ts">
import Loading from './Loading.vue'
import { get, reportError, inject_response } from '../utils'

export default {
    name: "run-review-window",
    components: { Loading },
    props: ['run_id'],
    data() {
      return {
        evaluations: [],
        tab: null,
        loading: true,
        text: 'saa',
      }
    },
    computed: {
        items() {
            return [{'display_name': 'Run', 'run_id': this.run_id}]
        }
    },
    methods: {
      clicked: function() {
        this.loading = true
        get('/api/evaluations_of_run/' + this.run_id)
          .then(inject_response(this, {'loading': false}))
          .catch(reportError("Problem While Loading the the runs and evaluations for review", "This might be a short-term hiccup, please try again. We got the following error: "))
      }
    },
  }
  </script>
  