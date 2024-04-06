<template>
  <import-submission submission_type="docker"/>
  <h2>Create New Docker Submission</h2>
  <v-stepper v-model="stepperModel" flat :border=false>
    <template v-slot:default="{ prev, next }">
    <v-stepper-header>
      <template v-for="n in stepperTitles.length" :key="`step-${n}`">
        <v-stepper-item
          :complete="stepperModel > n"
          :step="`Step {{ n }}`"
          :value="n"
          :editable="false"
        ></v-stepper-item>

        <v-divider
          v-if="n !== steps"
          :key="n"
        ></v-divider>
      </template>
        </v-stepper-header>
      <v-stepper-window>
          <v-stepper-window-item style="min-height: 100vh" :value="1">
            <v-card title="Local Tests of your Docker Submission" flat>
              <v-card-text>
                    <p>This form will guide you through the process of adding a new Docker submission. Please test that your Docker submission works as expected on your machine with the commands below and click on "Next" as soon as everything looks fine.</p>
                    <p>Please use the <a href="https://www.tira.io/c/support"> Forum</a> or contact the organizers if you face problems.</p>
                  </v-card-text>
                  <v-card-text>
                    <h3 class="text-h6 font-weight-light mb-6">Step-by-Step Guide to test your Docker Submission</h3>
                    <p>Before you submit your Docker submission, please test it on your machine using the following three steps:</p>
                    
                    <div class="my-3"/>

                    <code-snippet title="(1) Make sure that your TIRA client is up to date and authenticated" :code="tira_setup_code" expand_message="(1) Make sure that your TIRA client is up to date and authenticated"/>

                    <div class="my-3"/>

                    <code-snippet title="(2) Execute your Docker Submission on a Small Example Dataset" :code="tira_initial_run_example" expand_message="(2)  Execute your submission on a small example dataset"/>

                      <div class="my-3"/>

                    <code-snippet title="Verify the Evaluator outputs to to ensure your Docker submission produces valid outputs" code="# The command above evaluated the outputs of your software 
        # Please verify that the evaluation in the directory tira-evaluation indicates that the outputs of your software are valid.
        cat tira-evaluation/evaluation.prototext" expand_message="(3) Verify the evaluator outputs to ensure all outputs are valid"/>
                  </v-card-text>
            </v-card>
          </v-stepper-window-item>

          <v-stepper-window-item style="min-height: 100vh" :value="2">
            <v-card title="Add the Docker Submission" flat>
              <div class="pa-4 text-center">

        <h3 class="text-h6 font-weight-light my-6" v-if="is_ir_task">
          Please select previous stages
        </h3>
        <p v-if="is_ir_task" class="mb-4">You can select multiple previous stages. The outputs of the previous stages are mounted into the container that executes the software.</p>
        <v-form ref="form" v-model="valid">
        <v-autocomplete v-if="is_ir_task" label="Previous Stages"
                        :items="all_previous_stages"
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
          <p>A software submission consists of a docker image and the command that is executed in the docker image. Please specify both below.</p>

          <p class="my-4 d-flex align-start"> Choose either an existing docker image... </p>
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
          <v-btn
                  class="mr-4"
                  color="primary"
                  :loading="refreshingInProgress"
                  @click="refreshImages()"
                >
                  refresh images
          </v-btn>
          <span><br v-if="$vuetify.display.mdAndDown">last refreshed: {{docker_images_last_refresh}}</span>
        </div>
          <div class="text-center mb-4">
            <v-dialog
              v-model="dialog"
              width="auto"
            >
              <template v-slot:activator="{ props }" class="d-flex flex-column align-center" >
                <div>
                <v-btn
                  class="d-flex mr-2 mb-4 mt-6 align-start"
                  color="primary"
                  variant="plain"
                  v-bind="props"
                >
                  <span v-if="!$vuetify.display.mdAndDown">...or see instructions on how to add a new docker image to tira</span>
                  <span v-if="$vuetify.display.mdAndDown">...or add new image</span>
                </v-btn>
              </div>
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
            </v-card>
          </v-stepper-window-item>

          <v-stepper-window-item style="min-height: 100vh" :value="3">
            <v-card title="Final Checks" flat>
              <div class="text-center">
                  <h3 class="text-h6 font-weight-light my-6">
                    Double check your local run and submit
                  </h3>
              </div>
              <code-snippet title="Check the Software Submission on a Small Example Dataset" :code="double_check_tira_run_command" expand_message="Please test the configuration of your your submission on a small example dataset"/>
              <div class="w-100 d-flex justify-end">
                <v-btn
                    :loading="addSoftwareInProgress"
                    v-if="step === 'step-3'"
                    color="primary"
                    variant="flat"
                    @click="addImage()"
                    >
                      Submit
                  </v-btn>  
                </div>      
            </v-card>
          </v-stepper-window-item>
          </v-stepper-window>
     <v-stepper-actions
          @click:prev="previousStep"
          @click:next="nextStep"
        >
      </v-stepper-actions>
    </template>
