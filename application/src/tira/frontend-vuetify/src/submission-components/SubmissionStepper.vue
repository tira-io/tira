<template>
<v-card
    class="mx-auto mt-12"
    max-width="500"
  >
    <v-card-title class="text-h6 font-weight-regular justify-space-between">
      <span class="mr-3">{{ currentTitle }}</span>
      <v-avatar
        color="primary"
        size="24"
        v-text="parseInt(this.step.split('-')[1])"
      ></v-avatar>
    </v-card-title>

    <v-window v-model="step" :key="rerenderKey">
      <v-window-item :value="'step-1'">
        <v-card-text>
          <h3>Create Run Upload Group</h3>
          <p>This is general information on how to submit your run ...</p>
          <p>Please click on "Next" below to start your submission upload.</p>
        </v-card-text>
      </v-window-item>

      <v-window-item :value="'step-2'">
        <v-card-text>
        <h3>Test baseline locally</h3>
        <p>Before you submit your run, you can test your baseline locally.</p>
        <p>For this, you need to download ...</p>
        <p>Then, you can run the baseline locally on the test dataset via following commands:</p>
          <code>1. this is example code to test locally <br> 2. Do this <br> 3. do that</code>
        </v-card-text>
      </v-window-item>

      <v-window-item :value="'step-3'">
        <div class="pa-4 text-center">
          <h3 class="text-h6 font-weight-light mb-2">
            Please select select your docker image
          </h3>
          <v-autocomplete label="Docker Image"
                  clearable/>
        </div>
      </v-window-item>
      <v-window-item :value="'step-4'">
        <div class="pa-4 text-center">

          <h3 class="text-h6 font-weight-light mb-2">
            Please select previous stages and run command
          </h3>
          <v-autocomplete label="Previous Stages"
                  clearable
                  multiple
                  chips/>
          <v-text-field clearable label="Command" hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."/>
        </div>
      </v-window-item>
      <v-window-item :value="'step-5'">
        <div class="pa-4 text-center">
          <h3 class="text-h6 font-weight-light mb-2">
            Double check your local run and submit
          </h3>
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
    </v-card-actions>
  </v-card>
</template>

<script>

import {ref} from "vue";

export default {
  name: "SubmissionStepper",
  props: {
    step_prop: {
      type: String,
      default: 'step-1'
    }
  },
  data() {
    return {
      step: this.step_prop,
      rerenderKey: 0
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
          return 'Double Check and Submit'
      }
    },
  },
  methods: {
    nextStep() {
      this.step = `step-${parseInt(this.step.split('-')[1]) - 1}`
      this.rerenderKey += 1
    },
    previousStep() {
      this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
      this.rerenderKey += 1
    },
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