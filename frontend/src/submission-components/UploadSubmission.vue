<template>
  <loading :loading="loading" />

  <login-to-submit v-if="!loading && userinfo.role === 'guest'" />
  <v-row v-if="!loading && userinfo.role !== 'guest'">
    <v-col :cols="$vuetify.display.mdAndUp ? '9' : '12'">
      <v-autocomplete clearable auto-select-first label="Choose upload &hellip;" prepend-inner-icon="mdi-magnify"
        :items="this.uploadGroups" item-title="display_name" item-value="id" variant="underlined" v-model="tab" />
    </v-col>
    <v-col v-if="!$vuetify.display.smAndDown" :cols="$vuetify.display.mdAndUp ? '3' : '0'">
      <v-btn color="primary" v-if="!$vuetify.display.mdAndUp" icon="mdi-plus" @click="this.tab = 'newUploadGroup'" />
      <v-btn color="primary" v-if="$vuetify.display.mdAndUp" prepend-icon="mdi-plus" size="large"
        @click="this.tab = 'newUploadGroup'" block>New Approach</v-btn>
    </v-col>
  </v-row>
  <v-row v-if="$vuetify.display.smAndDown">
    <v-col :cols="12">
      <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="this.tab = 'newUploadGroup'" block rounded>New
        Approach</v-btn>
    </v-col>
  </v-row>
  <v-row v-if="!loading && userinfo.role !== 'guest'">
    <v-col cols="10">
      <v-tabs v-model="tab" fixed-tabs class="mb-10 d-none">
        <v-tab variant="outlined" v-for="us in this.filteredSoftwares" :value="us.id">
          {{ us.display_name }}
        </v-tab>
      </v-tabs>
    </v-col>
    <v-col cols="2">
      <v-tabs v-model="tab" fixed-tabs class="mb-10 d-none">
        <v-tab value="newUploadGroup" color="primary" style="max-width: 100px;" variant="outlined">
          <v-icon>mdi-plus</v-icon>
        </v-tab>
      </v-tabs>
    </v-col>
  </v-row>
  <v-window v-model="tab" v-if="!loading && userinfo.role !== 'guest'" :touch="{ left: null, right: null }">
    <v-window-item value="newUploadGroup">
      <h2>New Upload</h2>
      <v-stepper :items="['About', 'Specify Metadata', 'Upload']" v-model="stepperModel" hide-actions="true" flat
        :border=false>
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
              In TIRA, approaches are often evaluated on multiple datasets. Please ensure that you correctly group runs
              created by the same approach. <span v-if="userUploadGroups.length == 0">You have no upload groups
                yet.</span>
              <span v-if="userUploadGroups.length > 0">You already have uploads for the following approaches:
                <v-list density="compact">
                  <v-list-item v-for="i in userUploadGroups">
                    <v-list-item-title>Upload run(s) for approach <a href="javascript:void(0);"
                        @click="stepperModel = 1; tab = i.id">{{ i.display_name }}</a></v-list-item-title>
                  </v-list-item>
                </v-list>
              </span>

              <div>
                <v-checkbox label="I want to upload runs for a new approach" v-model="new_approach"></v-checkbox>

                <div v-if="new_approach">
                  <p>You will create a new run upload group. Please ensure that you only create only one run upload
                    group per approach, so that you can upload "executions" of the same approach on different datasets
                    while maintaining the documentation.</p>
                  <v-form>
                    <v-radio-group v-model="upload_type">
                      <v-radio label="Rename all uploaded files as configured by the organizers" value="upload-1" />
                      <v-radio
                        label="I want to configure the name of my uploaded file manually (Only for expert users, e.g., to normalize all uploaded files of this group.)"
                        value="upload-2" />
                    </v-radio-group>

                    <v-text-field v-if="upload_type === 'upload-2'" v-model="rename_file_to"
                      label="Rename a file after upload to this name " />
                  </v-form>

                  <p>Please click on "Add Upload Group" to create a new run upload group (i.e., if the run that you want
                    to upload does not belong to the upload groups listed above).</p>

                  <v-btn variant="outlined" @click="addUpload()">Add Upload Group</v-btn>

                  <div v-if="!showImportSubmission">
                    <br>
                    If you participate in multiple tasks, you can also <a href="javascript:void(0);"
                      @click="showImportSubmission = true">import your upload group</a>.
                  </div>
                  <div v-if="showImportSubmission">
                    <br>
                    <import-submission submission_type="upload" />
                  </div>
                </div>
              </div>
            </div>
          </v-card>
        </template>

        <v-stepper-actions @click:prev="stepperModel = Math.max(1, stepperModel - 1)" @click:next="stepperModel = Math.max(1, stepperModel +1)"
          :disabled='disableUploadStepper'></v-stepper-actions>

      </v-stepper>
      <br>


    </v-window-item>
    <v-window-item v-for="us in this.all_uploadgroups" :value="us.id">
      <loading :loading="description === 'no-description'" />

      <div v-if="description !== 'no-description'" class="d-flex flex-column">

        <div class="d-flex justify-end">
          <edit-submission-details class="mr-3" type='upload' :id="us.id" :user_id="user_id_for_task"
            @edit="(i) => updateUploadDetails(i)" />
          <v-btn variant="outlined" color="red" @click="deleteUpload(us.id)"><v-tooltip activator="parent"
              location="bottom">Attention! This deletes the container and ALL runs associated with
              it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>

        </div>
        <div class="my-5">
          <p>{{ description }}</p>
        </div>

      </div>

      <h2>Your Existing Submissions for Approach {{ us.display_name }}</h2>
      <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id_for_task"
        :upload_id="us.id" ref="upload-run-list" from_archive="false"/>

    
      <v-btn class="my-5" v-if="description !== 'no-description' && !upload_for_approach" color="primary" prepend-icon="mdi-plus" size="large"
        @click="this.upload_for_approach = true" block>Upload New Submission for Approach {{ us.display_name }}</v-btn>
      <v-form class="my-5"  v-if="description !== 'no-description' && upload_for_approach">
        <h2>Upload new Submissions for Approach {{ us.display_name }}</h2>
        <v-radio-group v-model="upload_type_next_upload">
          <v-radio :label="'I want to upload runs for approach ' + us.display_name + ' via the command line'"
            value="upload-via-script"/>
          <v-radio :label="'I want to upload a new run for approach ' + us.display_name + ' via the web UI'"
            value="upload-via-ui" />
        </v-radio-group>
        <div v-if="upload_type_next_upload == 'upload-via-script'">
          <upload-submission-via-cli :token="token" :datasets="datasets" :approach="us.display_name"/>
        </div>
        <div v-if="upload_type_next_upload == 'upload-via-ui'">
          <v-file-input v-model="fileHandle" :rules="[v => !!v || 'File is required']" label="Click to add run file" />
          <v-autocomplete label="Input Dataset" :items="datasets" item-title="display_name" item-value="dataset_id"
            prepend-icon="mdi-file-document-multiple-outline" v-model="selectedDataset" variant="underlined"
            clearable />
          <v-text-field v-if="'' + rename_to !== 'null' && '' + rename_to !== '' && '' + rename_to !== 'undefined'"
            v-model="rename_to" label="Uploaded Files are renamed to (immutable for reproducibility)" disabled="true" />
        </div>

        <v-row>
          <v-col cols="12"><v-alert v-if="error_message" title="Uploading the run failed. Maybe a short hiccup?" type="error" closable :text="error_message"/></v-col>
        </v-row>

        <v-btn v-if="description !== 'no-description' && upload_type_next_upload == 'upload-via-ui'" color="primary"
        :loading="uploading" :disabled="uploading || fileHandle === null || selectedDataset === ''"

        class="my-5" prepend-icon="mdi-plus" size="large" block

        @click="fileUpload(us.id)">Upload Run</v-btn>
      </v-form>
    </v-window-item>
  </v-window>
