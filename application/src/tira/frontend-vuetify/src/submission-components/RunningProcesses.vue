<template class="mx-5" v-if="running_processes.length > 0">
  <v-expansion-panels>
    <v-expansion-panel>
      <v-expansion-panel-title>
        <template v-slot:default="{ expanded }">
          <div v-if="!expanded">
            <b>{{ running_processes.length }} running processes</b>
          </div>
          <div v-if="expanded" class="w-100">
            <v-row class="mt-3">
              <v-icon class="mx-2">mdi-transit-connection</v-icon>
              <b>Running Processes</b>
            </v-row>
            <p class="mt-5">
              Inspect your current runs
            </p>
          </div>
        </template>
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-btn variant="outlined" color="blue" class="my-2">
          <v-tooltip activator="parent" location="bottom">
            Check if some new runs have started
          </v-tooltip>
          <v-icon class="mr-2">mdi-refresh</v-icon>
          Refresh
        </v-btn>
        <v-card>
          <v-card-actions>
            <v-row>
              <v-expansion-panels>
                <v-expansion-panel
                    v-for="i in running_processes.length"
                    :key="i">
                  <v-expansion-panel-title>
                    <v-row>
                      <v-col cols="3" class="d-flex justify-start align-center">
                        TF_IDF + DPH
                      </v-col>
                      <v-col cols="3" class="d-flex justify-start align-center">
                        07-06-2023
                      </v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">scheduling</div>
                        <v-progress-circular
                            :size="20"
                            color="primary"
                            indeterminate
                        ></v-progress-circular>
                      </v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">execution</div>
                        <v-progress-circular
                            :size="20"
                            color="primary"
                            indeterminate
                        ></v-progress-circular>
                      </v-col>
                      <v-col cols="2" class="d-flex justify-start align-center">
                        <div class="mr-3">evaluation</div>
                        <v-progress-circular
                            :size="20"
                            color="primary"
                            indeterminate
                        ></v-progress-circular>
                      </v-col>
                    </v-row>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-layout row wrap class="pa-0">
                      <v-col cols="8">
                        <v-row class="mr-2 pa-md-3 overflow-x-auto">
                          <v-text-field
                              :model-value=docker.image
                              label="Image"
                              variant="outlined"
                              readonly
                          ></v-text-field>
                        </v-row>
                        <v-row class="mr-2 pa-md-3 overflow-x-auto">
                          <v-text-field
                              :model-value=docker.command
                              label="Command"
                              variant="outlined"
                              readonly
                          ></v-text-field>
                        </v-row>
                        <v-row class="mr-2 pa-md-3 overflow-y-auto">
                          <v-textarea
                              :model-value=example_output
                              label="Software Output"
                              variant="outlined"
                              rows="4"
                              readonly
                          ></v-textarea>
                        </v-row>
                      </v-col>

                      <v-divider :thickness="3" width="80" class="border-opacity-25" vertical></v-divider>

                      <v-col cols="4">
                        <v-list>
                          <v-list-item
                              v-for="(item, i) in run_items"
                              :key="i"
                          >
                            <template v-slot:prepend>
                              <v-icon :icon="item.icon"></v-icon>
                            </template>

                            <v-list-item-title>{{ item.key }}: {{ item.value }}</v-list-item-title>
                          </v-list-item>
                        </v-list>
                        <v-btn variant="outlined" color="red" class="w-100">
                          <v-tooltip
                              activator="parent"
                              location="bottom"
                          >
                            Attention! This canccels the current run
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
import {VAutocomplete} from 'vuetify/components'

export default {
  name: "RunningProcesses",
  components: {VAutocomplete},
  props: ["running_evaluations", "running_software", "last_software_refresh", "next_software_refresh"],
  emits: ['stopRun', 'addNotification', 'pollRunningContainer'],
  data() {
    return {
      running_processes: [1, 2, 3],
      /**
       * this is just mock_data for visual feedback
       * mock_data: example_output, values in run_items, docker
       */
      example_output: "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
          "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
          "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n" +
          "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n",
      run_items: [
        {key: "Start", icon: "mdi-timer-play-outline", value: "2023-06-29 17:29:50"},
        {key: "dataset", icon: "mdi-table", value: "task-1-type-classification"},
        {key: "dateset type", icon: "mdi-alpha-t-box-outline", value: "training"},
        {key: "CPU", icon: "mdi-cpu-64-bit", value: "1 CPU Cores"},
        {key: "Memory", icon: "mdi-memory", value: "10 GB of RAM"},
        {key: "GPU", icon: "mdi-expansion-card", value: "0 GPU"}
      ],
      docker: {
        image: "registry.webis.de/code-research/tira/tira-user-ir-lab-sose-2023-dogument-retriever/milestone-02:0.0.1",
        command: "/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/üyterrier-bm25.ipynb",
        software_output: "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
            "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
            "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n" +
            "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n",
      },
      selectedRuns: null,
    }
  },
  computed: {},
  methods: {
    updateUrlToCurrentStep() {
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    stopRun(run_id) {
      if (!(this.aborted_processes.includes(run_id))) {
        this.aborted_processes.push(run_id)
        this.$emit('stopRun', run_id)
      }
    },
    update_cache() {
      let force_cache_refresh = "True"
      this.$emit('pollRunningContainer', force_cache_refresh)
    },
    /**
     * Helper function, because the job config is sometimes not there
     */
    get_field(process, field) {
      if ("job_config" in process) {
        return process.job_config[field]
      }
      return ""
    },
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  },
  beforeMount() {
    console.log(this.running_software)
  }
}
</script>