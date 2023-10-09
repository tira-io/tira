<template>
  <div style="min-height: 120vh;">
  <h2>Create New Docker Software</h2>
  <div class="d-flex justify-lg-space-between">
    <v-card class="mx-auto mt-12" style="width: 100%;">
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
                    @click="() => nextStepWithValidate()"
          ></v-avatar>
        </div>
      </v-card-title>

      <v-window v-model="step">
        <v-window-item :value="'step-1'">
          <v-card-text>
            <p>This form will guide you through the process of adding a new Docker submission. Please test that your Docker submission works as expected on your machine with the commands below and click on "Next" as soon as everything looks fine.</p>
            <p>Please use the <a href="https://www.tira.io/c/support"> Forum</a> or contact the organizers if you face problems.</p>
          </v-card-text>
          <v-card-text>
            <h3 class="text-h6 font-weight-light mb-6">Step-by-Step Guide to test your Docker Submission</h3>
            <p>Before you submit your Docker submission, please test it on your machine using the following three steps:</p>
            
            <div class="my-3"/>

            <code-snippet title="Install the TIRA CLI on your machine" code="pip3 install tira" expand_message="(1) Install the TIRA CLI"/>

            <div class="my-3"/>

            <code-snippet title="Execute your Docker Submission on a Small Example Dataset" code="# This example shows how to execute the baseline on a small example dataset.
# Please adjust the --image and --command parameters accordingly.
tira-run \
  --input-directory ${PWD}/output-directory \
  --image webis/tira-ir-starter-pyterrier:0.0.2-base \
  --command '/workspace/run-pyterrier-notebook.py --input $inputDataset --output $outputDir --notebook
              /workspace/full-rank-pipeline.ipynb'" expand_message="(2)  Execute your submission on a small example dataset"/>

              <div class="my-3"/>

            <code-snippet title="Run the Evaluator to ensure your Docker submission produces valid outputs" code="tira-run \
  --output-directory ${PWD}/output-directory \
  --image $your-image-name \
  --allow-network true \
  --command '/irds_cli.sh --ir_datasets_id your-ir-dataset-name --output_dataset_path $outputDir'" expand_message="(3) Run the evaluator to ensure all outputs are valid"/>
          </v-card-text>
        </v-window-item>

        <v-window-item :value="'step-2'">
          <div class="pa-4 text-center">

            <h3 class="text-h6 font-weight-light my-6" v-if="is_ir_task">
              Please select previous stages
            </h3>
            <p v-if="is_ir_task" class="mb-4">You can select multiple previous stages. The outputs of the previous stages are mounted into the container that executes the software.</p>
            <v-form ref="form" v-model="valid">
            <v-autocomplete v-if="is_ir_task" label="Previous Stages"
                            :items="docker_softwares"
                            v-model="selectedDockerSoftware"
                            item-value="docker_software_id"
                            item-title="display_name"
                            clearable
                            multiple
                            chips/>

            <div class="text-center">
            <h3 class="text-h6 font-weight-light my-6">
              Please specify your docker software
            </h3>
              <p class="mb-4">A software submission consists of a docker image and the command that is executed in the docker image. Please specify both below.</p>

            <v-autocomplete
                label="Docker Image"
                :items="docker_images"
                v-model="selectedDockerImage"
                item-value="image"
                item-title="title"
                :loading="loading"
                :disabled="loading"
                clearable
                :rules="[v => !!(v && v.length) || 'Please select the docker image for the execution.']"/>
            </div>
               <div class="text-center mb-4">
                <v-dialog
                  v-model="dialog"
                  width="auto"
                >
                  <template v-slot:activator="{ props }" class="d-flex flex-column align-center" >
                    <div>
                    <v-btn
                      class="mr-2"
                      color="primary"
                      v-bind="props"
                    >
                      Push New Docker Image
                    </v-btn>
                     <v-btn
                      color="primary"
                      :loading="refreshingInProgress"
                      @click="refreshImages()"
                    >
                      refresh images
                    </v-btn>
                   </div>
                    <span>last refreshed: {{docker_images_last_refresh}}</span>
                  </template>

                  <v-card>
                    <v-card-text v-if="loading"><loading :loading="loading"/></v-card-text>
                    <v-card-text v-html="docker_software_help" v-if="!loading" />
                    <v-card-actions>
                      <v-btn color="primary" block @click="dialog = false">Close Information</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </div>
            <v-text-field v-model="runCommand" clearable
                          label="Command: mySoftware -c $inputDataset -r $inputRun -o $outputDir"
                          hint="Available variables: $inputDataset, $inputRun, $outputDir, $dataServer, and $token."
                          :rules="[v => !!(v && v.length) || 'Please select the run command for the execution.']"/>
          </v-form>

          </div>
        </v-window-item>

        <v-window-item :value="'step-3'">
          <div class="text-center">
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
                  item-value="image"
                  item-title="title"
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
            @click="previousStep()"
        >
          Back
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
            v-if="step !== 'step-3'"
            color="primary"
            variant="flat"
            @click="step === 'step-1' ? nextStep() : nextStepWithValidate()"
        >
          Next
        </v-btn>
        <v-btn
            :loading="addSoftwareInProgress"
            v-if="step === 'step-3'"
            color="primary"
            variant="flat"
            @click="addImage()"
        >
          Submit
        </v-btn>
      </v-card-actions>
    </v-card>

  </div>
