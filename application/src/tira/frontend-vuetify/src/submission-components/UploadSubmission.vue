<template>
  <loading :loading="loading"/>
  <login-to-submit v-if="!loading && role === 'guest'"/>
<v-tabs v-model="tab" v-if="!loading && role !== 'guest'"
    fixed-tabs class="my-10">
            <v-tab value="newUploadGroup" variant="outlined">Add new upload group</v-tab>
            <v-tab variant="outlined" v-for="uploadGroup in this.all_uploadgroups" :value="uploadGroup.display_name">
         {{ uploadGroup.display_name }} </v-tab>
  </v-tabs>
  <v-window v-model="tab" v-if="!loading && role !== 'guest'">
          <v-window-item value="newUploadGroup">
              <h2>Create Run Upload Group</h2>
              <p>Please click on "Add Upload Group" below to create a new run upload group.</p>
              <p>Please use one upload group (you can edit the metadata of an upload group later) per appraoch. I.e., in TIRA, you can usually run software submissions on different datasets. For manually uploaded runs, we employ the same methodology: Please create one run upload group per approach, so that you can upload "executions" of the same approach on different datasets while maintaining the documentation.</p>

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
              <v-btn variant="outlined" color="red"><v-tooltip
                activator="parent"
                location="bottom"
              >Attention! This deletes the container and ALL runs associated with it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>
              </div>
            </div>
            <v-form>
              <v-file-input
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

            <v-btn :disabled="uploading || fileHandle === null || selectedDataset === 'None'"
                   @click="fileUpload()">Upload Run</v-btn>
          </v-window-item>
    </v-window>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'
import {extractTaskFromCurrentUrl, extractUserFromCurrentUrl, get, inject_response, reportError, extractRole} from "@/utils";
import {Loading, LoginToSubmit} from "@/components";

export default {
  name: "UploadSubmission",
  components: {Loading, VAutocomplete, LoginToSubmit},

  data () {
    return {
      loading: true,
      task_id: extractTaskFromCurrentUrl(),
      user_id: extractUserFromCurrentUrl(),
      role: extractRole(), // Values: guest, user, participant, admin
      tab: null,
      showUploadForm: false,
      uploadDataset: '',
      uploadFormError: '',
      fileHandle: null,
      uploading: false,
      editUploadMetadataToggle: false,
      all_uploadgroups: [{"display_name": 'loading...'}],
      selectedDataset: '',
      datasets: [{"dataset_id": "loading...", "display_name": "loading...",}]
    }
  },
  methods: {
    addUpload() {
       get(`/task/${this.task_id}/vm/${this.user_id}/add_software/upload`).then(message => {
                this.all_uploadgroups.push({"display_name": message.context.upload.display_name})
                this.tab = message.context.upload.display_name
            })
            .catch(reportError("Problem While Adding New Upload Group.", "This might be a short-term hiccup, please try again. We got the following error: "))
    }
  },
  beforeMount() {
    get('/api/submissions-for-task/' + this.task_id + '/' + this.user_id + '/upload')
      .then(inject_response(this, {'loading': false}, true))
      .catch(reportError("Problem While Loading The Submissions of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
  },
}
</script>
