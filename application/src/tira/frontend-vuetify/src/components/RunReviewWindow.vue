<template>
<v-dialog width="auto" scrollable>
  <template v-slot:activator="{ props }">
    <v-btn icon="mdi-tooltip-edit" class="pa0 ma0" @click="clicked()" rounded v-bind="props" density="compact"/>
  </template>
  <template v-slot:default="{ isActive }">
    <v-card>
      <loading :loading="loading" />
      <card-title>
        <v-toolbar v-if="!loading" color="primary" :title="'Details of Run ' + run_id">
          <template v-slot:extension  class="mx2">
            <v-tabs v-model="tab" align-tabs="title">
              <v-tab v-for="item in items" :key="item.run_id" :value="item.run_id" >{{ item.display_name }}</v-tab>
            </v-tabs>
          </template>
        </v-toolbar>
      </card-title>
    
      <v-card-text>
      <v-window v-if="!loading" v-model="tab">
        <v-window-item v-for="item in items" :key="item.run_id" :value="item.run_id">
          <v-card flat>
            <v-card-text><run-review-form :run_id="item.run_id" :vm_id="vm_id"/></v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
      
    </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="isActive.value = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </template>
</v-dialog>
</template>
  
<script lang="ts">
import Loading from './Loading.vue'
import RunReviewForm from './RunReviewForm.vue'
import { get, reportError, inject_response } from '../utils'

export default {
    name: "run-review-window",
    components: { Loading, RunReviewForm },
    props: ['run_id', 'vm_id'],
    data() {
      return {
        evaluations: [],
        tab: null,
        loading: true,
        evaluation_data: {},
        text: 'saa',
      }
    },
    computed: {
        items() {
            var ret = [{'display_name': 'Run', 'run_id': this.run_id}] 
           
            for (const i in this.evaluations) {
              console.log(i+1)
              ret.push({'display_name': 'Evaluation ' + (parseInt(i) + 1), 'run_id': this.evaluations[i]})
            }

            return ret;
        }
    },
    methods: {
      clicked: function() {
        this.loading = true
        get('/api/evaluations_of_run/' + this.vm_id + '/' + this.run_id)
          .then(inject_response(this, {'loading': false}))
          .catch(reportError("Problem While Loading the the runs and evaluations for review", "This might be a short-term hiccup, please try again. We got the following error: "))
      }
    },
  }
  </script>
  