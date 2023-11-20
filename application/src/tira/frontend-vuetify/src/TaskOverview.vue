<template>
  <tira-breadcrumb/>
  <loading :loading="loading"/>
  <div v-if="!loading" class="!$vuetify.display.mdAndUp ? 'my-0 px-3' : 'my-5 px-10'">
        <loading :loading="loading"/>
        <v-container v-if="!loading">
          <v-card class="px2" max-width="2560">
            <v-card-item :title="task.task_name">
              <template v-slot:subtitle>by <a :href="link_organizer">{{ task.organizer }}</a> (<a :href="contact_organizer">contact</a>)</template>
            </v-card-item>

             <v-card-text class="py-0">
               <v-row no-gutters><v-col cols="10">{{task.task_description}}</v-col></v-row>
             </v-card-text>

            <div class="d-flex py-3">
              <v-list-item density="compact" prepend-icon="mdi-calendar-blank-outline">
                <v-list-item-subtitle>{{task.year}}</v-list-item-subtitle>
                <v-tooltip activator="parent" location="bottom">Task year(s): {{task.year}}</v-tooltip>
              </v-list-item>

              <v-list-item density="compact" prepend-icon="mdi-account-group">
                <v-list-item-subtitle>{{task.teams}}</v-list-item-subtitle>
                <v-tooltip activator="parent" location="bottom">Teams: {{ task.teams }}</v-tooltip>
              </v-list-item>

              <v-list-item density="compact" prepend-icon="mdi-database-outline">
                <v-list-item-subtitle>{{task.dataset_count}}</v-list-item-subtitle>
                <v-tooltip activator="parent" location="bottom">Dataset count: {{task.dataset_count}}</v-tooltip>
              </v-list-item>

              <v-list-item density="compact" prepend-icon="mdi-briefcase-outline">
                <v-list-item-subtitle>{{task.software_count}}</v-list-item-subtitle>
                <v-tooltip activator="parent" location="bottom">Software count: {{task.software_count}}</v-tooltip>
              </v-list-item>
            </div>

          <v-divider></v-divider>

          <v-card-actions>
            <v-row>
              <v-col cols="6"><submit-button :task="task" :vm="vm" :user_id="user_id" :user_vms_for_task="user_vms_for_task"/></v-col>
              <v-col cols="6"><v-btn variant="outlined" :href="task.web" block>Task Website</v-btn></v-col>
            </v-row>
          </v-card-actions>
          <v-card-actions v-if="task_id === 'ir-benchmarks'">
            <v-row>
              <v-dialog transition="dialog-bottom-transition" width="auto">
                <template v-slot:activator="{ props }">
                  <v-col cols="12"><v-btn variant="outlined" v-bind="props" block>Documentation</v-btn></v-col>
                </template>
                <template v-slot:default="{ isActive }">
                  <task-documentation :task="task"/>
                </template>
              </v-dialog>
            </v-row>
          </v-card-actions>
          <v-card-actions v-if="vm_ids">
            <v-row>
              <v-menu transition="slide-y-transition">
                <template v-slot:activator="{ props }">
                  <v-col cols="12"><v-btn v-bind="props" variant="outlined" block>Manage your Teams</v-btn></v-col>
                </template>
                <v-list>
                  <v-list-item v-for="(item, i) in vm_ids" :key="i">
                    <v-btn :href="'https://www.tira.io/g/tira_vm_' + item" variant="outlined" target="_blank" block>Manage Team {{ item }}</v-btn>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-row>
          </v-card-actions>
        </v-card>
        </v-container>
        <tira-task-admin v-if="!loading" :datasets="datasets" :task="task" @addDataset="(x:any) => addDataset(x)" @deleteDataset="(dataset_id: string) => deleteDataset(dataset_id)"/>
          <v-container v-if="!loading" id="dataset-select">
            <h2>Submissions</h2>
            <run-list :task_id="task_id" :organizer="task.organizer"
                      :organizer_id="task.organizer_id"
                      :datasets="datasets" :component_type="component_type"/>
          </v-container>
  </div>
</template>

<script lang="ts">
  import { TiraBreadcrumb, TiraTaskAdmin, RunList, Loading, SubmitButton, TaskDocumentation } from './components'
  import RunUpload from "@/RunUpload.vue"
  import { VAutocomplete } from 'vuetify/components'
  import { extractTaskFromCurrentUrl, get_link_to_organizer, get_contact_link_to_organizer, extractDatasetFromCurrentUrl, changeCurrentUrlToDataset, get, inject_response, reportError, extractRole} from './utils'
  export default {
    name: "task-list",
    components: {TiraBreadcrumb, RunList, Loading, VAutocomplete, SubmitButton, TiraTaskAdmin, TaskDocumentation, RunUpload},
    data() {
      return {
        task_id: extractTaskFromCurrentUrl(),
        loading: true,
        role: extractRole(), // Values: guest, user, participant, admin
        selectedDataset: '',
        task: { "task_id": "", "task_name": "", "task_description": "",
                "organizer": "", "organizer_id": "", "web": "", "year": "",
                "dataset_count": 0, "software_count": 0, "teams": 0, "is_ir_task": false
        },
        vm: '',
        user_id: '',
        user_vms_for_task: [],
        datasets: [{'dataset_id': 'loading...', 'display_name': 'loading...'}],
        tab: "test",
        component_type: 'Overview',
    }
  },
  computed: {
    link_organizer() {return get_link_to_organizer(this.task.organizer_id);},
    contact_organizer() {return get_contact_link_to_organizer(this.task.organizer_id);},
    vm_ids() { return this.user_vms_for_task.length > 1 ? this.user_vms_for_task : null;},
  },
  methods: {
    updateDataset() {
      this.selectedDataset = extractDatasetFromCurrentUrl(this.datasets, this.selectedDataset)
      this.newDatasetSelected();
    },
    newDatasetSelected() {
      changeCurrentUrlToDataset(this.selectedDataset)
    },
    changeCurrentRouteToSubmission() {
      this.$router.push('/submit/' + this.task_id + '/user/' + this.user_id)
    },
    addDataset(dataset: any) {
      let found = false

      for (let d of this.datasets) {
        if (d['dataset_id'] === dataset['dataset_id']) {
          found = true
          d['display_name'] = dataset['display_name']
        }
      }

      if (!found) {
        this.datasets.push(dataset)
      }

      this.selectedDataset = dataset['dataset_id']
      this.newDatasetSelected()
    },
    deleteDataset(dataset_id: string) {
      // filter by dataset on datasets
      this.datasets = this.datasets.filter(d => d['dataset_id'] !== dataset_id)
      this.updateDataset()
    },
  },
  beforeMount() {
    get('/api/task/' + this.task_id)
      .then(inject_response(this, {'loading': false}, true))
      .then(this.updateDataset)
      .catch(reportError("Problem While Loading the Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  watch: {
    selectedDataset(old_value, new_value) { this.newDatasetSelected() },
  },
}
</script>
