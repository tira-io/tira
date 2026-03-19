<template>
  <loading :loading="loading" />

  <login-to-submit v-if="!loading && userinfo.role === 'guest'" />

  <br>

  
  <v-btn color="primary" class="my-5" prepend-icon="mdi-plus" size="large" block @click="showUploadForm=true">Upload New Run</v-btn>
  
  <v-dialog v-model="showUploadForm" width="80%" height="80%" scrollable>
    <v-card>
      <v-toolbar color="primary"><v-card-title> Upload New Run </v-card-title></v-toolbar>
      <v-card-text>
    
    <v-stepper :items="['How to Submit', 'Specify Metadata', 'Upload']" v-model="stepperModel" hide-actions="true" flat :border=false>
      <template v-slot:item.1>
        <v-card title="Specify what you want to upload" flat>
          <v-radio-group v-model="upload_configuration">
            <v-radio label="I want to upload runs via the command line" value="upload-config-2" />
            <v-radio label="I want to upload runs via the UI" value="upload-config-1" />
          </v-radio-group>
        </v-card>
      </template>

      <template v-slot:item.2>
        <v-card flat>
          <div v-if="upload_configuration === 'upload-config-2'">
            <upload-submission-via-cli :token="token" :datasets="datasets"/>
          </div>
          <div v-if="upload_configuration === 'upload-config-1'">
            <v-form>
              Please select the dataset for which you want to upload your run<br>
              <v-autocomplete label="Dataset" :items="datasets" item-title="display_name" item-value="dataset_id"  prepend-icon="mdi-file-document-multiple-outline" v-model="selectedDataset" variant="underlined" clearable :rules="[v => !!(v) || 'Please select a dataset.']"/>

              Please describe your run<br>
              <v-text-field v-model="run_name" label="The ID/Name of your run" :rules="[v => !!(v && v.length >= 3 && v.length < 20) || 'Please use between 3 and 20 characters for your run id.']"/>
              <v-textarea v-model="description" label="Description" :rules="[v => !!(v && v.length >= 3) || 'Please add a non-empty description of your run.']"/>
            </v-form>
          </div>
        </v-card>
      </template>


      <template v-slot:item.3>
        <v-card flat>
          <v-form ref="form" v-model="upload_form_valid">
            <v-file-input v-model="fileHandle" :rules="[v => (Array.isArray(v) ? v.length > 0 : !!v) || 'File is required']" label="Click to add run file" />
            <v-row>
              <v-col cols="12"><v-alert v-if="error_message" title="Uploading the run failed. Maybe a short hiccup?" type="error" closable :text="error_message"/></v-col>
            </v-row>

            <v-btn color="primary" :loading="uploading" :disabled="uploading" class="my-5" prepend-icon="mdi-plus" size="large" block @click="fileUpload()">Upload Run</v-btn>
          </v-form>
        </v-card>
      </template>

      

    </v-stepper>
    </v-card-text>
    <v-card-actions>
      <v-stepper-actions @click:prev="stepperModel = Math.max(1, stepperModel - 1)" @click:next="stepperModel = Math.max(1, stepperModel +1)" :disabled='disableUploadStepper'></v-stepper-actions>
    </v-card-actions>
    </v-card>
  </v-dialog>

  <h2>Your Uploaded Runs</h2>
  <uploaded-run-list :task_id="task_id" :vm_id="user_id_for_task" ref="simplified-upload-run-list"/>

  
</template>

<script>
import { inject } from 'vue'

import { VAutocomplete } from 'vuetify/components'
import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, post_file, reportSuccess, get_link_to_organizer, get_contact_link_to_organizer } from "@/utils";
import { Loading, LoginToSubmit, UploadedRunList } from "@/components";
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";
import ImportSubmission from "./ImportSubmission.vue";
import CodeSnippet from "../components/CodeSnippet.vue";
import UploadSubmissionViaCli from "./UploadSubmissionViaCli.vue"

export default {
  name: "upload-submission",
  components: { EditSubmissionDetails, Loading, VAutocomplete, LoginToSubmit, UploadedRunList, ImportSubmission, CodeSnippet, UploadSubmissionViaCli },
  props: ['organizer', 'organizer_id'],
  emits: ['refresh_running_submissions'],
  data() {
    return {
      userinfo: inject('userinfo'),
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_task: extractUserFromCurrentUrl(),
      showUploadForm: false,
      uploading: false,
      uploadDataset: '',
      uploadFormError: '',
      upload_type: 'upload-1',
      upload_configuration: '',
      upload_type_next_upload: '',
      stepperModel: '',
      fileHandle: null,
      upload_form_valid: false,
      description: '',
      run_name: '',
      error_message: '',
      editUploadMetadataToggle: false,
      hf_model_available: 'loading',
      selectedDataset: '',
      showImportSubmission: false,
      upload_for_approach: false,
      token: 'YOUR-TOKEN-HERE',
      datasets: [{ "dataset_id": "loading...", "display_name": "loading...", }],
      rest_url: inject("REST base URL"),
    }
  },
  computed: {
    link_organizer() { return get_link_to_organizer(this.organizer_id); },
    contact_organizer() { return get_contact_link_to_organizer(this.organizer_id); },
    
    disableUploadStepper() {
      if (this.stepperModel == '1' && !this.upload_configuration) {
        return 'next';
      }

      if (this.stepperModel == '2' && this.upload_configuration != 'upload-config-1') {
        return 'next'
      }

      const valid = this.run_name && this.run_name.length >= 3 && this.run_name.length <= 20 && this.description && this.description.length >= 3 && this.selectedDataset

      if (this.stepperModel == '2' && this.upload_configuration == 'upload-config-1' && !valid) {
        return 'next'
      }

      if (this.stepperModel == '3') {
        return 'next'
      }

      return false;
    }
  },
  methods: {
    async fileUpload() {  // async
      const { valid } = await (this.$refs.form).validate()
      console.log('' + this.fileHandle)
      console.log(valid)
      if (!valid) {
        return
      }

      this.uploading = true
      let formData = new FormData();
      this.error_message = ''
      formData.append("file", this.fileHandle);
      formData.append("display_name", this.run_name);
      formData.append("description", this.description);
      let endpoint = this.rest_url + `/task/${this.task_id}/vm/${this.user_id_for_task}/upload/${this.selectedDataset}/new-submission`
      post_file(endpoint, formData, this.userinfo, true)
        .then(reportSuccess("File Uploaded Successfully. It might take a few minutes until the evaluation is finished."))
        .catch(e => {
          this.error_message = e["message"];
          reportError("Problem While Uploading File.", "This might be a short-term hiccup, please try again. We got the following error: ")(e)
        })
        .then(() => {
          this.uploading = false;
          if (!this.error_message) {
            this.clean_formular()
            this.upload_for_approach = false
          }
        })
    },
    clean_formular() {
      this.uploading = false
      this.fileHandle = null
      this.selectedDataset = ''
      this.description = ''
      this.run_name = ''
      this.stepperModel = ''
      this.upload_configuration = ''
      this.showUploadForm = false
      this.$emit('refresh_running_submissions')
      this.$refs['simplified-upload-run-list'].fetchData()
    }
  },
  beforeMount() {
    get(this.rest_url + '/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_task + '/upload')
      .then(inject_response(this, { 'loading': false }, true))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))

    get(this.rest_url + '/api/token/' + this.user_id_for_task)
      .then(inject_response(this))
  },
}
</script>
