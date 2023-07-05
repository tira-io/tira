<template class="mx-5">
  <v-card class="mx-auto my-7">
    <v-card-title>
      <v-icon class="mx-2">mdi-transit-connection</v-icon>
      Running Processes
    </v-card-title>
    <v-card-text>
      Inspect your current runs
    </v-card-text>
    <v-card-actions>
      <v-row>
      <v-expansion-panels variant="inset">
        <v-expansion-panel
            v-for="i in 3"
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
                <v-col cols="8" >
                  <v-row class="mr-2 pa-md-3 overflow-x-auto">
                    <v-text-field
                        model-value="registry.webis.de/code-research/tira/tira-user-ir-lab-sose-2023-dogument-retriever/milestone-02:0.0.1"
                        label="Image"
                        variant="outlined"
                        readonly
                    ></v-text-field>
                  </v-row>
                  <v-row class="mr-2 pa-md-3 overflow-x-auto">
                    <v-text-field
                        model-value="/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/üyterrier-bm25.ipynb"
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
                    <v-icon class="mr-2">mdi-cancel</v-icon>Cancel Run
                  </v-btn>
                </v-col>
              </v-layout>
            </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      </v-row>

    </v-card-actions>
  </v-card>
</template>

<script>
import { VAutocomplete } from 'vuetify/components'

export default {
  name: "RunningProcesses",
  components: {VAutocomplete},
    props: {
    step_prop: {
      type: String,
    }
  },
  data() {
    return {
      example_output: "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
          "INFO 2023-06-29 15:55:21,871 basehttp: \"GET /public/tira/frontend-vuetify/chunks/webfontloader.js HTTP/1.1\" 200 12768\n" +
          "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n" +
          "INFO 2023-06-29 15:55:22,172 basehttp: \"GET /api/task/author-profiling HTTP/1.1\" 200 9031\n",
      run_items: [
        {key: "Start", value: "2023-06-29 17:29:50", icon: "mdi-timer-play-outline"},
        {key: "dataset", value: "task-1-type-classification", icon: "mdi-table"},
        {key: "dateset type", value: "training", icon: "mdi-alpha-t-box-outline"},
        {key: "CPU", value: "1 CPU Cores", icon: "mdi-cpu-64-bit"},
        {key: "Memory", value: "10 GB of RAM", icon: "mdi-memory"},
        {key: "GPU", value: "0 GPU", icon: "mdi-expansion-card"}
        ],

      selectedRuns: null,
      docker: {
        "images": ["image1", "image2"],
        "docker_softwares": ["software1", "software2"],
        "docker_software_help": "This is the help text for the docker software",
      },
      selectedRessources: '',
      ressources: [
          "Small (1 CPU Core, 10GB of RAM)",
          "Small (1 CPU Core, 10GB of RAM, IRDS)",
          "Small w. GPU (1 CPU Core, 10GB of RAM, 1 NVIDIA GTX 1080 with 8GB)",
          "Medium (2 CPU Cores, 20GB of RAM)",
          "Large (4 CPU Cores, 40GB of RAM)",

      ],
      selectedDataset: '',
      datasets: [{
                "dataset_id": "1",
                "display_name": "task-1-type-classification",
                "is_confidential": true,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 10,
                "runs_count": 220,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }, {
                "dataset_id": "2",
                "display_name": "task-1-type-classification-validation",
                "is_confidential": false,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 20,
                "runs_count": 100,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }
        ],
    }
  },
  computed: {
  },
  methods: {
    updateUrlToCurrentStep() {
      this.$router.replace({name: 'submission', params: {submission_type: this.$route.params.submission_type, selected_step: this.step}})
    }
  },
    watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>