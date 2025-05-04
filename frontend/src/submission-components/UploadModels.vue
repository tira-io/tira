<template>
    <login-to-submit v-if="userinfo.role === 'guest'" />
    <v-window v-model="tab" v-if="userinfo.role !== 'guest'" :touch="{ left: null, right: null }">
      <v-window-item value="newUploadGroup">
        <v-stepper :items="['About', 'Specify Metadata', 'Upload']" v-model="stepperModel" hide-actions="true" flat
          :border=false>
          <template v-slot:item.1>
            <v-card title="Please specify how you want to upload the model" flat>
              <v-radio-group v-model="upload_configuration">
                <v-radio label="I want to upload a model from Hugging Face" value="upload-config-2" />
                <v-radio label="Manually upload model" value="upload-config-1" />
              </v-radio-group>
            </v-card>
          </template>
  
          <template v-slot:item.2>
            <v-card flat>  
              <div v-if="upload_configuration === 'upload-config-1'">
                If your model is not on HuggingFace, please do not hesitate to <a :href="contact_organizer">contact</a> the organizer <a
                :href="link_organizer"> {{ organizer }}</a> to manually upload the model.
              </div>
              <div v-if="upload_configuration === 'upload-config-2'">
                Please specify the model that will be downloaded via huggingface-cli
                <v-text-field v-model="hugging_face_model" label="Hugging Face Model " />
                <div v-if="hugging_face_model">
                  The following command will be used to download your model:
  
                  <code-snippet title="TIRA will download and mount the model via"
                    :code="'huggingface-cli download ' + hugging_face_model" expand_message="" />
                  You can later mount the downloaded model into your software submission. Please click next to
                  upload/import this Hugging Face model to TIRA.
                </div>
              </div>
            </v-card>
          </template>
  
          <template v-slot:item.3>
            <v-card flat>
  
              <div v-if="hf_model_available === 'loading'">
                Download the model ...
              </div>
              <loading :loading="hf_model_available === 'loading'" />
  
              <span v-if="hf_model_available && hf_model_available !== 'loading'">
                The Huggingface model {{ hugging_face_model }} is already available in TIRA.
              </span>
              <span v-if="!hf_model_available">
                The Huggingface model {{ hugging_face_model }} is not yet available in TIRA and the automatic upload is
                disabled for this task. Please <a :href="contact_organizer">contact</a> the organizer <a
                  :href="link_organizer"> {{ organizer }}</a> to manually upload the model (this is usually finished
                within 24 hours).
              </span>
            </v-card>
          </template>

          <v-stepper-actions @click:prev="stepperModel = Math.max(1, stepperModel - 1)" @click:next="nextStep" :disabled='disableUploadStepper'></v-stepper-actions>
        </v-stepper>
        <br>

      </v-window-item>
    </v-window>
  </template>
  
  <script>
  import { inject } from 'vue'
  
  import { VAutocomplete } from 'vuetify/components'
  import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, get_link_to_organizer, get_contact_link_to_organizer } from "@/utils";
  import { Loading, LoginToSubmit, RunList } from "@/components";
  import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";
  import ImportSubmission from "./ImportSubmission.vue";
  import CodeSnippet from "../components/CodeSnippet.vue"
  
  export default {
    name: "upload-models",
    components: { EditSubmissionDetails, VAutocomplete, LoginToSubmit, RunList, ImportSubmission, CodeSnippet },
    props: ['organizer', 'organizer_id'],
    data() {
      return {
        userinfo: inject('userinfo'),
        task_id: extractTaskFromCurrentUrl(),
        user_id_for_task: extractUserFromCurrentUrl(),
        tab: null,
        upload_type: 'upload-1',
        hf_model_available: 'loading',
        hugging_face_model: '',
        upload_configuration: '',
        rest_url: inject("REST base URL"),
        stepperModel: 1,
      }
    },
    computed: {
      link_organizer() { return get_link_to_organizer(this.organizer_id); },
      contact_organizer() { return get_contact_link_to_organizer(this.organizer_id); },
      disableUploadStepper() {
        if (this.stepperModel == '1' && !this.upload_configuration) {
          return 'next';
        }
        if (this.stepperModel == '2' && (this.upload_configuration == 'upload-config-1' || !this.hugging_face_model)) {
          return 'next'
        }

        return false;
      }
    },
    methods: {
      nextStep() {
        if (this.stepperModel == 1) {
          this.stepperModel = 2;
        }
        else if (this.stepperModel == 2 && this.upload_configuration === 'upload-config-2') {
          this.hf_model_available = 'loading'
          get(this.rest_url + '/api/huggingface_model_mounts/vm/' + this.user_id_for_task + '/' + this.hugging_face_model.replace('/', '--'))
            .then(inject_response(this))
            .catch(reportError("Problem While importing the Hugging Face model " + this.hugging_face_model, "This might be a short-term hiccup, please try again. We got the following error: "))
          this.stepperModel = 3;
        }
      }
    }
  }
  </script>
  