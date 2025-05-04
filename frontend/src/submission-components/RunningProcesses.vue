<template class="mx-5">
  <v-expansion-panels>
    <v-expansion-panel>
      <v-expansion-panel-title>
        <template v-slot:default="{ expanded }">
          <div v-if="!expanded">
            <b>{{ title_of_component }}</b>
          </div>
          <div v-if="expanded" class="w-100">
            <v-row class="mt-3">
              <v-icon class="mx-2">mdi-transit-connection</v-icon>
              <b>{{ title_of_component }}</b>
            </v-row>
            <p class="mt-5">
              Inspect your current runs
            </p>
          </div>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-btn variant="outlined" color="blue" class="my-2" :disabled="poll_in_progress" :loading="poll_in_progress"
          @click="pollRunningSoftware('True')">
          <v-tooltip activator="parent" location="bottom">
            Check if some new runs have started
          </v-tooltip>
          <v-icon class="mr-2">mdi-refresh</v-icon>
          Refresh
        </v-btn>
        <v-card v-if="!loading && running_software.length > 0">
          <loading :loading="loading" />
          <v-card-actions v-if="!loading">
            <v-row>
              <v-expansion-panels>
                <v-expansion-panel v-for="software of running_software" :key="run_id">
                  <v-expansion-panel-title>
                    <v-row>
                      <v-col cols="3" class="d-flex justify-start align-center">{{ software.job_config.software_name
                        }}</v-col>
                      <v-col cols="3" class="d-flex justify-start align-center">{{ software.run_id }}</v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">scheduling</div>
                        <v-progress-circular v-if="software.execution.scheduling === 'pending'" :size="20"
                          color="primary" indeterminate />
                        <v-progress-circular v-if="software.execution.scheduling === 'running'" :size="20"
                          color="primary" indeterminate />
                        <v-icon v-if="software.execution.scheduling === 'done'">mdi-checkbox-marked-circle</v-icon>
                      </v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">execution</div>
                        <v-progress-circular v-if="software.execution.execution === 'pending'" :size="20"
                          color="primary" indeterminate />
                        <v-progress-circular v-if="software.execution.execution === 'running'" :size="20"
                          color="primary" indeterminate />
                        <v-icon v-if="software.execution.execution === 'done'">mdi-checkbox-marked-circle</v-icon>
                      </v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">evaluation</div>
                        <v-progress-circular v-if="software.execution.evaluation === 'pending'" :size="20"
                          color="primary" indeterminate />
                        <v-progress-circular v-if="software.execution.evaluation === 'running'" :size="20"
                          color="primary" indeterminate />
                        <v-icon v-if="software.execution.evaluation === 'done'">mdi-checkbox-marked-circle</v-icon>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-layout row wrap class="pa-0">
                      <v-col cols="8">
                        <v-row class="mr-2 pa-md-3 overflow-x-auto">
                          <v-text-field :model-value=software.job_config.image label="Image" variant="outlined"
                            readonly></v-text-field>
                        </v-row>
                        <v-row class="mr-2 pa-md-3 overflow-x-auto">
                          <v-text-field :model-value=software.job_config.command label="Command" variant="outlined"
                            readonly></v-text-field>
                        </v-row>
                        <v-row class="mr-2 pa-md-3 overflow-y-auto">
                          <v-textarea :model-value=software.stdOutput label="Software Output" variant="outlined"
                            rows="4" readonly></v-textarea>
                        </v-row>
                      </v-col>

                      <v-divider :thickness="3" width="80" class="border-opacity-25" vertical></v-divider>

                      <v-col cols="4">
                        <v-list>
                          <v-list-item prepend-icon="mdi-timer-play-outline">
                            <v-list-item-title>Start: {{ software.started_at }}</v-list-item-title>
                          </v-list-item>

                          <v-list-item prepend-icon="mdi-table">
                            <v-list-item-title>Dataset: {{ software.job_config.dataset }}</v-list-item-title>
                          </v-list-item>

                          <v-list-item prepend-icon="mdi-alpha-t-box-outline">
                            <v-list-item-title>Dataset Type: {{ software.job_config.dataset_type }}</v-list-item-title>
                          </v-list-item>

                          <v-list-item prepend-icon="mdi-cpu-64-bit">
                            <v-list-item-title>CPU: {{ software.job_config.cores }}</v-list-item-title>
                          </v-list-item>

                          <v-list-item prepend-icon="mdi-memory">
                            <v-list-item-title>CPU: {{ software.job_config.ram }}</v-list-item-title>
                          </v-list-item>

                          <v-list-item prepend-icon="mdi-expansion-card">
                            <v-list-item-title>CPU: {{ software.job_config.gpu }}</v-list-item-title>
                          </v-list-item>
                        </v-list>
                        <v-btn variant="outlined" color="red" class="w-100" @click="stopRun(software.run_id)">
                          <v-tooltip activator="parent" location="bottom">
                            Attention! This cancels the current run
                          </v-tooltip>
                          <v-icon class="mr-2">mdi-cancel</v-icon>
                          Cancel Run
                        </v-btn>
                      </v-col>
                    </v-layout>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-row>

          </v-card-actions>
        </v-card>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>

