<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-data-table v-if="dataset_id" v-model:expanded="expanded" show-expand :headers="table_headers"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" density="compact"
                  show-select class="elevation-1 d-none d-md-block" hover>
      <template v-slot:item.actions="{item}">
        <run-actions :run="item.value" />
      </template>
      <template #item.vm_id="{ item }">
        <span v-if="item.value.is_software">
          <v-icon>mdi-docker</v-icon>
          <v-tooltip activator="parent" location="top">Software Submission</v-tooltip>
        </span>
        <span v-if="item.value.is_upload">
          <v-icon>mdi-file-document</v-icon>
          <v-tooltip activator="parent" location="top">Run Submission</v-tooltip>
        </span>
        <span v-if="!item.value.published" class="mr1">
          <v-icon>mdi-eye-off-outline</v-icon>
          <v-tooltip activator="parent" location="top">Not Published on Leaderboard</v-tooltip>
        </span>
        <span v-if="item.value.published" class="mr1">
          <v-icon>mdi-eye-outline</v-icon>
          <v-tooltip activator="parent" location="top">Published on Leaderboard</v-tooltip>
        </span>
        <a target="_blank" :href="item.value.link_to_team">{{ item.value.vm_id }}</a>
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            <software-details :run="item.value" :columns_to_skip="table_headers" :organizer="organizer" :organizer_id="organizer_id"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-data-table v-if="dataset_id" v-model:expanded="expanded" show-expand :headers="table_headers_small_layout"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" expand-on-click density="compact"
                  class="elevation-1 d-md-none" hover>
                  <template #item.vm_id="{ item }">
        <a target="_blank" :href="item.value.link_to_team">{{ item.value.vm_id }}</a>
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length">
            <software-details :run="item.value" :columns_to_skip="table_headers_small_layout" :organizer="organizer" :organizer_id="organizer_id"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <div v-if="dataset_id" class="d-none d-md-block">
      <v-row class="pt-2">
        <v-col cols="6"><v-btn variant="outlined" block>Download Selected</v-btn></v-col>
        <v-col cols="6"><v-btn variant="outlined" block>Compare Selected</v-btn></v-col>
      </v-row>
    </div>
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
  props: ['task_id', 'dataset_id', 'organizer', 'organizer_id'],
  data() { return {
      expanded: [],
      loading: true,
      runs: [],
      table_headers: [],
      table_headers_small_layout: [],
      table_sort_by: [],
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      get('/api/evaluations/' + this.task_id + '/' + this.dataset_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError("Problem While Loading the List of Runs", "This might be a short-term hiccup, please try again. We got the following error: "))
      }
  },
  beforeMount() {this.fetchData()},
  watch: {
    dataset_id(old_id, new_id) {this.fetchData()},
    task_id(old_id, new_id) {this.fetchData()},
  }
}
</script>