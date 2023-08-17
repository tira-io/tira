<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-data-table v-if="showTable" v-model="selected_runs" v-model:expanded="expanded" show-expand :headers="table_headers"
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
          <td :colspan="columns.length" style="background-color: white;" class="px-0 mx-0">
            <software-details :run="item.value" :columns_to_skip="table_headers" :organizer="organizer" :organizer_id="organizer_id"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-data-table v-if="showTable" v-model:expanded="expanded" show-expand :headers="table_headers_small_layout"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" expand-on-click density="compact"
                  class="elevation-1 d-md-none" hover>
                  <template #item.vm_id="{ item }">
        <a target="_blank" :href="item.value.link_to_team">{{ item.value.vm_id }}</a>
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" style="background-color: white;"  class="px-0 mx-0">
            <software-details :run="item.value" :columns_to_skip="table_headers_small_layout" :organizer="organizer" :organizer_id="organizer_id"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <div v-if="showTable" class="d-none d-md-block">
      <v-row class="pt-2">
        <v-col cols="6"><v-btn variant="outlined" block :disabled="downloadLink === ''" :href="downloadLink" target="_blank">Download Selected</v-btn></v-col>
        <v-col cols="6"><v-btn variant="outlined" block :disabled="compareLink === ''" :href="compareLink" target="_blank">Compare Selected</v-btn></v-col>
      </v-row>
    </div>
    <div v-if="showTable" class="d-md-none d-md-block">
      <v-row class="pt-2">
        <v-col cols="12"><v-btn variant="outlined" block :disabled="compareExpandedLink === ''" :href="compareExpandedLink" target="_blank">Compare Expanded</v-btn></v-col>
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
  props: ['task_id', 'dataset_id', 'organizer', 'organizer_id', 'vm_id', 'docker_software_id', 'upload_id'],
  data() { return {
      expanded: [],
      selected_runs: [],
      loading: true,
      runs: [],
      table_headers: [],
      table_headers_small_layout: [],
      table_sort_by: [],
    }
  },
  computed: {
    downloadLink() {return '';},
    compareLink() {return this.createCompareLink(this.selected_runs);},
    compareExpandedLink() {return this.createCompareLink(this.expanded);},
    showTable() {return this.dataset_id || this.vm_id}
  },
  methods: {
    createCompareLink(src: any[]) {
      let candidates : string[] = []

      for (var s of src) {
        if('selectable' in s && s['selectable']) {
          candidates.push(s['run_id'])
        }
      }

      if (candidates.length >= 2) {
        return '/diffir/' + this.task_id + '/10/' + candidates[0] + '/' + candidates[1]
      } else {
        return '';
      }
    },
    fetchData() {
      this.loading = true
      var rest_endpoint = ''
      if (this.task_id && this.dataset_id) {
        rest_endpoint = '/api/evaluations/' + this.task_id + '/' + this.dataset_id
      } else if (this.task_id && this.vm_id) {
        rest_endpoint = '/api/evaluations-of-vm/' + this.task_id + '/' + this.vm_id 
        
        if (this.docker_software_id) {
          rest_endpoint += '?docker_software_id=' + this.docker_software_id
        } else if (this.upload_id) {
          rest_endpoint += '?upload_id=' + this.upload_id
        }
      }

      get(rest_endpoint)
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