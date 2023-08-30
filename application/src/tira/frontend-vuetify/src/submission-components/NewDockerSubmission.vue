<template>
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
                            :items="docker_softwares"
                            v-model="selectedDockerSoftware"
                            item-value="docker_software_id"
                            item-title="display_name"
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
                :items="docker_images"
                v-model="selectedDockerImage"
                clearable/>
          </div>
        </v-window-item>

        <v-window-item :value="'step-5'">
          <div class="pa-4 text-center">
            <h3 class="text-h6 font-weight-light my-6">
              Double check your local run and submit
            </h3>
            <v-form>
               <v-autocomplete label="Previous Stages"
                            :items="docker_softwares"
                            v-model="selectedDockerSoftware"
                            item-value="docker_software_id"
                            item-title="display_name"
                            multiple
                            chips
                            disabled/>
               <v-text-field v-model="runCommand" disabled
                          label="Command: mySoftware -c $inputDataset -r $inputRun -o $outputDir"
                          hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
               <v-autocomplete
                  label="Docker Image"
                  :items="docker_images"
                  v-model="selectedDockerImage"
                  disabled/>
            </v-form>

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
            v-if="step !== 'step-5'"
            color="primary"
            variant="flat"
            @click="previousStep()"
        >
          Next
        </v-btn>
        <v-btn
            :loading="addSoftwareInProgress"
            v-if="step === 'step-5'"
            color="primary"
            variant="flat"
            @click="addImage()"
        >
          Submit
        </v-btn>
      </v-card-actions>
    </v-card>

  </div>

</template>

<script lang="ts">
import {VAutocomplete} from "vuetify/components";
import {extractTaskFromCurrentUrl, get, reportError} from "@/utils";

export default {
  name: "new-docker-submission",
  components: {VAutocomplete},
  props: ['user_id_for_submission', 'step_prop', 'organizer', 'organizer_id', 'docker_softwares'],
  emits: ['addNewDockerImage'],
  data() {
    return {
      task_id: extractTaskFromCurrentUrl(),
      selectedDockerSoftware: [],
      selectedDockerImage: '',
      runCommand: '',
      addSoftwareInProgress: false,
      step: this.step_prop,
      docker_images: ['image1', 'image2', 'image3'],
      docker_software_help: 'test docker software help',
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
    updateUrlToCurrentStep() {
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    addImage() {
      this.addSoftwareInProgress = true;
      /*get(`/task/${this.task_id}/vm/${this.user_id_for_submission}/add_software/docker`).then(message => {
        this.$emit('addNewDockerImage', message.context.docker);
      })
          .catch(reportError("Problem While Adding New Docker Image.", "This might be a short-term hiccup, please try again. We got the following error: "))*/
    setTimeout(() => {
          this.addSoftwareInProgress = false;
          let next_id = (this.docker_softwares.length + 1) + '';
          this.$emit('addNewDockerImage', {'display_name': 'meine_neue_software_' + next_id, 'docker_software_id': next_id});
        }, 2000)
    },
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>
