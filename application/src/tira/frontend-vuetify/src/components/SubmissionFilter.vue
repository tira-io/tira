<template>
  <v-card>
    <v-card-subtitle>
      filter Submissions
    </v-card-subtitle>
    <v-card-actions>
      <v-row>
        <v-col cols="4" v-if="type === 'task'">
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
        <v-col cols="4" v-if="this.type === 'task'">
          <v-autocomplete label="Approach" :items="runs" :item-title="['input_software_name']"
                          variant="underlined" clearable multiple return-object
                          @update:modelValue="(to_emit) => $emit('pass_runs', to_emit)"
                          v-model="filtered_runs" />
        </v-col>
      </v-row>
    </v-card-actions>
  </v-card>
</template>

<script>

  import {Loading} from "@/components";
  import {VAutocomplete} from "vuetify/components";
export default {
  name: 'submission-filter',
  components: {Loading, VAutocomplete},
  props: ['datasets', 'selected_dataset', 'ev_keys', 'runs', 'type'],
  data() {
    return {
      loading: true,
      filtered_datasets: [],
      filtered_ev_keys: [],
      filtered_runs: [],
    }
  },
  beforeUpdate() {
    this.filtered_ev_keys = this.ev_keys
    this.filtered_datasets = this.selected_dataset.split(',')
  },
}
</script>