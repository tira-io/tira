<template>
<div class="uk-card uk-card-body uk-card-default uk-card-small">
<form class="upload_form">
    <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf }}">
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
                  <span v-show="uploading" uk-spinner="ratio: 0.3"></span> last edit: {{ upload.last_edit }}
        </span>
    </div>
    </div>
</form>
</div>
<div class="uk-margin-small">
    <review-list
        v-if="upload.runs"
        :runs="upload.runs"
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

export default {
    name: "upload-submission-panel",
    components: {
        ReviewList
    },
    props: ['csrf', 'datasets', 'upload', "taskid", "userid", "running_evaluations"],
    emits: ['addNotification', 'pollEvaluations', 'removeRun'],
    data() {
      return {
        uploadDataset: '',
        uploadFormError: '',
        fileHandle: null,
        uploading: false
      }
    },
    methods: {
        async fileUpload() {  // async
            console.log(this.uploading, this.uploadDataset, this.fileHandle)
            // TODO: when successful, add new entry to uploads.runs
            this.uploading = true
            let formData = new FormData();
            const headers = new Headers({'X-CSRFToken': this.csrf})
            formData.append("file", this.fileHandle);
            const response = await fetch(`/task/${this.taskid}/vm/${this.userid}/upload/${this.uploadDataset}`, {
              method: "POST",
              headers,
              body: formData
            });

            let r = await response.json()
            if (!response.ok) {
                this.$emit('addNotification', 'error', `Uploading failed with status ${response.status}: ${await response.text()}`)
            } else if (r.status === 1){
                this.uploadFormError = 'Error: ' + r.message
            } else {
                this.uploadFormError = ''
                console.log(r.new_run)
                this.upload.runs.push(r.new_run.run)
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
        }
    },
    beforeMount() {
        if (this.upload.dataset) {
            this.uploadDataset = this.upload.dataset
        } else {
            this.uploadDataset = "None"
        }
    }
}
</script>

<style scoped>

</style>
