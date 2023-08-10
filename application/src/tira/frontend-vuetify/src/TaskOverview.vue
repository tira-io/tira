<template>
  <v-container>
  <tira-breadcrumb/>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-card >
      <v-card-actions>
        <v-layout class="overflow-visible " style="height: 56px; ">
          <v-bottom-navigation v-model="tab" color="primary" :elevation="10" grow>

             <v-btn value="Overview">
              <v-icon>mdi-home-analytics</v-icon>
              Overview
            </v-btn>

            <v-btn value="Leaderboard">
              <v-icon>mdi-google-analytics</v-icon>
              Leaderboard
            </v-btn>

            <v-btn @click="changeCurrentRouteToSubmission()">
              <v-icon>mdi-new-box</v-icon>
              New Submission
            </v-btn>

          </v-bottom-navigation>
        </v-layout>
      </v-card-actions>
    </v-card>


    <v-window v-model="tab">

      <v-window-item value="Overview">
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
        </v-card>
        </v-container>
      </v-window-item>

      <v-window-item value="Leaderboard">

        <tira-task-admin v-if="!loading"/>
          <v-container v-if="!loading" id="dataset-select">
            <h2>Submissions</h2>
            <v-autocomplete label="Dataset" :items="datasets" item-title="display_name" item-value="dataset_id"
                            v-model="selectedDataset" variant="underlined" clearable/>

            <run-list v-if="selectedDataset" :task_id="task_id" :organizer="task.organizer" :organizer_id="task.organizer_id" :dataset_id="selectedDataset"/>
          </v-container>

      </v-window-item>
    </v-window>
  </v-container>
  </v-container>
</template>

<script lang="ts">
  import { TiraBreadcrumb, TiraTaskAdmin, RunList, Loading, SubmitButton, TaskDocumentation } from './components'
  import RunUpload from "@/RunUpload.vue";
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
                "dataset_count": 0, "software_count": 0, "teams": 0
        },
        vm: '',
        user_id: '',
        user_vms_for_task: [],
        datasets: [{'dataset_id': 'loading...', 'display_name': 'loading...'}],
        tab: "test",
    }
  },
  computed: {
    link_organizer() {return get_link_to_organizer(this.task.organizer_id);},
    contact_organizer() {return get_contact_link_to_organizer(this.task.organizer_id);}
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
    }
  },
  beforeMount() {
    get('/api/task/' + this.task_id)
      .then(inject_response(this, {'loading': false}, true))
      .then(this.updateDataset)
      .catch(reportError("Problem While Loading the Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    console.log(this.user_id)
  },
  watch: {
    selectedDataset(old_value, new_value) { this.newDatasetSelected() },
  },
}
</script>