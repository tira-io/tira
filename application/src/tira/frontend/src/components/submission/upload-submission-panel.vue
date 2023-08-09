<template>
<button class="uk-button uk-button-default uk-button-small" :class="{ 'uk-button-primary': !showUploadForm, 'tira-button-selected': showUploadForm}" @click="showUploadForm=false; uploadgroup=''; editUploadMetadataToggle=false;">
    Add New Upload Group <font-awesome-icon icon="fas fa-folder-plus" />
</button>
<button v-for="a in this.all_uploadgroups"
        class="uk-button uk-button-default uk-button-small uk-margin-small-horizontal"
        @click="uploadgroup=a ;showUploadForm=true; editUploadMetadataToggle=false;"
        :class="{ 'tira-button-selected': a==uploadgroup }">
         {{ a.display_name }} </button>

<div class="uk-card uk-card-body uk-card-default uk-card-small">

<form v-if="!showUploadForm" class="upload_form">
    <h2>Create Run Upload Group</h2>
    <p>Please click on "Add Upload Group" below to create a new run upload group.</p>
    <p>Please use one upload group (you can edit the metadata of an upload group later) per approach. I.e., in TIRA, you can usually run software submissions on different datasets. For manually uploaded runs, we employ the same methodology: Please create one run upload group per approach, so that you can upload "executions" of the same approach on different datasets while maintaining the documentation.</p>
    
    <br>
    
    <button class="uk-button uk-button-default uk-button-small uk-button-primary" @click="addUpload()">
        Add Upload Group <font-awesome-icon icon="fas fa-folder-plus" />
    </button>
</form>

<form v-if="showUploadForm && uploadgroup" class="upload_form">
    <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf }}">
    <div class="uk-width-1-1 uk-margin-remove" data-uk-grid>
        <div class="uk-width-expand"></div>
        <a  class="uk-button uk-text-small" @click="editUploadMetadataToggle = !editUploadMetadataToggle"
                       :class="{ 'uk-button-default': !editUploadMetadataToggle, 'uk-button-primary': editUploadMetadataToggle }"
                       uk-tooltip="title: Edit Description of the Run Upload Group;">Edit 
                        <font-awesome-icon icon="fas fa-cog" /></a>
        <delete-confirm
            tooltip="Attention! This deletes the upload group and and ALL RUNS"
            @confirmation="() => deleteUpload()" :disable="false"/>
    </div>
    
    <div v-if="editUploadMetadataToggle">
            <div class="uk-grid-medium uk-margin-remove-top" data-uk-grid>
                <div class="uk-width-1-1">
                    <label class="uk-form-label">Upload Group Name
                    <input class="uk-input" type="text" uk-tooltip="the name of your upload group"
                           v-model="uploadgroup.display_name" placeholder="name of your upload group">
                    </label>
                </div>
                <div class="uk-width-1-1">
                    <label class="uk-form-label">Upload Group Description
                    <textarea id="software-description" rows="3" class="uk-textarea"
                              v-model="uploadgroup.description" placeholder="description of your upload group"/>
                    </label>
                </div>
                <div class="uk-width-1-1">
                    <label class="uk-form-label">DOI of the Paper (Please use the DOI from <a href="https://www.doi.org/">www.doi.org</a>)
                    <input class="uk-input" type="text" uk-tooltip="the paper describing the upload group"
                           v-model="uploadgroup.paper_link" placeholder="paper describing the upload group">
                    </label>
                </div>
            </div>

            <div>
                  <label class="uk-form-label" for="edit-software-button">&nbsp;</label>
                  <div>
                      <a class="uk-button uk-button-primary" id="edit-software-button" @click="editUploadGroup()">Save Metadata</a>
                  </div>
            </div>
            <br>
            <br>
        </div>
        <div v-if="!editUploadMetadataToggle && uploadgroup">
            <p>{{uploadgroup.description}}</p>
        </div>
    
    <div class="uk-grid-medium" uk-grid>
        <div class="uk-width-1-2">
            <label class="uk-form-label" for="uploadresultsform">Upload Run</label>
            <div class="uk-form-controls uk-width-expand" uk-form-custom="target: true">
                <input type="file" @change="saveFileRef" ref="file">
                <input class="uk-input" id="uploadresultsform" type="text" placeholder="Click to select file" disabled>
            </div>
        </div>
        <div class="uk-width-1-3">
            <div class="uk-form-controls">
                <label class="uk-form-label">Input Dataset
                <select class="uk-select upload-select" v-model="uploadDataset">
                    <option :disabled="uploadDataset !== 'None'" value="None">Select Dataset</option>
                    <option v-for="dataset in datasetOptions" :value="dataset.at(0)">{{ dataset.at(1) }}</option>
                </select>
                </label>
            </div>
        </div>
        <div class="upload-form-buttons uk-width-expand">
            <label class="uk-form-label" for="upload-button">&nbsp;</label>
            <div>
                <a id="upload-button" class="uk-button uk-width-expand"
                   :class="{ 'uk-button-default': (uploading || fileHandle === null || uploadDataset === 'None'),
                   'uk-button-primary': !(uploading || fileHandle === null || uploadDataset === 'None')}"
                   :disabled="uploading || fileHandle === null || uploadDataset === 'None'"
                   @click="fileUpload()">
                  upload
                </a>
            </div>
        </div>
    </div>
    <div class="uk-grid-collapse uk-margin-remove" uk-grid>
        <div class="uk-text-danger uk-width-expand">{{ uploadFormError}}</div>
        <div>
            <span class="uk-text-small uk-text-lead" id="upload-last-edit">
                  <span v-show="uploading" uk-spinner="ratio: 0.3"></span> last edit: {{ uploadgroup.last_edit }}
        </span>
    </div>
    </div>
