<template>
  <v-card class="mx-auto mt-12" style="height: 100%;" >
    <v-card-title class="text-h6 font-weight-regular d-flex justify-space-between">
      <span class="mr-3">{{ currentTitle }}</span>
      <div>
        <v-avatar class="mx-1"
        :color="step === 'step-1' ? 'primary' : 'grey'"
        size="24"
        v-text="1"
        @click="() => step = 'step-1'"
      ></v-avatar>
      <v-avatar class="mx-1"
        :color="step === 'step-2' ? 'primary' : 'grey'"
        size="24"
        v-text="2"
        @click="() => step = 'step-2'"
      ></v-avatar>
      <v-avatar class="mx-1"
        :color="step === 'step-3' ? 'primary' : 'grey'"
        size="24"
        v-text="3"
        @click="() => step = 'step-3'"
      ></v-avatar>
      <v-avatar class="mx-1"
        :color="step === 'step-4' ? 'primary' : 'grey'"
        size="24"
        v-text="4"
        @click="() => step = 'step-4'"
      ></v-avatar>
      <v-avatar class="mx-1"
        :color="step === 'step-5' ? 'primary' : 'grey'"
        size="24"
        v-text="5"
        @click="() => step = 'step-5'"
      ></v-avatar>
        <v-avatar class="mx-1"
        :color="step === 'step-6' ? 'primary' : 'grey'"
        size="24"
        v-text="6"
        @click="() => step = 'step-6'"
      ></v-avatar>
      </div>
    </v-card-title>

    <v-window v-model="step">
      <v-window-item :value="'step-1'">
        <v-card-text>
          <h3 class="text-h6 font-weight-light mb-6">General information regarding submissions</h3>
          <p>This is general information about submitting to the TIRA platform ...</p>
          <p>Please click on "Next" below to start your submission process.</p>
        </v-card-text>
      </v-window-item>

      <v-window-item :value="'step-2'">
        <v-card-text>
        <h3 class="text-h6 font-weight-light mb-6">Test baseline locally</h3>
        <p>Before you submit your run, you need to test your baseline locally.</p>
        <p>You can do this in three steps:</p>
          <h4 class="my-5">(1) Data import</h4>
          <code class="bg-grey-lighten-1">tira-run \ <br>
            --output-directory ${PWD}/output-directory \ <br>
            --image $your-image-name \ <br>
            --allow-network true \ <br>
            --command '/irds_cli.sh --ir_datasets_id your-ir-dataset-name --output_dataset_path $outputDir'
          </code>
          <h4 class="my-5">(2) Retrieval</h4>
          <code class="bg-grey-lighten-1">
            tira-run \ <br>
            --input-directory ${PWD}/output-directory \ <br>
            --image webis/tira-ir-starter-pyterrier:0.0.2-base \ <br>
            --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook /workspace/full-rank-pipeline.ipynb'
          </code>
          <h4 class="my-5">(3) Retrieval Results</h4>
          <code class="bg-grey-lighten-1">
            tira-run \ <br>
            --input-directory ${PWD}/tira-output \ <br>
            --image your-image-name \ <br>
            --allow-network true \ <br>
            --command 'diffir --dataset your-ir-dataset-name --web $outputDir/run.txt > $outputDir/run.html'
          </code>
        </v-card-text>
      </v-window-item>

      <v-window-item :value="'step-3'">
        <div class="pa-4 text-center">
          <h3 class="text-h6 font-weight-light mb-6">
            Please select your docker image
          </h3>
          <v-autocomplete
              label="Docker Image"
              :items="docker.images"
              v-model="selectedDockerImage"
                  clearable/>
        </div>
      </v-window-item>
      <v-window-item :value="'step-4'">
        <div class="pa-4 text-center">

          <h3 class="text-h6 font-weight-light mb-6">
            Please select previous stages and run command
          </h3>
          <v-autocomplete label="Previous Stages"
              :items="docker.docker_softwares"
              v-model="selectedDockerSoftware"
              clearable
              multiple
              chips/>
          <v-text-field v-model="runCommand" clearable label="Command: mySoftware -c $inputDataset -r $inputRun -o $outputDir" hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
        </div>
      </v-window-item>
      <v-window-item :value="'step-5'">
        <div class="pa-4 text-center">
          <h3 class="text-h6 font-weight-light mb-6">
            Choose ressources and select a dataset
          </h3>
          <v-autocomplete
              label="Ressources"
              :items="ressources"
              v-model="selectedRessources"
                  clearable/>
          <v-autocomplete
              label="Dataset"
              :items="datasets['display_name']"
              v-model="selectedDataset"
                  clearable/>
        </div>
      </v-window-item>
      <v-window-item :value="'step-6'">
        <div class="pa-4 text-center">
          <h3 class="text-h6 font-weight-light mb-6">
            Double check your local run and submit
          </h3>
          <v-list lines="one" class="text-left mx-auto w-50">
            <v-list-item class="my-4" title="Image:" :subtitle="selectedDockerImage" key="Image:"></v-list-item>
            <v-list-item class="my-4" title="Previous stages:" :subtitle="selectedDockerSoftware" key="Previous stages:"></v-list-item>
            <v-list-item class="my-4" title="Run command:" :subtitle="runCommand" key="Run command:"></v-list-item>
            <v-list-item class="my-4" title="Ressources:" :subtitle="selectedRessources" key="Ressources: "></v-list-item>
            <v-list-item class="my-4" title="Dataset:" :subtitle="selectedDataset" key="Dataset: "></v-list-item>
          </v-list>

        </div>
      </v-window-item>
    </v-window>

    <v-divider></v-divider>

    <v-card-actions>
      <v-btn
        v-if="step !== 'step-1'"
        variant="text"
        @click="nextStep()"
      >
        Back
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        v-if="step !== 'step-6'"
        color="primary"
        variant="flat"
        @click="previousStep()"
      >
        Next
      </v-btn>
      <v-btn
        v-if="step === 'step-6'"
        color="primary"
        variant="flat"
        @click="submitRun()"
      >
        Submit
      </v-btn>
    </v-card-actions>
  </v-card>

</template>

<script>

import { VAutocomplete } from 'vuetify/components'
import {get, inject_response, reportError} from "@/utils";

export default {
  name: "DockerSubmission",
  components: {VAutocomplete},
    props: {
    step_prop: {
      type: String,
      default: 'step-1'
    }
  },
  data() {
    return {
      selectedDockerSoftware: null,
      selectedContainer: null,
      selectedDockerImage: null,
      runCommand: null,
      step: this.step_prop,
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
    currentTitle() {
      switch (this.step) {
        case 'step-1':
          return 'General Information'
        case 'step-2':
          return 'Local testing'
        case 'step-3':
          return 'Choose Docker image'
        case 'step-4':
          return 'Run Configuration'
        case 'step-5':
          return 'Ressources and Dataset'
        case 'step-6':
          return 'Double Check and Submit'
      }
    },
  },
  methods: {
    nextStep() {
      this.step = `step-${parseInt(this.step.split('-')[1]) - 1}`
    },
    previousStep() {
      this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
    },
    submitRun() {
      console.log('submit run')
    },
    updateUrlToCurrentStep() {
      this.$router.replace({name: 'submission', params: {submission_type: this.$route.params.submission_type, selected_step: this.step}})
    }
  },
  beforeMount() {
    get('/api/datasets_by_task/' + this.task_id)
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading the Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
      console.log(this)
  },
    watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>