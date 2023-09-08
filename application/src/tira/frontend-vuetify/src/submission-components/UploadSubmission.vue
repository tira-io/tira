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
        <v-tab variant="outlined" v-for="us in this.filteredSoftwares" :value="us.id">
          {{ us.display_name }}
        </v-tab>
      </v-tabs>
    </v-col>
    <v-col cols="2">
      <v-tabs v-model="tab" fixed-tabs class="mb-10">
        <v-tab value="newUploadGroup" color="primary" style="max-width: 100px;" variant="outlined">
          <v-icon>mdi-plus</v-icon>
        </v-tab>
      </v-tabs>
    </v-col>
  </v-row>
  <v-window v-model="tab" v-if="!loading && role !== 'guest'">
          <v-window-item value="newUploadGroup">
              <h2>Create Run Upload Group</h2>
              <p>Please click on "Add Upload Group" below to create a new run upload group.</p>
              <p>Please use one upload group (you can edit the metadata of an upload group later) per approach. I.e., in TIRA, you can usually run software submissions on different datasets. For manually uploaded runs, we employ the same methodology: Please create one run upload group per approach, so that you can upload "executions" of the same approach on different datasets while maintaining the documentation.</p>

              <br>

              <v-btn variant="outlined" @click="addUpload()">
                  Add Upload Group
              </v-btn>
          </v-window-item>
          <v-window-item v-for="us in this.all_uploadgroups" :value="us.id">

            <div class="d-flex justify-lg-space-between">
              <p>Please add a description that describes uploads of this type.</p>
              <div>
               <edit-submission-details
                  type='upload' :id="us.id" :user_id="user_id_for_task"
              />
              <v-btn variant="outlined" color="red" @click="deleteUpload(us.id)"><v-tooltip
                activator="parent"
                location="bottom"
              >Attention! This deletes the container and ALL runs associated with it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>
              </div>
            </div>
            <v-form>
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
            </v-form>

            <v-btn color="primary" :loading="uploading" :disabled="uploading || fileHandle === null || selectedDataset === ''"
                   @click="fileUpload(us.id)">Upload Run</v-btn>


            <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id_for_task" :upload_id="us.id" />
          </v-window-item>
    </v-window>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'
import {
  extractTaskFromCurrentUrl,
  extractUserFromCurrentUrl,
  get,
  inject_response,
  reportError,
  extractRole,
  filterByDisplayName,
  post_file
} from "@/utils";
import {Loading, LoginToSubmit, RunList} from "@/components";
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";

export default {
  name: "upload-submission",
  components: {EditSubmissionDetails, Loading, VAutocomplete, LoginToSubmit, RunList},
  props: ['organizer', 'organizer_id'],
  data () {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id_for_task: extractUserFromCurrentUrl(),
      role: extractRole(), // Values: guest, user, participant, admin
      tab: null,
      software_filter: null,
      showUploadForm: false,
      uploading: false,
      uploadDataset: '',
      uploadFormError: '',
      fileHandle: null,
      editUploadMetadataToggle: false,
      all_uploadgroups: [{"id": null, "display_name": 'loading...'}],
      selectedDataset: '',
      datasets: [{"dataset_id": "loading...", "display_name": "loading...",}]
    }
  },
    computed: {
    filteredSoftwares() {
      return filterByDisplayName(this.all_uploadgroups, this.software_filter)
    },
  },
  methods: {
    addUpload() {
       get(`/task/${this.task_id}/vm/${this.user_id_for_task}/add_software/upload`).then(message => {
                this.all_uploadgroups.push({"id": message.context.upload.id, "display_name": message.context.upload.display_name})
                this.tab = message.context.upload.display_name
            })
            .catch(reportError("Problem While Adding New Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
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
            console.log(this.uploading, this.selectedDataset, this.fileHandle)
            this.uploading = true
            let formData = new FormData();
            console.log(formData)
            formData.append("file", this.fileHandle[0]);
            post_file(`/task/${this.task_id}/vm/${this.user_id_for_task}/upload/${this.selectedDataset}/${id_to_upload}`, formData)
                .then(message => {})
                .catch(reportError("Problem While Uploading File.", "This might be a short-term hiccup, please try again. We got the following error: "))
                .then(() => {this.uploading = false})
    },
  },
  beforeMount() {
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id_for_task + '/upload')
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.tab = this.all_uploadgroups[0].display_name
  },
}
</script>