</form>
</div>
<div class="uk-margin-small">
    <review-list
        v-if="uploadgroup && uploadgroup.runs"
        :runs="uploadgroup.runs"
        :task_id="taskid"
        :user_id="userid"
        display="participant"
        :csrf="csrf"
        :running_evaluations="running_evaluations"
        @add-notification="(type, message) => $emit('addNotification', type, message)"
        @remove-run="(runId) => $emit('removeRun', runId, 'upload')"
        @poll-evaluations="() => $emit('pollEvaluations')"/>
</div>
</template>

<script>
import ReviewList from '../runs/review-list'
import DeleteConfirm from '../elements/delete-confirm'
import { get, submitPost } from "../../utils/getpost"

export default {
    name: "upload-submission-panel",
    components: {
        ReviewList, DeleteConfirm
    },
    props: ['csrf', 'datasets', 'upload', "taskid", "userid", "running_evaluations"],
    emits: ['addNotification', 'pollEvaluations', 'removeRun', 'addUploadgroup'],
    data() {
      return {
        showUploadForm: false,
        uploadDataset: '',
        uploadFormError: '',
        fileHandle: null,
        uploading: false,
        uploadgroup: null,
        editUploadMetadataToggle: false,
        all_uploadgroups: []
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
            this.get(`/task/${this.taskid}/vm/${this.userid}/upload-delete/${this.uploadgroup.id}`)
                .then(message => {
                    this.all_uploadgroups = this.all_uploadgroups.filter(i => i.id != this.uploadgroup.id)
                    this.uploadgroup = null
                    this.showUploadForm = false
                })
                .catch(error => {
                    console.log(error)
                    this.$emit('addNotification', 'error', error.message)
                })
        },
        async editUploadGroup() {
            let params = {
                "display_name": this.uploadgroup.display_name,
                "description": this.uploadgroup.description,
                "paper_link": this.uploadgroup.paper_link
            }

            submitPost(
                `/task/${this.taskid}/vm/${this.userid}/save_software/upload/${this.uploadgroup.id}`,
                this.csrf,
                params
            ).then(message => {
                for (let uid in this.all_uploadgroups) {
                    if (this.all_uploadgroups[uid].id === this.uploadgroup.id) {
                        this.all_uploadgroups[uid].display_name = this.uploadgroup.display_name
                        this.all_uploadgroups[uid].description = this.uploadgroup.description
                        this.all_uploadgroups[uid].paper_link = this.uploadgroup.paper_link
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
                this.uploadgroup = message.context.upload
                this.all_uploadgroups.push(this.uploadgroup)
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
            const response = await fetch(`/task/${this.taskid}/vm/${this.userid}/upload/${this.uploadDataset}/${this.uploadgroup.id}`, {
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
                
                this.uploadgroup.runs.push(new_run)
                
                for (let uid in this.all_uploadgroups) {
                    if (this.all_uploadgroups[uid].id === this.uploadgroup.id) {
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

<style scoped>

</style>
