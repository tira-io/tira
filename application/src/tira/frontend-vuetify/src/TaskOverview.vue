<template>
  <loading :loading="loading"/>

  <v-container v-if="!loading">
  <v-card class="px2" max-width="2560">
    <v-card-item :title="task.task_name">
      <template v-slot:subtitle>by <a :href="'https://www.tira.io/g/tira_org_' + task.organizer_id">{{ task.organizer }}</a> (<a :href="'https://www.tira.io/new-message?username=tira_org_' + task.organizer_id + '&title=Request%20&body=message%20body'">contact</a>)</template>
    </v-card-item>

    <v-card-text class="py-0">
      <v-row no-gutters>
        <v-col cols="10">{{task.task_description}}</v-col>
      </v-row>
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
  </v-card>
  </v-container>

  <v-container v-if="!loading">
    <h2>Submissions</h2>
    <v-autocomplete label="Dataset" :items="datasets" item-title="display_name" item-value="dataset_id"
                    v-model="selectedDataset" variant="underlined" clearable/>

    <run-list v-if="selectedDataset" :task_id="task_id" :dataset_id="selectedDataset"/>
  </v-container>
</template>

<script lang="ts">
  import RunList from './components/RunList.vue'
  import Loading from "./components/Loading.vue"
  import SubmitButton from './components/SubmitButton.vue'
  import { VAutocomplete } from 'vuetify/components'
  import { extractTaskFromCurrentUrl, extractDatasetFromCurrentUrl, chanceCurrentUrlToDataset, get, inject_response, reportError, extractRole } from './utils'

  export default {
    name: "task-list",
    components: {RunList, Loading, VAutocomplete, SubmitButton},
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
    }
  },
  methods: {
    updateDataset() {
      this.selectedDataset = extractDatasetFromCurrentUrl(this.datasets, this.selectedDataset)
      this.newDatasetSelected();
    },
    newDatasetSelected() {
      chanceCurrentUrlToDataset(this.selectedDataset)
    }
  },
  beforeMount() {
    get('/api/task/' + this.task_id)
      .then(inject_response(this, {'loading': false}, true))
      .then(this.updateDataset)
      .catch(reportError)
  },
  watch: {
    selectedDataset(old_value, new_value) { this.newDatasetSelected() },
  },
}
</script>
