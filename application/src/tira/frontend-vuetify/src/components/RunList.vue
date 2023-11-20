<template>
  <submission-filter :datasets="datasets" :selected_dataset="dataset_ids"
                     :ev_keys="ev_keys" :runs="runs" :component_type="component_type" @pass_dataset="receiveFilteredDataset"
                     @pass_keys="receiveFilteredKeys" @pass_runs="receiveFilteredRuns"/>
  <div>
    <loading :loading="loading"/>
    <div v-if="!loading">
      <v-data-table v-if="showTable" v-model="selected_runs" show-expand :headers="table_headers"
                    :items="computedRuns" item-value="Run" v-model:sort-by="table_sort_by" density="compact"
                    show-select class="elevation-1 d-none d-md-block" hover>
        <template v-slot:item.actions="{item}">
          <run-actions :run="item.value" @reviewRun="(i: any) => reviewChanged(i)"/>
        </template>
        <template #item.vm_id="{ item }">
          <submission-icon :submission="item.value" />
          <a v-if="role != 'admin'" target="_blank" :href="item.value.link_to_team">{{ item.value.vm_id }}</a>

          <v-menu v-if="role == 'admin'" transition="slide-y-transition">
            <template v-slot:activator="{ props }">
              <a href="javascript:void(0)" v-bind="props">{{ item.value.vm_id }}</a>
            </template>
            <v-list>
              <v-list-item key="team-page"><a target="_blank" :href="item.value.link_to_team">Team Page of {{ item.value.vm_id }}</a></v-list-item>
              <v-list-item key="submission-page"><a target="_blank" :href="'/submit/' + task_id + '/user/' + item.value.vm_id">Submission Page of {{ item.value.vm_id }}</a></v-list-item>
            </v-list>
          </v-menu>
        </template>

        <template #item.dataset_id="{ item }">
          <submission-icon :submission="item.value" /> {{ item.value.dataset_id }}
        </template>

        <template v-slot:expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length" style="background-color: white;" class="px-0 mx-0">
              <software-details :run="item.value" :columns_to_skip="table_headers" :organizer="organizer" :organizer_id="organizer_id"/>
            </td>
          </tr>
        </template>
      </v-data-table>

      <v-data-table v-if="showTable" show-expand :headers="table_headers_small_layout"
                    :items="computedRuns" item-value="Run" v-model:sort-by="table_sort_by" expand-on-click density="compact"
                    class="elevation-1 d-md-none" hover>
                    <template #item.vm_id="{ item }">
          <a target="_blank" :href="item.value.link_to_team">{{ item.value.vm_id }}</a>
        </template>
        <template v-slot:expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length" style="background-color: white;"  class="px-0 mx-0">
              <software-details :run="item.value" :columns_to_skip="table_headers_small_layout" :organizer="organizer" :organizer_id="organizer_id" @reviewRun="(i: any) => reviewChanged(i)"/>
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
  </div>
</template>

<script lang="ts">
import RunActions from './RunActions.vue'
import SoftwareDetails from './SoftwareDetails.vue'
import Loading from "./Loading.vue"
import SubmissionIcon from "./SubmissionIcon.vue"
import SubmissionFilter from "./SubmissionFilter.vue"
import {get, reportError, inject_response, extractRole, extractDatasetFromCurrentUrl} from '../utils'

type run = { run_id: string; review_state: string; dataset_id: string; input_software_name: string; }

export default {
  name: "run-list",
  components: {RunActions, SoftwareDetails, Loading, SubmissionIcon, SubmissionFilter},
  props: ['task_id', 'organizer', 'organizer_id', 'vm_id', 'docker_software_id', 'upload_id', 'show_only_unreviewed', 'datasets', 'component_type'],
  data() { return {
      selected_runs: [],
      loading: true,
      runs: [{'run_id': 'loading...', 'review_state': 'no-review', 'dataset_id': 'loading...', 'input_software_name': 'loading...'}] as run[],
      table_headers: [],
      table_headers_small_layout: [],
      table_sort_by: [],
      ev_keys: [],
      filtered_runs: [] as run[],
      filtered_datasets: [],
      dataset_ids: '',
      role: extractRole(), // Values: guest, user, participant, admin
    }
  },
  computed: {
    downloadLink() {return '';},
    compareLink() {return this.createCompareLink(this.selected_runs);},
    showTable() {return this.dataset_ids || this.vm_id},
    computedRuns() {
      if (this.component_type === 'Overview') {return this.filtered_runs.length != 0 ? this.filtered_runs : this.runs}
      else if (this.component_type === 'Submission'){return this.filtered_datasets.length > 0 ? this.filtered_runs : this.runs}
    }
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
    receiveFilteredDataset(received_datasets: any) {
      if (this.component_type === 'Overview') {

        if (received_datasets.length === 0) {
          this.filtered_datasets = this.datasets.map((dataset: { [x: string]: any }) => dataset['dataset_id'])
          this.dataset_ids = this.datasets.map((dataset: { [x: string]: any }) => dataset['dataset_id']).join(',')
        }
        else {
          this.filtered_datasets = received_datasets
          this.dataset_ids = received_datasets.join(',')
        }

      }
      else {
        this.filtered_datasets = received_datasets.filter((x: string | any[]) => x.length > 0)
        this.filtered_runs = this.runs.filter(run => received_datasets.includes(run['dataset_id'])) as never
      }
    },
    receiveFilteredKeys(filtered_ev_keys: never[]) {
      let header_keys = this.table_headers
          .filter(header => header['title'] === header['key'])
          .map(measurement => measurement['title'])

      if (filtered_ev_keys.length < header_keys.length){
        let remove_keys = header_keys.filter((x) => !filtered_ev_keys.includes(x))
        this.table_headers = this.table_headers.filter(header => header['title'] !== remove_keys[0])
      }
      else if (filtered_ev_keys.length > header_keys.length){
        let add_keys = filtered_ev_keys.filter((x) => !header_keys.includes(x))
        let dict = {'title': add_keys[0], 'key': add_keys[0]}
        this.table_headers.splice(this.table_headers.length -1, 0, dict as never)
      }
    },
    receiveFilteredRuns(receivedRuns: any[]){
      let approaches = receivedRuns.map(run => run['input_software_name'])
      let runs_by_dataset: run[] = this.runs.filter(run => this.filtered_datasets.includes(run['dataset_id'] as never))
      this.filtered_runs = (runs_by_dataset.filter(run => approaches.includes(run['input_software_name'])))
    },
    fetchData() {
      if (this.dataset_ids === '' && this.component_type === 'Overview'){return /* dont fetch */}
      else {
      this.loading = true
      var rest_endpoint = ''
      if (this.task_id && this.dataset_ids) {
        rest_endpoint = '/api/evaluations/' + this.task_id + '/' + this.dataset_ids

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
    }
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
  beforeMount() {
    this.fetchData()
  },
  mounted(){
    if (this.component_type === 'Overview'){
      this.filtered_datasets = extractDatasetFromCurrentUrl() ? extractDatasetFromCurrentUrl() : this.datasets[0]['dataset_id']
      this.dataset_ids = extractDatasetFromCurrentUrl() ? extractDatasetFromCurrentUrl() : this.datasets[0]['dataset_id']
    } else {
      this.filtered_datasets = []
    }
  },
  watch: {
    task_id(old_id, new_id) {this.fetchData()},
    dataset_ids(old_value, new_value) {this.fetchData()},
  }
}
</script>