<template>
  <v-card>
    <v-card-actions>
      <v-row>
        <v-col cols="4">
          <v-autocomplete  label="Dataset" :items="datasets" item-title="display_name" item-value="dataset_id"
                           variant="underlined" clearable multiple
                           @update:modelValue="(to_emit) => $emit('pass_dataset', to_emit)"
                           v-model="filtered_datasets"/>
        </v-col>
        <v-col cols="4">
          <v-autocomplete label="Evaluation Measures" :items="ev_keys"
                          variant="underlined" clearable multiple
                          @update:modelValue="(to_emit) => $emit('pass_keys', to_emit)"
                          v-model="filtered_ev_keys"/>
        </v-col>
        <v-col cols="4" v-if="component_type === 'Overview'">
          <v-autocomplete label="Approach" :items="computedRuns" :item-title="['input_software_name']"
                          variant="underlined" clearable multiple return-object
                          @update:modelValue="(to_emit) => $emit('pass_runs', to_emit)"
                          v-model="filtered_runs"/>
        </v-col>
      </v-row>
    </v-card-actions>
  </v-card>
</template>
<script>

import {VAutocomplete} from "vuetify/components";

export default {
  name: 'submission-filter',
  components: {VAutocomplete},
  props: ['datasets', 'selected_dataset', 'ev_keys', 'runs', 'component_type'],
  data() {
    return {
      filtered_datasets: [],
      filtered_ev_keys: [],
      filtered_runs: [],
    }
  },
  updated() {
    this.filtered_ev_keys = this.ev_keys

    if (this.selected_dataset.split(',').filter(x => x.length > 1).length === this.datasets.length){
      return this.filtered_datasets = []
    }
    else {
      return this.filtered_datasets = this.selected_dataset.split(',').filter(x => x.length > 1)
    }
  },
  computed: {
    computedRuns() {return this.removeDuplicateRuns(this.runs)},
  },
  methods:{
    updateFilteredRuns(){
      if (this.component_type === 'Overview'){
        this.filtered_runs = this.computedRuns
            .filter(run => this.filtered_runs
                .map(run => run['input_software_name'])
                .includes(run['input_software_name']))
        this.$emit('pass_runs', this.filtered_runs)
      }
    },
    removeDuplicateRuns(runs) {
      let approaches = new Set();
      return runs
          .filter(run => run.hasOwnProperty('input_software_name'))
          .filter(run => {
            if (!approaches.has(run['input_software_name'])) {
              approaches.add(run['input_software_name'])
              return true
            }
            return false
          })
    }
  },
  watch: {
    filtered_datasets(old_value, new_value){this.updateFilteredRuns()}
  }
}
</script>