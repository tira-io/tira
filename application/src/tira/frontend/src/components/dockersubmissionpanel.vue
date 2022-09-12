<template>
<h2>Docker Submission</h2>

<div class="uk-width-1-1 uk-margin-small">
<button v-for="docker_software in docker"
        class="uk-button uk-button-default uk-button-small"
        @click="selectedContainerId=docker_software.docker_software_id"
        :class="{ 'tira-button-selected': selectedContainerId === docker_software.docker_software_id }">
          {{ docker_software.docker_software_id  }}</button>
<button class="uk-button uk-button-primary uk-button-small"
        :class="{ 'uk-button-primary': !showNewImageForm, 'tira-button-selected': showNewImageForm}"
        @toggle="showNewImageForm">
    Add Image <font-awesome-icon icon="fas fa-folder-plus" /></button>
</div>

<!-- shown for the initial creation-->
<div v-if="showNewImageForm" class="uk-width-1-1 uk-margin-small">
    <form id="docker-form" class="docker_form">
        Please upload your docker images
        <a uk-tooltip="title: Click to show the help for adding docker softwares; delay: 500" uk-toggle="target: #modal-docker-software-help">
        according to your personalized documentation</a>.
        All docker images that you have uploaded appear in the selectbox below so that you can add them to TIRA to run the image on datasets.
        We add a detailed documentation on how to upload docker images soon.<br><br>

        <input type="hidden" name="csrfmiddlewaretoken" :value="csrf">  <!-- TODO: this might not be needed anymore -->
        <div class="uk-grid-medium" uk-grid>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Docker Image
                <select class="uk-select upload-select" v-model="containerImage" >
                    <option :value="None" selected>Select Docker Image</option>
                    <option v-for="image in docker.docker_images" :value="image">{{ image }}</option>
                </select>
                </label>
            </div>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Command
                <input class="uk-input command-input" type="text"
                       :value="containerCommand" placeholder="cat 'some data' >> tmp.txt"></label>
            </div>
            <div class="docker-form-buttons uk-width-expand">
                <label class="uk-form-label">&nbsp;
                <button class="uk-button uk-button uk-button-primary uk-width-expand" @click="saveContainer()">add</button>
                </label>
                <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
            </div>
        </div>
    </form>
</div>
<div v-else class="uk-width-1-1 uk-margin-small">
<form id="docker-form" class="docker_form">
      <div class="uk-grid-medium" uk-grid>
          <div class="uk-width-4-4">
              <label class="uk-form-label">Unused Image (immutable for reproducibility)
              <select class="uk-select upload-select" disabled>
                  <option :value="None" selected>{{ docker_software.user_image_name }}</option>
              </select>
              </label>
          </div>
          <div class="uk-width-1-3">
              <label class="uk-form-label">Command (immutable for reproducibility)
              <input class="uk-input command-input" id="existing-command" type="text"
                     :value="docker_software.command" placeholder="Command" readonly disabled>
              </label>
          </div>
          <div class="uk-width-1-3">
              <label class="uk-form-label">Run on Dataset
                  <select class="uk-select upload-select" v-model="selectedDataset"
                          @change="checkInputFields()"
                          :class="{ 'uk-form-danger': containerDatasetError}">
                      <option :disabled="selectedDataset !== 'None'" value="None">Select Dataset</option>
                      <option v-for="dataset in datasetOptions" :value="dataset.at(0)">{{ dataset.at(1) }}</option>
                  </select>
              </label>
          </div>

          <div class="docker-form-buttons uk-width-expand">
              <label class="uk-form-label">&nbsp;</label>
              <div>
                  <button class="uk-button uk-button uk-button-primary uk-width-expand docker-run-button"
                          :data-tira-run-docker-software-id="docker_software.docker_software_id">Run</button>
              </div>
              <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
          </div>
      </div>
      <br><br>
      <div class="uk-grid-medium" uk-grid>
          <div class="uk-width-1-1">
              You can not change the image and the command in retrospect to ensure reproducibility. The original docker image is also used when you upload a new image with the same name and tag as TIRA snapshots the image. To add a new version of a docker image or use a different command, you should add multiple docker docker images. If this image contains errors that also make the runs created via the image invalid, you can delete the image below.
          </div>
      </div>

<!--  docker_software.runs  -->

      <br><br>
      <div class="uk-grid-medium" uk-grid>
          <div class="uk-width-3-5"></div>
          <div class="docker-form-buttons uk-width-expand">
              Delete Docker Software and all runs <b>(Attention)</b>:  <button class="uk-button uk-button-small uk-button-danger docker-delete-button"
                      :data-tira-docker-software-id="docker_software.docker_software_id"><i class="fas fa-trash-alt"></i></button>
          </div>
      </div>
</form>
</div>

