<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
  <v-row v-if="!loading && role !== 'guest'">
    <v-responsive class="mt-10" min-width="220px" id="task-search">
      <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
                    variant="underlined" v-model="software_filter"/>
    </v-responsive>
  </v-row>
  <v-row v-if="!loading && role !== 'guest'">
    <v-col cols="10">
      <v-tabs v-model="tab" fixed-tabs class="mb-10">
        <v-tab variant="outlined" v-for="ds in this.filteredSoftwares" :value="ds.docker_software_id">
          {{ ds.display_name }}
        </v-tab>
      </v-tabs>
    </v-col>
    <v-col cols="2">
      <v-tabs v-model="tab" fixed-tabs class="mb-10">
        <v-tab value="newDockerImage" color="primary" style="max-width: 100px;" variant="outlined">
          <v-icon>mdi-tab-plus</v-icon>
        </v-tab>
      </v-tabs>
    </v-col>
  </v-row>

  <v-window v-model="tab" v-if="!loading && role !== 'guest'">
    <v-window-item v-for="ds in this.docker.docker_softwares" :value="ds.docker_software_id">
      <existing-docker-submission @deleteDockerImage="handleDeleteDockerImage" :user_id="user_id_for_submission"
                                  :datasets="datasets"
                                  :resources="resources" :docker_software_id="ds.docker_software_id"
                                  :organizer="organizer" :organizer_id="organizer_id"/>
    </v-window-item>
    <v-window-item value="newDockerImage">
      <h2>Create New Docker Image</h2>
      <div class="d-flex justify-lg-space-between">
        <v-card class="mx-auto mt-12" style="height: 100%;">
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
            </div>
          </v-card-title>

          <v-window v-model="step" style="height: 560px; width: 100%;">
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
                  --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook
                  /workspace/full-rank-pipeline.ipynb'
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

                <h3 class="text-h6 font-weight-light my-6">
                  Please select previous stages and run command
                </h3>
                <v-autocomplete label="Previous Stages"
                                :items="docker.docker_softwares"
                                v-model="selectedDockerSoftware"
                                clearable
                                multiple
                                chips/>
                <v-text-field v-model="runCommand" clearable
                              label="Command: mySoftware -c $inputDataset -r $inputRun -o $outputDir"
                              hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
              </div>
            </v-window-item>
            <v-window-item :value="'step-4'">
              <div class="pa-4 text-center">
                <h3 class="text-h6 font-weight-light my-6">
                  Please select your docker image
                </h3>
                <v-autocomplete
                    label="Docker Image"
                    :items="docker.images"
                    v-model="selectedDockerImage"
                    clearable/>
              </div>
            </v-window-item>

            <v-window-item :value="'step-5'">
              <div class="pa-4 text-center">
                <h3 class="text-h6 font-weight-light my-6">
                  Double check your local run and submit
                </h3>
                <v-list lines="one" class="text-left mx-auto w-50">
                  <v-list-item class="my-4" title="Image:" :subtitle="selectedDockerImage" key="Image:"></v-list-item>
                  <v-list-item class="my-4" title="Previous stages:" :subtitle="selectedDockerSoftware"
                               key="Previous stages:"></v-list-item>
                  <v-list-item class="my-4" title="Run command:" :subtitle="runCommand"
                               key="Run command:"></v-list-item>
                  <v-list-item class="my-4" title="Resources:" :subtitle="selectedResources"
                               key="Resources: "></v-list-item>
                  <v-list-item class="my-4" title="Dataset:" :subtitle="selectedDataset" key="Dataset: "></v-list-item>
                </v-list>

              </div>
              <v-btn variant="outlined" @click="addImage()">Add New Image</v-btn>
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

      </div>
    </v-window-item>
  </v-window>

</template>

<script>

import {VAutocomplete} from 'vuetify/components'
import {
  get,
  reportError,
  extractRole,
  extractTaskFromCurrentUrl,
  extractUserFromCurrentUrl,
  inject_response,
  filterByDisplayName
} from "@/utils";
import {Loading, LoginToSubmit, ExistingDockerSubmission} from "@/components";

export default {
  name: "docker-submission",
  components: {Loading, LoginToSubmit, VAutocomplete, ExistingDockerSubmission},
  props: ['step_prop', 'organizer', 'organizer_id'],
  data() {
    return {
      tab: null,
      software_filter: null,
      role: extractRole(),
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_submission: extractUserFromCurrentUrl(),
      selectedDockerSoftware: null,
      selectedContainer: null,
      selectedDockerImage: null,
      runCommand: null,
      step: this.step_prop,
      loading: true,
      docker: {
        "images": [{"id": null, "display_name": 'loading...'}],
        "docker_softwares": ["loading..."],
        "docker_software_help": "loading...",
      },
      selectedResources: '',
      resources: [
        "loading..."
      ],
      selectedDataset: '',
      datasets: [{
        "dataset_id": null,
        "display_name": "loading...",
      }
      ],
    }
  },
  computed: {
    filteredSoftwares() {
      return filterByDisplayName(this.docker.docker_softwares, this.software_filter)
    },
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
          return 'Double Check and Add Software'
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
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    addImage() {
      get(`/task/${this.task_id}/vm/${this.user_id_for_submission}/add_software/docker`).then(message => {
        this.docker.push(message.context.docker)
        this.tab = message.context.docker.images[0].display_name
      })
          .catch(reportError("Problem While Adding New Docker Image.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    handleDeleteDockerImage() {
      get(`/task/${this.task_id}/vm/${this.user_id_for_submission}/delete_software/docker/${this.tab}`)
          .then(message => {
            this.docker.images = this.docker.images.filter(i => i.id != this.docker.images.find(i => i.display_name === this.tab).id)
            this.tab = this.docker.images.length > 0 ? this.docker.images[0].display_name : null
            this.showUploadForm = false
          })
          .catch(reportError("Problem While Deleting Docker Image.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
  },
  beforeMount() {
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_submission + '/docker')
        .then(inject_response(this, {'loading': false}, true))
        .catch(reportError("Problem While Loading the Docker Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.tab = this.docker.images[0].display_name
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>