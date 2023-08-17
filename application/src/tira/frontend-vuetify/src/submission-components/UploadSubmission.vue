<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
<v-tabs v-model="tab" v-if="!loading && role !== 'guest'"
    fixed-tabs class="my-10">
  <v-tab variant="outlined" v-for="uploadGroup in this.all_uploadgroups" :value="uploadGroup.display_name">
         {{ uploadGroup.display_name }}
  </v-tab>
   <v-tab value="newUploadGroup" color="primary" style="max-width: 100px;" variant="outlined"><v-icon>mdi-tab-plus</v-icon></v-tab>
  </v-tabs>
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
          <v-window-item v-for="uploadGroup in this.all_uploadgroups" :value="uploadGroup.display_name">
            <div class="d-flex justify-lg-space-between">
              <h2>{{ uploadGroup.display_name }}</h2>
              <p>Please add a description that describes uploads of this type.</p>
              <div>
              <v-btn variant="outlined" color="#303f9f"><v-icon>mdi-file-edit-outline</v-icon>Edit</v-btn>
              <v-btn variant="outlined" color="red" @click="deleteUpload()"><v-tooltip
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

            <v-btn color="primary" :disabled="uploading || fileHandle === null || selectedDataset === ''"
                   @click="fileUpload()">Upload Run</v-btn>


            <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id" :upload_id="uploadGroup.id" />
          </v-window-item>
    </v-window>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'
import {extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, extractRole} from "@/utils";
import {Loading, LoginToSubmit, RunList} from "@/components";

export default {
  name: "upload-submission",
  components: {Loading, VAutocomplete, LoginToSubmit, RunList},
  props: ['organizer', 'organizer_id'],
  data () {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id: extractUserFromCurrentUrl(),
      role: extractRole(), // Values: guest, user, participant, admin
      tab: null,
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
  methods: {
    addUpload() {
       get(`/task/${this.task_id}/vm/${this.user_id}/add_software/upload`).then(message => {
                this.all_uploadgroups.push({"id": message.context.upload.id, "display_name": message.context.upload.display_name})
                this.tab = message.context.upload.display_name
            })
            .catch(reportError("Problem While Adding New Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    deleteUpload() {
            get(`/task/${this.task_id}/vm/${this.user_id}/upload-delete/${this.tab}`)
                .then(message => {
                    this.all_uploadgroups = this.all_uploadgroups.filter(i => i.id != this.all_uploadgroups.find(i => i.display_name === this.tab).id)
                    this.tab = this.all_uploadgroups.length > 0 ? this.all_uploadgroups[0].display_name : null
                    this.showUploadForm = false
                })
                .catch(reportError("Problem While Deleting Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
        },
    //TODO not working yet, forbidden?? maybe needs crfs token?
    async fileUpload() {  // async
            console.log(this.uploading, this.selectedDataset, this.fileHandle)
            this.uploading = true
            let formData = new FormData();
            console.log(formData)
            formData.append("file", this.fileHandle);
            const response = await fetch(`/task/${this.task_id}/vm/${this.user_id}/upload/${this.selectedDataset}/${this.all_uploadgroups.find(i => i.display_name == this.tab).id}`, {
              method: "POST",
              body: formData
            }).catch(reportError("Problem While Uploading File.", "This might be a short-term hiccup, please try again. We got the following error: "))

            this.uploading = false
        },
  },
  beforeMount() {
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id + '/upload')
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
    this.tab = this.all_uploadgroups[0].display_name
  },
}
</script>