</template>

<script>
import { inject } from 'vue'

import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, reportSuccess } from "@/utils";
import { VAutocomplete } from 'vuetify/components'
import { Loading } from "@/components";

export default {
  name: "running-processes",
  components: { VAutocomplete, Loading },
  data() {
    return {
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_task: extractUserFromCurrentUrl(),
      running_software_last_refresh: 'loading...',
      running_software_next_refresh: 'loading...',
      running_software: [{
        'run_id': 'loading...',
        'execution': { 'scheduling': 'done', 'execution': 'running', 'evaluation': 'pending' },
        'stdOutput': 'hello world ....\nhunu',
        'started_at': 'started at...',
        'job_config': {
          'software_name': 'software...', 'image': 'image...', 'command': 'command...',
          'cores': '? CPU Cores', 'ram': '? GB of RAM', 'gpu': '0 GPUs',
          'data': '?', 'dataset_type': '?', 'dataset': 'tbd dataset',
          'software_id': 'loading software id', 'task_id': 'loading task...',
        },
      }],
      loading: true,
      poll_in_progress: false,
      selectedRuns: null,
      pollSoftwareInterval: null,
      abortedProcesses: [],
      grpc_url: inject("gRPC base URL"),
      rest_url: inject("REST base URL")
    }
  },
  computed: {
    title_of_component() {
      return this.loading ? 'Fetch Running Processes from the Backend ...' : this.running_software.length + ' Running Processes. (Last Refresh: ' + this.running_software_last_refresh + '; Next Refresh: ' + this.running_software_next_refresh + ')'
    }
  },
  methods: {
    stopRun(run_id) {
      if (!(this.abortedProcesses.includes(run_id))) {
        this.abortedProcesses.push(run_id)
        get(this.grpc_url + `/grpc/${this.task_id}/${this.user_id_for_task}/stop_docker_software/${run_id}`)
          .then(reportSuccess('Run with the id ' + run_id + " was successfully aborted!"))
          .catch(reportError("Problem while trying to abort the process with id: " + run_id))
      }
    },
    pollRunningSoftware(force_cache_refresh = "False") {
      if (this.poll_in_progress) {
        return
      }
      if ('' + this.pollSoftwareInterval !== 'null') {
        clearTimeout(this.pollSoftwareInterval)
      }

      this.poll_in_progress = true
      get(this.rest_url + `/api/task/${this.task_id}/user/${this.user_id_for_task}/software/running/${force_cache_refresh}`)
        .then(inject_response(this, { 'loading': false }))
        .catch(reportError("Problem While polling running software."))
        .then(message => {
          this.poll_in_progress = false

          if (this.running_software.length > 0) {
            console.log("ToDo: Re-Enable automatic polling...")
            //this.pollSoftwareInterval = setTimeout(this.pollRunningSoftware, 10000)  // Note: https://stackoverflow.com/questions/61683534/continuous-polling-of-backend-in-vue-js
          } else if ('' + this.pollSoftwareInterval !== 'null') {
            clearTimeout(this.pollSoftwareInterval)
          }
        })
    },
  },
  beforeMount() {
    this.loading = true
    this.pollRunningSoftware()
  }
}
</script>
