<template>
<v-card tonal class="my-10">
          <v-card-item>
            <v-btn variant="outlined" @click="showUploadForm=false; uploadgroupselected=''; editUploadMetadataToggle=false;">Add new upload group</v-btn>
            <v-btn variant="outlined" v-for="uploadGroup in this.all_uploadgroups"
                    @click="uploadgroupselected=uploadGroup ;showUploadForm=true; editUploadMetadataToggle=false;">
         {{ uploadGroup.display_name }} </v-btn>
          </v-card-item>
          <v-card-item v-if="!showUploadForm">
            <h2>Create Run Upload Group</h2>
              <p>Please click on "Add Upload Group" below to create a new run upload group.</p>
              <p>Please use one upload group (you can edit the metadata of an upload group later) per appraoch. I.e., in TIRA, you can usually run software submissions on different datasets. For manually uploaded runs, we employ the same methodology: Please create one run upload group per approach, so that you can upload "executions" of the same approach on different datasets while maintaining the documentation.</p>

              <br>

              <v-btn variant="outlined" @click="addUpload()">
                  Add Upload Group
              </v-btn>
          </v-card-item>
          <v-card-item v-if="showUploadForm">
            <v-card-actions class="d-flex justify-lg-space-between">
              <p>Please add a description that describes uploads of this type.</p>
              <div>
              <v-btn variant="outlined" color="#303f9f"><v-icon>mdi-file-edit-outline</v-icon>Edit</v-btn>
              <v-btn variant="outlined" color="red"><v-tooltip
                activator="parent"
                location="bottom"
              >Attention! This deletes the container and ALL runs associated with it</v-tooltip><v-icon>mdi-delete-alert-outline</v-icon>Delete</v-btn>
              </div>
            </v-card-actions>
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
          </v-card-item>
        </v-card>
</template>

<script>
export default {
  name: "UploadSubmission",
  props: ['csrf', 'datasets', 'upload', "taskid", "userid", "running_evaluations"],
  emits: ['addNotification', 'pollEvaluations', 'removeRun', 'addUploadgroup'],
  data () {
      return {
        showUploadForm: false,
        uploadDataset: '',
        uploadFormError: '',
        fileHandle: null,
        uploading: false,
        uploadgroupselected: null,
        editUploadMetadataToggle: false,
        all_uploadgroups: [],
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
        async get(url) {
            const response = await fetch(url)
            if (!response.ok) {
                throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
            }
            let results = await response.json()
            if (results.status === 1) {
                throw new Error(`${results.message}`);
            }
            return results
        },
        deleteUpload() {
            this.get(`/task/${this.taskid}/vm/${this.userid}/upload-delete/${this.uploadgroupselected.id}`)
                .then(message => {
                    this.all_uploadgroups = this.all_uploadgroups.filter(i => i.id != this.uploadgroupselected.id)
                    this.uploadgroupselected = null
                    this.showUploadForm = false
                })
                .catch(error => {
                    console.log(error)
                    this.$emit('addNotification', 'error', error.message)
                })
        },
        async editUploadGroup() {
            let params = {
                "display_name": this.uploadgroupselected.display_name,
                "description": this.uploadgroupselected.description,
                "paper_link": this.uploadgroupselected.paper_link
            }

            submitPost(
                `/task/${this.taskid}/vm/${this.userid}/save_software/upload/${this.uploadgroupselected.id}`,
                this.csrf,
                params
            ).then(message => {
                for (let uid in this.all_uploadgroups) {
                    if (this.all_uploadgroups[uid].id === this.uploadgroupselected.id) {
                        this.all_uploadgroups[uid].display_name = this.uploadgroupselected.display_name
                        this.all_uploadgroups[uid].description = this.uploadgroupselected.description
                        this.all_uploadgroups[uid].paper_link = this.uploadgroupselected.paper_link
                    }
                }

                this.editUploadMetadataToggle = false
            }).catch(error => {
                this.$emit('addNotification', 'error', `Editing failed with ${error}`)
            })
        },
        addUpload() {
            this.showUploadForm=true
            this.get(`/task/${this.taskid}/vm/${this.userid}/add_software/upload`).then(message => {
                const new_uploadgroup = {"uploadgroup":
                    {"display_name": message.context.upload.display_name}}
                this.$emit('addUploadgroup', new_uploadgroup)
                this.uploadgroupselected = message.context.upload
                this.all_uploadgroups.push(this.uploadgroupselected)
            })
            .catch(error => {
                this.$emit('addNotification', 'error', error.message)
            })
        },
        async fileUpload() {  // async
            console.log(this.uploading, this.uploadDataset, this.fileHandle)
            this.uploading = true
            let formData = new FormData();
            const headers = new Headers({'X-CSRFToken': this.csrf})
            formData.append("file", this.fileHandle);
            const response = await fetch(`/task/${this.taskid}/vm/${this.userid}/upload/${this.uploadDataset}/${this.uploadgroupselected.id}`, {
              method: "POST",
              headers,
              body: formData
            });

            let r = await response.json()
            if (!response.ok) {
                this.$emit('addNotification', 'error', `Uploading failed with status ${response.status}: ${await response.text()}`)
            } else if (r.status !== 0){
                this.uploadFormError = 'Error: ' + r.message
            } else {
                this.uploadFormError = ''
                console.log(r.new_run)

                //TODO: this is a fast hack as there are currently side effects with the run-list (duplicated runs that appear too late)
                window.location.reload()

                let new_run = r.new_run.run
                new_run.review.published = false

                this.uploadgroupselected.runs.push(new_run)

                for (let uid in this.all_uploadgroups) {
                    if (this.all_uploadgroups[uid].id === this.uploadgroupselected.id) {
                        this.all_uploadgroups[uid].runs.push(new_run)
                    }
                }

                this.fileHandle = null
                this.upload.last_edit = r.last_edit_date
                if (r.started_evaluation) {
                    this.$emit('pollEvaluations')
                }
            }
            this.$refs.file.value = null
            this.uploading = false
        },
        saveFileRef() {
            this.fileHandle = this.$refs.file.files[0];
        },
    },
    computed: {
        datasetOptions() {
            if (!this.datasets) {
                return []
            }
            return this.datasets.filter(k => !k.is_deprecated).map(k => {
                return [k.dataset_id, k.display_name]
            })
        },
        filterUploadRuns() {
            return this.upload.runs.filter(k => !k.is_evaluation).map(k => {
                return [k.display_name]
            })
        }
    },
    beforeMount() {
        this.all_uploadgroups = this.upload;
    }
}
</script>
