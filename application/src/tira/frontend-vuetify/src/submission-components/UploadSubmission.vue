<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
  <v-row v-if="!loading && role !== 'guest'">
    <v-col :cols="$vuetify.display.mdAndUp ? '9' : '12'">
      <v-autocomplete clearable auto-select-first label="Choose upload &hellip;" prepend-inner-icon="mdi-magnify" :items="this.uploadGroups" item-title="display_name" item-value="id"
                    variant="underlined" v-model="tab"/>
    </v-col>
    <v-col v-if="!$vuetify.display.smAndDown" :cols="$vuetify.display.mdAndUp ? '3' : '0'">
      <v-btn color="primary" v-if="!$vuetify.display.mdAndUp" icon="mdi-plus" @click="this.tab = 'newUploadGroup'"/>
        <v-btn color="primary" v-if="$vuetify.display.mdAndUp" prepend-icon="mdi-plus" size="large" @click="this.tab = 'newUploadGroup'" block>New Uploadgroup</v-btn>
    </v-col>
  </v-row>
  <v-row v-if="$vuetify.display.smAndDown">
    <v-col :cols="12">
        <v-btn color="primary" prepend-icon="mdi-plus" size="large" @click="this.tab = 'newUploadGroup'" block rounded>New Uploadgroup</v-btn>
    </v-col>
  </v-row>
  <v-row v-if="!loading && role !== 'guest'">
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
  <v-window v-model="tab" v-if="!loading && role !== 'guest'" :touch="{left: null, right: null}">
          <v-window-item value="newUploadGroup">
              <h2>Create Run Upload Group</h2>
              <p>Please click on "Add Upload Group" below to create a new run upload group.</p>
              <p>Please use one upload group (you can edit the metadata of an upload group later) per approach. I.e., in TIRA, you can usually run software submissions on different datasets. For manually uploaded runs, we employ the same methodology: Please create one run upload group per approach, so that you can upload "executions" of the same approach on different datasets while maintaining the documentation.</p>

              <br>

              <v-form>
                <v-radio-group v-model="upload_type">
                  <v-radio label="Rename all uploaded files as configured by the organizers" value="upload-1"/>
                  <v-radio label="I want to configure the name of my uploaded file manually (Only for expert users, e.g., to normalize all uploaded files of this group.)" value="upload-2"/>
                </v-radio-group>

                <v-text-field v-if="upload_type === 'upload-2'" v-model="rename_file_to" label="Rename a file after upload to this name " />
              </v-form>

              <v-btn variant="outlined" @click="addUpload()">
                  Add Upload Group
              </v-btn>

              <div v-if="!showImportSubmission">
              <br>
              If you participate in multiple tasks, you can also <a href="javascript:void(0);" @click="showImportSubmission=true">import your upload group</a>.
              </div>
              <div v-if="showImportSubmission">
                <br>
                <import-submission submission_type="upload"/>
              </div>
          </v-window-item>
          <v-window-item v-for="us in this.all_uploadgroups" :value="us.id">
            <loading :loading="description === 'no-description'"/>
            <div v-if="description !== 'no-description'" class="d-flex flex-column">

              <div class="d-flex justify-end">
                <edit-submission-details class="mr-3" type='upload' :id="us.id" :user_id="user_id_for_task" @edit="(i) => updateUploadDetails(i)"/>
                <v-btn variant="outlined" color="red" @click="deleteUpload(us.id)"><v-tooltip
                  activator="parent"
                  location="bottom"
                >Attention! This deletes the container and ALL runs associated with it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>

              </div>
              <div class="my-5">
                <p>{{ description }}</p>
              </div>

            </div>
            <v-form v-if="description !== 'no-description'">
              <v-file-input v-model="fileHandle"
                            :rules="[v => !!v || 'File is required']"
                            label="Click to add run file"
              ></v-file-input>
              <v-autocomplete label="Input Dataset"
                      :items="datasets"
                      item-title="display_name"
                      item-value="dataset_id"
                      prepend-icon="mdi-file-document-multiple-outline"
                      v-model="selectedDataset"
                      variant="underlined"
                      clearable/>
              <v-text-field v-if="'' + rename_to !== 'null' && '' + rename_to !== '' && '' + rename_to !== 'undefined'" v-model="rename_to" label="Uploaded Files are renamed to (immutable for reproducibility)" disabled="true"/>
            </v-form>

            <v-btn v-if="description !== 'no-description'" color="primary" :loading="uploading" :disabled="uploading || fileHandle === null || selectedDataset === ''"
                   @click="fileUpload(us.id)">Upload Run</v-btn>


            <h2>Submissions</h2>
            <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id_for_task" :upload_id="us.id" ref="upload-run-list" />
          </v-window-item>
    </v-window>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'
import { extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, extractRole, post_file, reportSuccess, handleModifiedSubmission } from "@/utils";
import { Loading, LoginToSubmit, RunList } from "@/components";
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";
import ImportSubmission from "./ImportSubmission.vue";

export default {
  name: "upload-submission",
  components: {EditSubmissionDetails, Loading, VAutocomplete, LoginToSubmit, RunList, ImportSubmission},
  props: ['organizer', 'organizer_id'],
  emits: ['refresh_running_submissions'],
  data () {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_task: extractUserFromCurrentUrl(),
      role: extractRole(), // Values: guest, user, participant, admin
      tab: null,
      showUploadForm: false,
      uploading: false,
      uploadDataset: '',
      uploadFormError: '',
      upload_type: 'upload-1',
      rename_file_to: '',
      fileHandle: null,
      description: 'no-description',
      rename_to: '',
      editUploadMetadataToggle: false,
      all_uploadgroups: [{"id": null, "display_name": 'loading...'}],
      selectedDataset: '',
      showImportSubmission: false,
      datasets: [{"dataset_id": "loading...", "display_name": "loading...",}]
    }
  },
  computed: {
    uploadGroups() {
      let ret = []

      if (this.tab === 'newUploadGroup') {
        ret = ret.concat([{'id': 'newUploadGroup', 'display_name': ' '}])
      }

      return ret.concat(this.all_uploadgroups)
    }
  },
  methods: {
    addUpload() {
      let upload_type_var = '?rename_to='
      if (this.upload_type === 'upload-2') {
        upload_type_var += this.rename_file_to
      }

      get(`/task/${this.task_id}/vm/${this.user_id_for_task}/add_software/upload${upload_type_var}`).then(message => {
              this.all_uploadgroups.push({"id": message.context.upload.id, "display_name": message.context.upload.display_name})
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
      get(`/task/${this.task_id}/vm/${this.user_id_for_task}/upload-delete/${this.tab}`)
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
      formData.append("file", this.fileHandle[0]);
      post_file(`/task/${this.task_id}/vm/${this.user_id_for_task}/upload/${this.selectedDataset}/${id_to_upload}`, formData)
      .then(reportSuccess("File Uploaded Successfully. It might take a few minutes until the evaluation is finished."))
      .catch(reportError("Problem While Uploading File.", "This might be a short-term hiccup, please try again. We got the following error: "))
      .then(() => {this.clean_formular()})
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
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_task + '/upload')
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.tab = this.all_uploadgroups[0].display_name
  },
  watch: {
    tab(new_value, old_value) {
      this.description = 'no-description'
      this.rename_to = ''
      if (new_value !== 'newUploadGroup' && '' + new_value !== 'null' && '' + new_value !== 'undefined' && '' + new_value !== 'loading...') {
        get(`/api/upload-group-details/${this.task_id}/${this.user_id_for_task}/${new_value}`).then(message => {
          this.description = message.context.upload_group_details.description
          this.rename_to = message.context.upload_group_details.rename_to
        })
      }
    }
  }
}
</script>
