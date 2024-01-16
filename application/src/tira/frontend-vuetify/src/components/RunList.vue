<template>
  <loading :loading="loading"/>
  <div v-if="!loading">
    <v-data-table v-if="showTable" v-model="selected_runs" show-expand :headers="table_headers"
                  :items="runs" item-value="run_id" v-model:sort-by="table_sort_by" density="compact"
                  show-select class="elevation-1 d-none d-md-block" hover>
      <template v-slot:item.actions="{item}">
        <run-actions :run="item" @reviewRun="(i: any) => reviewChanged(i)"/>
      </template>
      <template #item.vm_id="{ item }">
        <submission-icon :submission="item" />
        <a v-if="role != 'admin'" target="_blank" :href="item.link_to_team">{{ item.vm_id }}</a>

        <v-menu v-if="role == 'admin'" transition="slide-y-transition">
          <template v-slot:activator="{ props }">
            <a href="javascript:void(0)" v-bind="props">{{ item.vm_id }}</a>
          </template>
          <v-list>
            <v-list-item key="team-page"><a target="_blank" :href="item.link_to_team">Team Page of {{ item.vm_id }}</a></v-list-item>
            <v-list-item key="submission-page"><a target="_blank" :href="'/submit/' + task_id + '/user/' + item.vm_id">Submission Page of {{ item.vm_id }}</a></v-list-item>
          </v-list>
        </v-menu>
      </template>

      <template #item.dataset_id="{ item }">
        <submission-icon :submission="item"/> {{ item.dataset_id }}
      </template>

      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" style="background-color: white;" class="px-0 mx-0">
            <software-details :run="item" :columns_to_skip="table_headers" :organizer="organizer" :organizer_id="organizer_id"/>
          </td>
        </tr>
      </template>
    </v-data-table>

    <v-data-table v-if="showTable" show-expand :headers="table_headers_small_layout"
                  :items="runs" item-value="Run" v-model:sort-by="table_sort_by" expand-on-click density="compact"
                  class="elevation-1 d-md-none" hover>
                  <template #item.vm_id="{ item }">
        <a target="_blank" :href="item.link_to_team">{{ item.vm_id }}</a>
      </template>
      <template v-slot:expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" style="background-color: white;"  class="px-0 mx-0">
            <software-details :run="item" :columns_to_skip="table_headers_small_layout" :organizer="organizer" :organizer_id="organizer_id" @reviewRun="(i: any) => reviewChanged(i)"/>
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
  </div>
</template>

<script lang="ts">
import RunActions from './RunActions.vue'
import SoftwareDetails from './SoftwareDetails.vue'
import Loading from "./Loading.vue"
import SubmissionIcon from "./SubmissionIcon.vue"
import { get, reportError, inject_response, extractRole } from '../utils'


export default {
  name: "run-list",
  components: {RunActions, SoftwareDetails, Loading, SubmissionIcon},
  props: ['task_id', 'dataset_id', 'organizer', 'organizer_id', 'vm_id', 'docker_software_id', 'upload_id', 'show_only_unreviewed'],
  data() { return {
      selected_runs: [],
      loading: true,
      runs: [{'run_id': 'loading...', 'review_state': 'no-review', 'vm_id': '1', 'link_to_team': 'link', 'dataset_id': '1'}],
      table_headers: [],
      table_headers_small_layout: [],
      table_sort_by: [],
      role: extractRole(), // Values: guest, user, participant, admin
    }
  },
  computed: {
    downloadLink() {return '';},
    compareLink() {return this.createCompareLink(this.selected_runs);},
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
        
        if (this.show_only_unreviewed) {
          rest_endpoint += '?show_only_unreviewed=true'
        }
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
    },
    reviewChanged(review: any) {
      for (let run of this.runs) {
        if (run['run_id'] === review['run_id']) {
          if ('review_state' in review && 'review_state' in run) {
            run['review_state'] = review['review_state']
          }
          if ('published' in review && 'published' in run) {
            run['published'] = review['published']
          }
          if ('blinded' in review && 'blinded' in run) {
            run['blinded'] = review['blinded']
          }
        }
      }
    }
  },
  beforeMount() {this.fetchData()},
  watch: {
    dataset_id(old_id, new_id) {this.fetchData()},
    task_id(old_id, new_id) {this.fetchData()},
  }
}
</script>
