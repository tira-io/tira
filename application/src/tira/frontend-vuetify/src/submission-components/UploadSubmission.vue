<template>
<v-tabs v-model="tab"
    fixed-tabs class="my-10">
            <v-tab value="newUploadGroup" variant="outlined" @click="uploadgroupselected='';">Add new upload group</v-tab>
            <v-tab variant="outlined" v-for="uploadGroup in this.all_uploadgroups" :value="uploadGroup.display_name">
         {{ uploadGroup.display_name }} </v-tab>
  </v-tabs>
  <v-window v-model="tab">
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
                accept=""
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

            <v-btn :disabled="uploading || fileHandle === null || uploadDataset === 'None'"
                   @click="fileUpload()">Upload Run</v-btn>
          </v-window-item>
    </v-window>
</template>

<script>

import { VAutocomplete } from 'vuetify/components'

export default {
  name: "UploadSubmission",
  components: {VAutocomplete},
  data () {
      return {
        tab: null,
        showUploadForm: false,
        uploadDataset: '',
        uploadFormError: '',
        fileHandle: null,
        uploading: false,
        uploadgroupselected: null,
        editUploadMetadataToggle: false,
        all_uploadgroups: [
                    {"display_name": 'spiky-dandelion'},
                    {"display_name": 'snobby-pup'},
                    {"display_name": 'dry-heaven'}],
        selectedDataset: '',
        datasets: [{
                "dataset_id": "1",
                "display_name": "task-1-type-classification",
                "is_confidential": true,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 10,
                "runs_count": 220,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }, {
                "dataset_id": "2",
                "display_name": "task-1-type-classification-validation",
                "is_confidential": false,
                "is_deprecated": false,
                "year": "2022-11-15 06:51:49.117415",
                "task": "clickbait-spoiling",
                "software_count": 20,
                "runs_count": 100,
                "created": "2022-11-15",
                "last_modified": "2022-11-15"
            }
        ],
      }
  },
  methods: {
    addUpload() {
      const new_uploadgroup = {"display_name": 'new-upload-group_' + Math.floor(Math.random() * 1000)};
      this.all_uploadgroups.push(new_uploadgroup);
      this.tab = new_uploadgroup.display_name;
    },
  }
}
</script>