</template>

<script>
import { inject } from 'vue'

import { VAutocomplete } from 'vuetify/components'
import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, extractSoftwareIdFromCurrentUrl, get, inject_response, reportError, post_file, reportSuccess, handleModifiedSubmission, get_link_to_organizer, get_contact_link_to_organizer } from "@/utils";
import { Loading, LoginToSubmit, RunList } from "@/components";
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";
import ImportSubmission from "./ImportSubmission.vue";
import CodeSnippet from "../components/CodeSnippet.vue";
import UploadSubmissionViaCli from "./UploadSubmissionViaCli.vue"

export default {
  name: "upload-submission",
  components: { EditSubmissionDetails, Loading, VAutocomplete, LoginToSubmit, RunList, ImportSubmission, CodeSnippet, UploadSubmissionViaCli },
  props: ['organizer', 'organizer_id'],
  emits: ['refresh_running_submissions'],
  data() {
    return {
      userinfo: inject('userinfo'),
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_task: extractUserFromCurrentUrl(),
      tab: null,
      showUploadForm: false,
      uploading: false,
      uploadDataset: '',
      uploadFormError: '',
      upload_type: 'upload-1',
      new_approach: false,
      upload_configuration: '',
      upload_type_next_upload: '',
      rename_file_to: '',
      hugging_face_model: '',
      stepperModel: '',
      fileHandle: null,
      description: 'no-description',
      rename_to: '',
      error_message: '',
      editUploadMetadataToggle: false,
      hf_model_available: 'loading',
      all_uploadgroups: [{ "id": null, "display_name": 'loading...' }],
      selectedDataset: '',
      showImportSubmission: false,
      upload_for_approach: false,
      token: 'YOUR-TOKEN-HERE',
      datasets: [{ "dataset_id": "loading...", "display_name": "loading...", }],
      rest_url: inject("REST base URL"),
    }
  },
  computed: {
    uploadGroups() {
      let ret = []

      if (this.tab === 'newUploadGroup') {
        ret = ret.concat([{ 'id': 'newUploadGroup', 'display_name': ' ' }])
      }

      return ret.concat(this.all_uploadgroups)
    },
    userUploadGroups() {
      let ret = []

      for (let i of this.all_uploadgroups) {
        if (i.display_name != 'default upload') {
          ret.push(i)
        }
      }

      return ret
    },
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
    addUpload() {
      let upload_type_var = '?rename_to='
      if (this.upload_type === 'upload-2') {
        upload_type_var += this.rename_file_to
      }

      get(this.rest_url + `/task/${this.task_id}/vm/${this.user_id_for_task}/add_software/upload${upload_type_var}`).then(message => {
        this.all_uploadgroups.push({ "id": message.context.upload.id, "display_name": message.context.upload.display_name })
        this.tab = message.context.upload.id
        this.upload_type = 'upload-1'
        this.rename_file_to = ''
      })
        .then(reportSuccess("Upload Group Added Successfully."))
        .catch(reportError("Problem While Adding New Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    updateUploadDetails(editedDetails) {
      this.description = editedDetails.description
      handleModifiedSubmission(editedDetails, this.all_uploadgroups)
    },
    deleteUpload(id_to_delete) {
      get(this.rest_url + `/task/${this.task_id}/vm/${this.user_id_for_task}/upload-delete/${this.tab}`)
        .then(message => {
          this.all_uploadgroups = this.all_uploadgroups.filter(i => i.id !== id_to_delete)
          this.tab = this.all_uploadgroups.length > 0 ? this.all_uploadgroups[0].display_name : null
          this.showUploadForm = false
        })
        .catch(reportError("Problem While Deleting Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    async fileUpload(id_to_upload) {  // async
      this.uploading = true
      let formData = new FormData();
      this.error_message = ''
      formData.append("file", this.fileHandle);
      let endpoint = this.rest_url + `/task/${this.task_id}/vm/${this.user_id_for_task}/upload/${this.selectedDataset}/${id_to_upload}`
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
      this.$emit('refresh_running_submissions')
      for (let i of this.$refs['upload-run-list']) {
        i.fetchData()
      }
    }
  },
  beforeMount() {
    get(this.rest_url + '/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_task + '/upload')
      .then(inject_response(this, { 'loading': false }, true))
      .then((i) => {
        if(extractSoftwareIdFromCurrentUrl() !== null) {
          this.tab = extractSoftwareIdFromCurrentUrl()
        }
      })
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))

    get(this.rest_url + '/api/token/' + this.user_id_for_task)
      .then(inject_response(this))

    this.tab = this.all_uploadgroups[0].display_name
  },
  watch: {
    tab(new_value, old_value) {
      this.description = 'no-description'
      this.rename_to = ''
      if (new_value !== 'newUploadGroup' && '' + new_value !== 'null' && '' + new_value !== 'undefined' && '' + new_value !== 'loading...') {
        get(this.rest_url + `/api/upload-group-details/${this.task_id}/${this.user_id_for_task}/${new_value}`).then(message => {
          this.description = message.context.upload_group_details.description
          this.rename_to = message.context.upload_group_details.rename_to
        })
      }
    }
  }
}
</script>