</v-stepper>
</template>

<script lang="ts">
import {VAutocomplete} from "vuetify/components";
import {extractTaskFromCurrentUrl, get, post, inject_response, reportError, extractUserFromCurrentUrl} from "@/utils";
import CodeSnippet from "../components/CodeSnippet.vue"
import Loading from "../components/Loading.vue"
import ImportSubmission from "./ImportSubmission.vue"

export default {
  name: "new-docker-submission",
  components: { CodeSnippet, VAutocomplete, Loading, ImportSubmission },
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
      tira_initial_run_example: 'loading...',
      tira_final_run_example: 'loading...',
      valid: false,
      dialog: false,
      addSoftwareInProgress: false,
      loading: true,
      step: this.step_prop === '' ? "step-1" : this.step_prop,
      all_uploadgroups: [{"id": null, "display_name": 'loading...'}],
      docker_images: [{ "image": "loading...", "architecture": "loading...", "created": "loading...", "size": "loading...", "digest": "loading...", 'title': 'loading...'}],
      public_docker_softwares: [{"docker_software_id": 'loading...', "display_name": 'loading...', 'vm_id': 'loading...'}],
      user_id_for_task: extractUserFromCurrentUrl(),
      stepperTitles: ['Local Tests of your Docker Submission', 'Add the Docker Submission', 'Final Checks'],
      stepperModel: 1,
      token: 'YOUR-TOKEN-HERE',
      steps: 3
    }
  },
  computed: {
    all_previous_stages() {
      return this.docker_softwares
        .concat(this.all_uploadgroups.map((i) => ({"display_name": i.display_name, "docker_software_id": ('upload-' + i.id)})))
        .concat(this.public_docker_softwares.filter((i) => i.vm_id !== this.user_id_for_task).map((i) => ({"display_name": i.vm_id + '/' + i.display_name, "docker_software_id": i.docker_software_id})))
    },
    tira_setup_code() {
      return 'pip3 uninstall -y tira\npip3 install tira\ntira-cli login --token ' + this.token
    },
    double_check_tira_run_command() {
      return this.tira_final_run_example.replace('YOUR-IMAGE', this.selectedDockerImage).replace('YOUR-COMMAND', this.runCommand)
    },
  },
  methods: {
    async nextStepWithValidate() {
      console.log("validating")
      const { valid } = await (this.$refs.form as any).validate()

      if (this.stepperModel === 2 && valid) {
        this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
        this.stepperModel += 1
      } else {
        window.alert('please fill out the form correctly')
      }
    },
    nextStep() {
      if(this.stepperModel === 1){
        this.stepperModel += 1
        this.step = `step-${parseInt(this.step.split('-')[1]) + 1}`
      }
      else if(this.stepperModel === 2){
        this.nextStepWithValidate()
      }
    },
    previousStep() {
      if(this.stepperModel > 0){
        this.stepperModel -= 1
        this.step = `step-${parseInt(this.step.split('-')[1]) - 1}`
      }
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

    get('/api/token/' + this.user_id_for_task)
      .then(inject_response(this))
      .catch(reportError("Problem While Loading The Metadata for the team of the Task " + this.user_id_for_task, "This might be a short-term hiccup, please try again. We got the following error: "))

    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_task + '/upload')
      .then(inject_response(this))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
      .then(() => {
        get('/api/task/' + this.task_id + '/user/' + this.user_id_for_task)
          .then(inject_response(this, {'loading': false}, false, 'docker'))
          .then(this.refreshTitles)
          .catch(reportError("Problem While Loading the Docker Images.", "This might be a short-term hiccup, please try again. We got the following error: "))
      })
  },
  watch: {
    step(old_value, new_value) {
      this.updateUrlToCurrentStep()
    }
  }
}
</script>
