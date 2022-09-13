<template>
<h2>Docker Submission</h2>
<div class="uk-width-1-1 uk-margin-small">
<button v-for="docker_software in docker"
        class="uk-button uk-button-default uk-button-small"
        @click="selectedContainerId=docker_software.docker_software_id; showNewImageForm=false; showUploadVm=false"
        :class="{ 'tira-button-selected': selectedContainerId === docker_software.docker_software_id }">
         Run {{ docker_software.docker_software_id  }}</button>
<button class="uk-button uk-button-default uk-button-small"
        :class="{ 'uk-button-primary': !showNewImageForm && docker.docker_images, 'tira-button-selected': showNewImageForm}"
        @click="showNewImageForm = !showNewImageForm; selectedContainerId = null; showUploadVm=false">
    Add Container <font-awesome-icon icon="fas fa-folder-plus" /></button>
<button class="uk-button uk-button-default uk-button-small"
        :class="{ 'uk-button-primary': !docker.docker_images && !showUploadVm, 'tira-button-selected': showUploadVm}"
        @click="showUploadVm = !showUploadVm; selectedContainerId = null; showNewImageForm=false">
    Upload Images <font-awesome-icon icon="fas fa-info" /></button>
</div>

<!-- shown for the initial creation-->
<div v-if="showNewImageForm" class="uk-width-1-1 uk-margin-small">
    <form id="docker-form" class="docker_form">
        <input type="hidden" name="csrfmiddlewaretoken" :value="csrf">  <!-- TODO: this might not be needed anymore -->
        <div class="uk-grid-medium" uk-grid>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Docker Image
                <select :disabled="!docker.docker_images" class="uk-select upload-select" v-model="containerImage" >
                    <option v-if="docker.docker_images" value="None" :disabled="containerImage !== 'None'">Select Docker Image</option>
                    <option v-else value="None" disabled>Upload an image first</option>
                    <option v-for="image in docker.docker_images" :value="image">{{ image }}</option>
                </select>
                </label>
            </div>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Command
                <input class="uk-input command-input" type="text"
                       :disabled="!docker.docker_images"
                       :value="containerCommand" placeholder="cat 'some data' >> tmp.txt"></label>
            </div>
            <div class="docker-form-buttons uk-width-expand">
                <label class="uk-form-label">&nbsp;
                <button class="uk-button uk-button uk-button-primary uk-width-expand" @click="addContainer()">add</button>
                </label>
                <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
            </div>
        </div>
    </form>
</div>
<div v-else-if="showUploadVm" class="uk-width-1-1 uk-margin-small">
    <p>Please <em>upload</em> your docker images according to your personalized documentation below. All <em>uploaded</em> docker images can be selected from the dropdown when <em>adding containers</em> <font-awesome-icon icon="fas fa-folder-plus" />.</p>

    <div class="uk-margin-small">
        {{ docker.docker_software_help }}
    </div>
</div>
<div v-else class="uk-width-1-1 uk-margin-small">
    <form id="docker-form" class="docker_form">
        <div class="uk-grid-medium" uk-grid>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Unused Image (immutable for reproducibility)
                <select class="uk-select" disabled>
                    <option value="None" selected>{{ selectedContainer.user_image_name }}</option>
                </select>
                </label>
            </div>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Resources for Execution
                    <select class="uk-select" v-model="selectedResources"
                            @change="checkContainerRunValid()"
                            :class="{ 'uk-form-danger': containerResourceError}">
                        <option :disabled="selectedResources !== 'None'" value="None">Select Resources</option>
                        <option v-for="resource in docker.resources" :value="resource.key">{{ resource.description }}</option>
                    </select>
                </label>
                <select class="uk-select">
                    <option value="None" selected>{{ selectedContainer.user_image_name }}</option>
                </select>
            </div>

            <div class="uk-width-1-3">
                <label class="uk-form-label">Command (immutable for reproducibility)
                <input class="uk-input" type="text"
                       :value="selectedContainerCommand" placeholder="Command" readonly disabled>
                </label>
            </div>

            <div class="uk-width-1-3">
                <label class="uk-form-label">Run on Dataset
                    <select class="uk-select" v-model="selectedDataset"
                            @change="checkContainerRunValid()"
                            :class="{ 'uk-form-danger': containerDatasetError}">
                        <option :disabled="selectedDataset !== 'None'" value="None">Select Dataset</option>
                        <option v-for="dataset in datasetOptions" :value="dataset.at(0)">{{ dataset.at(1) }}</option>
                    </select>
                </label>
            </div>
            <div class="uk-width-1-3">
                <label class="uk-form-label">&nbsp;<button class="uk-button uk-button uk-button-primary uk-width-expand"
                        @click="runContainer()">Run</button></label>
                <label class="uk-form-label">&nbsp;<button uk-tooltip="title: Attention! This deleted the Container and ALL RUNS; delay: 1" class="uk-button uk-button-small uk-button-danger"><font-awesome-icon icon="fas fa-folder-plus" /></button></label>
            </div>

            <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
        </div>
        <br><br>
        <div class="uk-grid-medium" uk-grid>
            <div class="uk-width-1-1">
                You can not change the image and the command in retrospect to ensure reproducibility. The original docker image is also used when you upload a new image with the same name and tag as TIRA snapshots the image. To add a new version of a docker image or use a different command, you should add multiple docker docker images. If this image contains errors that also make the runs created via the image invalid, you can delete the image below.
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
</template>

<script>
import SubmissionResultsPanel from "./submissionresultspanel";

export default {
    name: "dockersubmissionpanel",
    components: {
        SubmissionResultsPanel
    },
    props: ['csrf', 'datasets', 'docker', 'user_id', 'running_evaluations', 'task'],
    emits: ['addnotification', 'pollevaluations', 'removerun', 'addcontainer', 'deletecontainer', 'pollrunningcontainer'],
    data() {
        return {
            runningEvaluationIds: [],
            showNewImageForm: true,
            showUploadVm: false,
            selectedContainerId: null,
            selectedContainer: null,
            selectedRuns: null,
            containerImage: "None",
            containerCommand: "",
            dockerFormError: "",
            containerCommanderError: false,
            containerDatasetError: false,
            containerResourceError: false,
            selectedDataset: "None",
            selectedContainerCommand: null,
            selectedResources: null,
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
        checkContainerRunValid() {
            this.dockerFormError = ''
            this.containerDatasetError = false
            this.containerResourceError = false

            if (this.selectedDataset +''  === 'undefined' || this.selectedDataset  === 'None' || this.selectedDataset === '') {
                this.dockerFormError = 'Error: Please select a dataset!'
                this.containerDatasetError = true
                return false
            }
            if (this.selectedResources +''  === 'undefined' || this.selectedResources  === 'None' || this.selectedResources === '') {
                this.dockerFormError = 'Error: Please specify an the resources to execute!'
                this.containerResourceError = true
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
            if (!this.checkContainerRunValid()) return;

            const response = await fetch(`/grpc/${this.task.task_id}/${this.user_id}/run_execute/docker/${this.selectedDataset}/${this.selectedContainerId}/${this.selectedResources}`, {
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
            this.containerDatasetError = false
            this.containerResourceError = false
            this.dockerFormError = ""
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