<div class="uk-margin-small">
    <submission-results-panel
        v-if="selectedRuns"
        :runs="selectedRuns"
        :task_id="task.task_id"
        :user_id="user_id"
        :running_evaluations="running_evaluations"
        @addNotification="(type, message) => addNotification(type, message)"
        @removeRun="(runId) => removeRun(runId)"
        @pollEvaluations="pollEvaluations()"
    />
</div>

<!-- The modal that shows the Command Help -->
<div id="modal-docker-software-help" class="uk-modal-container" uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-margin-auto-vertical">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <h1 class="uk-modal-title">How to Upload Docker Images</h1>
        {{ docker.docker_software_help }}
    </div>
</div>
</template>

<script>
import SubmissionResultsPanel from "./submissionresultspanel";

export default {
    name: "dockersubmissionpanel",
    components: {
        SubmissionResultsPanel
    },
    props: ['csrf', 'datasets', 'docker', 'user_id', 'running_evaluations', 'task'],
    emits: ['addnotification', 'pollevaluations', 'removerun', 'addcontainer', 'deletecontainer'],
    data() {
        return {
            runningEvaluationIds: [],
            showNewImageForm: true,
            selectedContainerId: null,
            selectedContainer: null,
            selectedRuns: null,
            containerImage: null,
            containerCommand: "",
            dockerFormError: "",
            containerCommanderError: false,
            containerDatasetError: false,
            selectedDataset: "None",
            selectedContainerCommand: null,
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
        addNotification(type, message) {
            this.$emit('addnotification', type, message)
        },
        pollEvaluations() {
            this.$emit('pollevaluations')
        },
        removeRun(runId) {
            this.$emit('removerun', runId, 'upload')
        },
        async addContainer() {
            this.checkContainerValid()

            let formData = new FormData();
            const headers = new Headers({'X-CSRFToken': this.csrf})
            formData.append("command", this.containerCommand);
            formData.append("image", image);
            const response = await fetch(`/task/${this.task.task_id}/vm/${this.user_id}/add_software/docker`, {
              method: "POST",
              headers,
              body: formData
            });

            let r = await response.json()
            console.log(response)
            console.log(r)
            if (!response.ok) {
                this.addNotification('error', `SUploading failed with ${response.status}: ${await response.text()}`)
            } else if (r.status === 0){
                this.dockerFormError = 'Error: ' + r.message
            } else {
                this.dockerFormError = ''
                this.$emit('addcontainer', r)
                // location.reload();
            }
        },
        checkContainerValid() {
            this.dockerFormError = ''
            if (this.containerImage  === 'None') {
                this.dockerFormError = 'Error: Please specify an docker image!'
                return false
            }
            if (this.containerCommand === 'undefined' || this.containerCommand  === 'None' || this.containerCommand === '') {
                this.dockerFormError = 'Error: Please specify a docker command!'
                return false
            }
            return true
        },
        deleteContainer() {
            this.get(`/task/${this.task.task_id}/vm/${this.user_id}/delete_software/docker/${this.selectedContainerId}`)
                .then(message => {
                    this.$emit('deletecontainer', this.selectedContainerId)
                    this.showNewImageForm = true
                })
                .catch(error => {
                    this.$emit('addnotification', 'error', error.message)
                })
        },
        async runContainer () {
            if (this.selectedDataset +''  === 'undefined' || this.selectedDataset  === 'None' || this.selectedDataset === '') {
                this.dockerFormError = 'You must select a Dataset.'
                return;
            }
            this.dockerFormError = ''

            const response = await fetch(`/grpc/${this.task.task_id}/${this.user_id}/run_execute/docker/${this.selectedDataset}/${this.selectedContainerId}`, {
                method: "POST",
                headers: new Headers({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrf
                }),
                body: JSON.stringify({
                    csrfmiddlewaretoken: this.csrf,
                    action: 'post'
                })
            })
            if (!response.ok) {
                this.addNotification('error', `Error fetching endpoint: ${url} with ${response.status}`)
            }
            let results = await response.json()
            if (results.status === 1) {
                this.addNotification('error', `Running Container ${this.selectedContainerId} failed with ${response.status}`)
                return
            }
            this.$emit('pollRunningContainer')
        },
    },
    computed: {
    },
    beforeMount() {
    },
    watch: {
        selectedContainerId(newSelectedContainerId, oldSelectedContainerId) {
            // If we delete the last image
            if (newSelectedContainerId == null) {
                this.showNewImageForm = true
                return
            }

            for (let did in this.docker.docker_softwares) {
                if (this.docker.docker_softwares[did].docker_software_id === newSelectedContainerId) {
                    this.selectedRuns = this.docker.docker_softwares[did].runs
                    this.selectedContainer = this.docker.docker_softwares[did]
                    this.containerCommand = this.docker.docker_softwares[did].command
                    this.containerImage = this.docker.docker_softwares[did].user_image_name
                    this.selectedDataset = "None"
                }
            }
        }
    }
}
</script>