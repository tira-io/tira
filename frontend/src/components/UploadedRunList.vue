<template>
  <loading :loading="loading" />
  <div v-if="!loading">
    <v-data-table show-expand :headers="headers" v-model:sort-by="sort_by" :items="runs"
      item-value="run_id" density="compact" >
      <template v-slot:item.actions="{ item }">
        <run-actions :run="item" :task_id="task_id" />
      </template>
      <template #item.dataset_id="{ item }">
        <submission-icon :submission="item" /> {{ item.dataset_id }}
      </template>

      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" style="background-color: white;" class="px-0 mx-0">
            {{ item }}
          </td>
        </tr>
      </template>
    </v-data-table>
  </div>
</template>

<script lang="ts">
import { inject } from 'vue'

import RunActions from './RunActions.vue'
import Loading from "./Loading.vue"
import SubmissionIcon from "./SubmissionIcon.vue"
import { get_from_archive, reportError, inject_response, type UserInfo } from '../utils'


export default {
  name: "uploaded-runs-list",
  components: { RunActions, Loading, SubmissionIcon },
  props: ['task_id', 'vm_id'],
  data() {
    return {
      userinfo: inject('userinfo') as UserInfo,
      selected_runs: [],
      loading: true,
      runs: [{ 'run_id': 'loading...', 'review_state': 'no-review', 'vm_id': '1', 'link_to_team': 'link', 'dataset_id': '1' }],
      headers: [{
          "title": "Dataset",
          "key": "dataset_id"
        }, {
          "title": "Run",
          "key": "input_software_name"
        }, {
          "title": "Uploaded",
          "key": "run_id"
        }, {
          "title": "",
          "key": "actions",
          "sortable": false
        }
    ],
    sort_by: [{"key": "run_id", "order": "desc"}]
    }
  },
  methods: {
    fetchData() {
      console.log("fetch data in list....")
      this.loading = true
      var rest_endpoint = '/api/evaluations-of-vm/' + this.task_id + '/' + this.vm_id + '?upload_id=all-uploads'
      get_from_archive(rest_endpoint, false)
        .then(inject_response(this, { 'loading': false }))
        .catch(reportError("Problem While Loading the List of Runs", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
  },
  beforeMount() {
    this.fetchData()
  },
  watch: {
    task_id(old_id, new_id) { this.fetchData() },
  }
}
</script>