</div>
</template>

<script lang="ts">
import {VAutocomplete} from "vuetify/components";
import {extractTaskFromCurrentUrl, get, post, inject_response, reportError, extractUserFromCurrentUrl} from "@/utils";
import CodeSnippet from "../components/CodeSnippet.vue"
import Loading from "../components/Loading.vue"

export default {
  name: "new-docker-submission",
  components: { CodeSnippet, VAutocomplete, Loading },
  props: ['user_id_for_submission', 'step_prop', 'organizer', 'organizer_id', 'docker_softwares', 'is_ir_task'],
  emits: ['addNewDockerImage'],
  data() {
    return {
      task_id: extractTaskFromCurrentUrl(),
      refreshingInProgress: false,
      selectedDockerSoftware: [],
      selectedDockerImage: '',
      runCommand: '',
      docker_images_last_refresh: 'loading...',
      docker_images_next_refresh: 'loading...',
      docker_software_help: 'loading...',
      valid: false,
      dialog: false,
      addSoftwareInProgress: false,
      loading: true,
      step: this.step_prop,
      docker_images: [{ "image": "loading...", "architecture": "loading...", "created": "loading...", "size": "loading...", "digest": "loading...", 'title': 'loading...'}],
      user_id_for_task: extractUserFromCurrentUrl(),
    }
  },
  computed: {
    currentTitle() {
      switch (this.step) {
        case 'step-1':
          return 'Local Tests of your Docker Submission'
        case 'step-2':
          return 'Add the Docker Submission'
        case 'step-3':
          return 'Final Checks'
      }
    },
  },
  methods: {
    async nextStepWithValidate() {
      const { valid } = await (this.$refs.form as any).validate()

      if (this.step === 'step-2' && valid) {
        this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
      } else {
        window.alert('please fill out the form correctly')
      }
    },
    nextStep() {
      this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
    },
    previousStep() {
        this.step = `step-${parseInt(this.step.split('-')[1]) - 1}`
    },
    updateUrlToCurrentStep() {
      this.$router.replace({
        name: 'submission',
        params: {submission_type: this.$route.params.submission_type, selected_step: this.step}
      })
    },
    addImage() {
      this.addSoftwareInProgress = true;
      post(`/task/${this.task_id}/vm/${this.user_id_for_submission}/add_software/docker`, {"command": this.runCommand, "image": this.selectedDockerImage, "inputJob": this.selectedDockerSoftware})
        .then(message => {
          this.$emit('addNewDockerImage', {'display_name': message.context.display_name, 'docker_software_id': message.context.docker_software_id});
        })
        .catch(reportError("Problem While Adding New Docker Software.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.addSoftwareInProgress = false})
    },
    refreshImages() {
      this.refreshingInProgress = true
      get(`/api/task/${this.task_id}/user/${this.user_id_for_task}/refresh-docker-images`)
        .then(inject_response(this, {"refreshingInProgress": false}, false, 'docker'))
        .then(this.refreshTitles)
    },
    refreshTitles() {
      for (const d of this.docker_images) {
        d['title'] = d.image + ' (' + d.architecture + ' ' + d.created + ' ' + d.size + ' ' + d.digest +')'
      }
    }
  },
  beforeMount() {
    this.loading = true
    get('/api/task/' + this.task_id + '/user/' + this.user_id_for_task)
      .then(inject_response(this, {'loading': false}, false, 'docker'))
      .then(this.refreshTitles)
      .catch(reportError("Problem While Loading the Docker Images.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>
