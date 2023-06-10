<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-data-table v-if="dataset_id" v-model:expanded="expanded" show-expand :headers="headers"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" density="compact"
                  show-select class="elevation-1 d-none d-md-block" hover>
      <template v-slot:item.actions="{item}">
        <run-actions :run_id="item.Run" />
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            <software-details :software_id="item.Run"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-data-table v-if="dataset_id" v-model:expanded="expanded" show-expand :headers="headers_small_layout"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" density="compact"
                  show-select class="elevation-1 d-md-none" hover>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            <software-details :software_id="item.Run"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-row v-if="dataset_id" class="pt-2">
      <v-col cols="6"><v-btn variant="outlined" block>Download Selected</v-btn></v-col>
      <v-col cols="6"><v-btn variant="outlined" block>Compare Selected</v-btn></v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import RunActions from './RunActions.vue'
import SoftwareDetails from './SoftwareDetails.vue'
import Loading from "./Loading.vue"
import { get, reportError, inject_response } from '../utils'

export default {
  name: "run-list",
  components: {RunActions, SoftwareDetails, Loading},
  props: ['task_id', 'dataset_id'],
  data() { return {
      expanded: [],
      loading: true,
      runs: [],
      headers: [],
      headers_small_layout: [],
      table_sort_by: [],
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      get('/api/evaluations/' + this.task_id + '/' + this.dataset_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError)
      }
  },
  beforeMount() {this.fetchData()},
  watch: {
    dataset_id(old_id, new_id) {this.fetchData()},
    task_id(old_id, new_id) {this.fetchData()},
  }
}
</script>