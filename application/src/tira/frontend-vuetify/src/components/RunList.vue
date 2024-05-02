<template>
  <div>
    <loading :loading="loading"/>
    <div v-if="!loading">

      <v-text-field>HALLLOOOOO</v-text-field>

      <submission-filter :datasets="datasets" :selected_dataset="dataset_ids" :isMounted="isMounted"
                         :ev_keys="ev_keys" :runs="runs" :component_type="component_type" :empty="empty"
                         :runs_url="runs_url" :datasets_url="datasets_url" :ev_keys_url="ev_keys_url"
                         @pass_dataset="receiveFilteredDataset" @pass_keys="receiveFilteredKeys" @pass_runs="receiveFilteredRuns"/>

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
import {
  get,
  reportError,
  inject_response,
  extractRole,
  extractDatasetFromCurrentUrl,
  extractEvKeysFromCurrentUrl, extractApproachFromCurrentUrl
} from '../utils'

type run = { run_id: string; review_state: string; dataset_id: string; input_software_name: string; }

export default {
  name: "run-list",
  components: {RunActions, SoftwareDetails, Loading, SubmissionIcon, SubmissionFilter},
  props: ['task_id', 'organizer', 'organizer_id', 'vm_id', 'docker_software_id', 'upload_id', 'show_only_unreviewed', 'datasets', 'component_type'],
  data() { return {
      loading: true,
      runs: [{'run_id': 'loading...', 'review_state': 'no-review', 'vm_id': '1', 'link_to_team': 'link', 'dataset_id': 'loading...', 'input_software_name': 'loading...'}] as run[],
      // runs: [{'run_id': 'loading...', 'review_state': 'no-review', 'vm_id': '1', 'link_to_team': 'link', 'dataset_id': '1'}],
      table_headers: [],
      table_headers_small_layout: [],
      table_sort_by: [],
      ev_keys: [],
      selected_runs: [],

      dataset_ids: '',
      filtered_ev_keys: [] as string[],
      filtered_runs: [] as run[],
      filtered_datasets: [],
      isMounted: 'test_alt',

      runs_url: extractApproachFromCurrentUrl().split(','),
      datasets_url: extractDatasetFromCurrentUrl().split(','),
      ev_keys_url: extractEvKeysFromCurrentUrl() === "nk" ? [] : extractEvKeysFromCurrentUrl().split(','),

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
    },
    empty(){return this.checkEmptyApproaches(this.runs)}
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
    receiveFilteredKeys(received_ev_keys: never[]) {
      let header_keys = this.extractEvKeys()

      if (received_ev_keys.length < header_keys.length){
        let remove_keys = header_keys.filter((x) => !received_ev_keys.includes(x))
        this.table_headers = this.table_headers.filter(header => !remove_keys.includes(header['title']))
      }
      else if (received_ev_keys.length > header_keys.length){
        let add_keys = (received_ev_keys).filter((x) => !header_keys.includes(x as never))
        let dict = {'title': add_keys[0], 'key': add_keys[0]}
        this.table_headers.splice(this.table_headers.length -1, 0, dict as never)
      }

      this.filtered_ev_keys = this.extractEvKeys()
    },
    receiveFilteredKeys2() {
      let received_ev_keys = this.ev_keys_url
      let header_keys = this.extractEvKeys()

      if (received_ev_keys.length === 1){
        console.log('test: ' + received_ev_keys)
        // do nothing
      }
      else {

        if (received_ev_keys.length < header_keys.length) {
          let remove_keys = header_keys.filter((x) => !received_ev_keys.includes(x))
          this.table_headers = this.table_headers.filter(header => !remove_keys.includes(header['title']))
        } else if (received_ev_keys.length > header_keys.length) {
          let add_keys = (received_ev_keys).filter((x) => !header_keys.includes(x as never))
          let dict = {'title': add_keys[0], 'key': add_keys[0]}
          this.table_headers.splice(this.table_headers.length - 1, 0, dict as never)
        }
        //this.filtered_ev_keys = this.extractEvKeys()
      }
    },
    receiveFilteredRuns(receivedRuns: any[]){
      let approaches = receivedRuns.map(run => run['input_software_name'])
      let runs_by_dataset: run[] = this.runs.filter(run => this.filtered_datasets.includes(run['dataset_id'] as never))
      this.filtered_runs = (runs_by_dataset.filter(run => approaches.includes(run['input_software_name'])))
    },
    checkEmptyApproaches(runs: any[]){
      return !runs.map((run: { [x: string]: any }) => run['input_software_name']).every((approach: string) => approach === '')
    },
    extractEvKeys(){
      return this.table_headers.filter(header => header['title'] === header['key']).map(measurement => measurement['title'])
    },
    updateUrlToCurrentFilterCriteria() {
      if (this.component_type === 'Overview'){
        this.$router.replace({name: 'task-overview', params: {task_id: this.task_id, dataset_id: encodeURIComponent(this.dataset_ids), ev_keys: encodeURIComponent((this.filtered_ev_keys as string[]).join(',').length === 0 ? "nk" : (this.filtered_ev_keys as string[]).join(',')), approach: encodeURI(this.filtered_runs.map(x => x.input_software_name).join(','))}})
      }
      else if (this.component_type === 'Submission'){
        console.log("component_type: " + this.component_type)
        this.$router.replace({
          name: 'submission',
          params: {submission_type: this.$route.params.submission_type, dataset_id: encodeURIComponent(this.dataset_ids), ev_keys: encodeURIComponent((this.filtered_ev_keys as string[]).join(',').length === 0 ? "nk" : (this.filtered_ev_keys as string[]).join(','))}})
      }
    },
    matchRuns(){
      if (this.runs_url[0] === ''){
        return []
      }
      else {
        console.log("real runs: " + this.runs[0]['input_software_name'])
        console.log('runs_url in match_runs: ' + this.runs_url[0])
        console.log("else: " + this.runs.filter(run => this.runs_url.includes(run['input_software_name'])))
        return this.runs.filter(run => this.runs_url.includes(run['input_software_name']))
      }
    },
    setupComponent() {
    if (this.component_type === 'Overview') {
      this.filtered_datasets = this.datasets_url[0] === '' ? this.datasets[0]['dataset_id'] : this.datasets_url
      this.filtered_ev_keys = this.ev_keys_url[0] === '' ? this.ev_keys : this.ev_keys_url
      this.receiveFilteredKeys2()
      this.filtered_runs = this.matchRuns()
      this.isMounted = "test_neu"
    } else {
      this.filtered_datasets = []
      this.filtered_ev_keys = this.ev_keys
    }
  },
    fetchData() {
        //this.loading = true
        var rest_endpoint = ''
        if (this.task_id && this.dataset_ids && this.component_type === 'Overview') {
          rest_endpoint = '/api/evaluations/' + this.task_id + '/' + this.dataset_ids
          console.log("endpoint1: " + rest_endpoint)

          if (this.show_only_unreviewed) {
            rest_endpoint += '?show_only_unreviewed=true'
          }
        } else if (this.task_id && this.vm_id) {
          rest_endpoint = '/api/evaluations-of-vm/' + this.task_id + '/' + this.vm_id
          console.log("endpoint2: " + rest_endpoint)

          if (this.docker_software_id) {
            rest_endpoint += '?docker_software_id=' + this.docker_software_id
            console.log("endpoint3: " + rest_endpoint)
          } else if (this.upload_id) {
            rest_endpoint += '?upload_id=' + this.upload_id
            console.log("endpoint4: " + rest_endpoint)
          }
        }
      return new Promise<void>((resolve, reject) => {
        get(rest_endpoint)
            .then((response) => {
                inject_response(this, { 'loading': false })(response);
                resolve(); // Resolve the promise when the injection is complete
            })
            .catch((error) => {
                reportError("Problem While Loading the List of Runs", "This might be a short-term hiccup, please try again. We got the following error: ")(error);
                reject(error); // Reject the promise if there is an error
            });
    });
        //get(rest_endpoint)   //
        //    .then(inject_response(this, {'loading': false}))
        //    .catch(reportError("Problem While Loading the List of Runs", "This might be a short-term hiccup, please try again. We got the following error: "))
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
    //this.fetchData()
  },
  async mounted() {
    try {
        await this.fetchData();
        this.setupComponent();
    } catch (error) {
        console.error('Error fetching data:', error);
    }
},
  created(){
    this.dataset_ids = this.datasets_url[0] === '' ? this.datasets[0]['dataset_id'] : this.datasets_url.join(',')
  },
  watch: {
    task_id(old_id, new_id) {this.fetchData()},
    dataset_ids(old_value, new_value) {
      this.updateUrlToCurrentFilterCriteria()
      this.fetchData()
    },
    filtered_ev_keys(old_value, new_value) {
      this.updateUrlToCurrentFilterCriteria()
    },
    filtered_runs(old_value, new_value) {this.updateUrlToCurrentFilterCriteria()},
  }
}
</script>