<template>
<button class="uk-button uk-button-default uk-button-small" :class="{ 'uk-button-primary': !showNewImageForm, 'tira-button-selected': showNewImageForm}"
        @click="showNewImageForm = true; selectedContainerId = null; showUploadVm=false">
    Add Container <font-awesome-icon icon="fas fa-folder-plus" /></button>
<button class="uk-button uk-button-default uk-button-small uk-margin-medium-right"
        :class="{ 'uk-button-primary': !docker.docker_images && !showUploadVm, 'tira-button-selected': showUploadVm}"
        @click="showUploadVm = true; selectedContainerId = null; showNewImageForm=false">
        <font-awesome-icon class="uk-preserve-width" icon="fas fa-info" /> Upload Images</button>
<button v-for="docker_software in docker.docker_softwares"
        class="uk-button uk-button-default uk-button-small uk-margin-small-horizontal"
        @click="selectedContainerId=docker_software.docker_software_id; showNewImageForm=false; showUploadVm=false"
        :class="{ 'tira-button-selected': selectedContainerId === docker_software.docker_software_id }">
         {{ docker_software.display_name }}</button>

<!-- shown for the initial creation-->
<div v-if="showNewImageForm" class="uk-card uk-card-body uk-card-default uk-card-small">
    <form id="docker-form" class="docker_form">
        <input type="hidden" name="csrfmiddlewaretoken" :value="csrf">  <!-- TODO: this might not be needed anymore -->
        <div class="uk-grid uk-grid-small" data-uk-grid>
            <div class="uk-width-4-5">
                <label class="uk-form-label" for="docker-command-input">Command
                <input id="docker-command-input" class="uk-input command-input" type="text"
                       :disabled="!docker.docker_images"
                       v-model="addContainerCommand" :placeholder="task.command_placeholder">
                </label>
            </div>
            <div>
                <label class="uk-form-label uk-width-4-5">&nbsp;</label>
                <div>
                    <a class="uk-button uk-button-default"
                              uk-tooltip="title: Click to show the help for Commands; delay: 500"
                              uk-toggle="target: #modal-command-help"><font-awesome-icon icon="fas fa-info" /></a>
                </div>
            </div>

            <div class="uk-width-4-5">
                <label class="uk-form-label" for="selector_docker_image">Docker Image</label>
                <select id="selector_docker_image" :disabled="!docker.docker_images" class="uk-select upload-select" v-model="containerImage" >
                    <option v-if="docker.docker_images" value="None" :disabled="containerImage !== 'None'">Select Docker Image</option>
                    <option v-else value="None" disabled>Upload an image first</option>
                    <option v-for="image in docker.docker_images" :disabled="image.architecture !== 'amd64'" :value="image.image">{{ image.image }} (Architecture: {{image.architecture}}; Size: {{image.size}}; Created: {{image.created}}; Digest: {{image.digest}})</option>
                </select>
                
            </div>

            <div>
              <label class="uk-form-label" for="add-container-button">&nbsp;</label>
              <div><a class="uk-button" id="add-container-button"
                        @click="checkContainerValid(true) && addContainer()"
                        :disabled="!checkContainerValid(false)"
                        :class="{ 'uk-button-primary': checkContainerValid(false), 'uk-button-default': !checkContainerValid(false)}"
                >add container</a></div>
            </div>
            <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>

        </div>
    </form>
</div>
<div v-else-if="showUploadVm" class="uk-card uk-card-body uk-card-default uk-card-small">
    <p>Please <em>upload</em> your docker images according to your personalized documentation below. All <em>uploaded</em> docker images can be selected from the dropdown when <em>adding containers</em> <font-awesome-icon icon="fas fa-folder-plus" />.</p>

    <div class="uk-margin-small">
        <span v-html="docker.docker_software_help"></span>
    </div>
</div>
<div v-else class="uk-card uk-card-body uk-card-default uk-card-small uk-padding-remove-top">
    <form id="docker-form" class="docker_form">
        <div class="uk-width-1-1 uk-margin-remove" data-uk-grid>
            <div class="uk-width-expand"></div>
            <delete-confirm
                :tooltip="softwareCanBeDeleted() ? 'Attention! This deletes the container and ALL RUNS' : 'Software can not be deleted because there are still valid runs assigned.'"
                @confirmation="() => deleteContainer()"
                :disable="!softwareCanBeDeleted()" />
        </div>
        <div class="uk-grid-medium uk-margin-remove-top" data-uk-grid>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Software Name
                <input class="uk-input" type="text" uk-tooltip="the name of your software"
                       :value="selectedContainer.display_name" placeholder="name of your software">
                </label>
            </div>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Software Description
                <textarea id="software-description" rows="3" class="uk-textarea"
               :v-model="selectedContainer.description" placeholder="description of your software"/>
                </label>
            </div>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Paper
                <input class="uk-input" type="text" uk-tooltip="the paper describing"
                       :value="selectedContainer.paper_link" placeholder="paper describing the software">
                </label>
            </div>
        </div>

        <div>
              <label class="uk-form-label" for="edit-software-button">&nbsp;</label>
              <div><a class="uk-button uk-button-primary" id="edit-software-button"
                        @click="editSoftware()"
                >edit software</a></div>
        </div>
        <br>
        <br>

        <div class="uk-grid-medium uk-margin-remove-top" data-uk-grid>
            <div class="uk-width-1-1">
                <label class="uk-form-label">Command (immutable for reproducibility)
                <input class="uk-input" type="text" :uk-tooltip="immutableHelp"
                       :value="selectedContainerCommand" placeholder="Command" readonly disabled>
                </label>
            </div>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Used Image (immutable for reproducibility)
                <select class="uk-select" :uk-tooltip="immutableHelp" disabled>
                    <option value="None" selected>{{ selectedContainer.user_image_name }}</option>
                </select>
                </label>
            </div>
            <div class="uk-width-1-4">
                <label class="uk-form-label">Resources for Execution
                    <select class="uk-select" v-model="selectedResources"
                            @change="checkContainerRunValid(true)"
                            :class="{ 'uk-form-danger': containerResourceError}">
                        <option :disabled="selectedResources !== 'None'" value="None">Select Resources</option>
                        <option v-for="resource in docker.resources" :value="resource.key">{{ resource.description }}</option>
                    </select>
                </label>
            </div>
            <div class="uk-width-1-4">
                <label class="uk-form-label">Run on Dataset
                    <select class="uk-select" v-model="selectedDataset"
                            @change="checkContainerRunValid(true); this.dockerFormError=''"
                            :class="{ 'uk-form-danger': containerDatasetError}">
                        <option :disabled="selectedDataset !== 'None'" value="None">Select Dataset</option>
                        <option v-for="dataset in datasetOptions" :value="dataset.at(0)">{{ dataset.at(1) }}</option>
                    </select>
                </label>
            </div>
            <div>
                <label>&nbsp;
                <a class="uk-button uk-button-small uk-button-default uk-margin-small"
                        :class="{ 'uk-button-primary': checkContainerRunValid(), 'uk-button-disabled': !checkContainerRunValid()}"
                        @click="checkContainerRunValid(true) && runContainer()"
                        ref="runContainerButton">
                    Run Container</a></label>
            </div>
            <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
        </div>
    </form>
</div>
<div id="modal-command-help" class="uk-modal-container" uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-margin-auto-vertical">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <h2 class="uk-modal-title">Docker Commands Help for {{ task.task_name }}</h2>
        <p v-html="task.command_description"></p>
    </div>
</div>
<div class="uk-grid-small" uk-grid>
    <div class="uk-width-1-2">&nbsp;</div>
    <div class="uk-width-1-6">&nbsp;</div>
    <div class="uk-width-1-6 uk-text-light">Last Refresh: {{ docker.docker_images_last_refresh.slice(11,19) }}&nbsp;</div>
    <div class="uk-width-1-6 uk-text-light"><a @click="update_docker_images_cache()">Refresh Images</a></div>
</div>
<div v-if="!showNewImageForm && ! showUploadVm" class="uk-margin-small">
    <review-list
        v-if="selectedRuns"
        :runs="selectedRuns"
        :task_id="task.task_id"
        :user_id="user_id"
        :csrf="csrf"
        display="participant"
        :running_evaluations="running_evaluations"
        @addNotification="(type, message) => $emit('addNotification', type, message)"
        @removeRun="(runId) => $emit('removeRun', runId, 'docker')"
        @pollEvaluations="() => $emit('pollEvaluations')"/>
</div>
</template>

<script>
import ReviewList from "../runs/review-list";
import DeleteConfirm from "../elements/delete-confirm";

export default {
    name: "docker-submission-panel",
    components: {
        ReviewList, DeleteConfirm
    },
    props: ['csrf', 'datasets', 'docker', 'user_id', 'running_evaluations', 'task'],
    emits: ['addNotification', 'pollEvaluations', 'removeRun', 'addContainer', 'deleteContainer', 'pollRunningContainer', 'refreshDockerImages'],
    data() {
        return {
            runningEvaluationIds: [],
            showNewImageForm: true,
            showUploadVm: false,
            selectedContainerId: null,
            selectedContainer: null,
            selectedRuns: null,
            containerImage: "None",
            addContainerCommand: "",
            dockerFormError: "",
            containerCommanderError: false,
            containerDatasetError: false,
            containerResourceError: false,
            containerImageError: false,
            selectedDataset: "None",
            selectedContainerCommand: null,
            selectedResources: "None",
            toggleCommandHelp: false,
            startingContainer: false,
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
        async addContainer() {
            this.checkContainerValid()

            let formData = new FormData();
            const headers = new Headers({'X-CSRFToken': this.csrf})
            formData.append("command", this.addContainerCommand);
            formData.append("image", this.containerImage);
            const response = await fetch(`/task/${this.task.task_id}/vm/${this.user_id}/add_software/docker`, {
              method: "POST",
              headers,
              body: formData
            });

            let r = await response.json()
            console.log(response)
            console.log(r)
            if (!response.ok) {
                this.$emit('addNotification', 'error', `Uploading failed with ${response.status}: ${await response.text()}`)
            } else if (r.status === 1){
                this.dockerFormError = 'Error: ' + r.message
            } else {
                this.dockerFormError = ''
                this.$emit('addContainer', r)
            }
        },
        checkContainerValid(updateView=false) {
            this.containerImageError = false
            this.containerCommanderError = false
            if (this.containerImage  === 'None') {
                if (updateView) {
                    this.dockerFormError = 'Error: Please specify an docker image!'
                    this.containerImageError = true
                }
                return false
            }
            if (this.addContainerCommand === 'undefined' || this.addContainerCommand  === 'None' || this.addContainerCommand === '') {
                if (updateView) {
                    this.dockerFormError = 'Error: Please specify a docker command!'
                    this.containerCommanderError = true
                }
                return false
            }
            return true
        },
        checkContainerRunValid(updateView=false) {
            this.containerDatasetError = false
            this.containerResourceError = false

            if (this.selectedDataset +''  === 'undefined' || this.selectedDataset  === 'None' || this.selectedDataset === '') {
                if (updateView) {
                    this.dockerFormError = 'Error: Please select a dataset!'
                    this.containerDatasetError = true
                }
                return false
            }
            if (this.selectedResources +''  === 'undefined' || this.selectedResources  === 'None' || this.selectedResources === '') {
                if (updateView) {
                    this.dockerFormError = 'Error: Please specify an the resources to execute!'
                    this.containerResourceError = true
                }
                return false
            }
            if (this.startingContainer === true) {
                return false
            }
            return true
        },
        deleteContainer() {
            this.get(`/task/${this.task.task_id}/vm/${this.user_id}/delete_software/docker/${this.selectedContainerId}`)
                .then(message => {
                    this.$emit('deleteContainer', this.selectedContainerId)
                    this.showNewImageForm = true
                })
                .catch(error => {
                    this.$emit('addNotification', 'error', error.message)
                })
        },
        async runContainer () {
            if (!this.checkContainerRunValid(true)) return;
            this.startingContainer = true
            this.$refs['runContainerButton'].text = "Starting..."

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
                this.$emit('addNotification', 'error', `Error fetching endpoint: ${url} with ${response.status}`)
            }
            let results = await response.json()
            if (results.status === 1) {
                this.$emit('addNotification', 'error', `Running Container ${this.selectedContainerId} failed with ${response.status}. Message = ${response.message}`)
                return
            }
            this.$emit('pollRunningContainer')
            this.$refs['runContainerButton'].text = "Run Container"
            this.startingContainer = false
        },
        softwareCanBeDeleted(){
            for (const run of this.selectedContainer.runs) {
                if (run.review.published ) {
                    return false
                }
                if (run.is_evaluation && run.review.noErrors) {
                    return false
                }
            }
            return true
        },
        update_docker_images_cache() {
            let force_cache_refresh = "True"
            this.$emit('refreshDockerImages', force_cache_refresh)
        }
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
        immutableHelp() {
            return "title: You can not change the image and the command in retrospect to ensure reproducibility. " +
                "The frozen image will not be changed even if you update the image in the registry. " +
                "To update the image the command add another image. " +
                "You can delete erroneous images and their runs below.; delay: 100"
        }
    },
    beforeMount() {
        if (this.docker.resources.length > 0){
            this.selectedResources = this.docker.resources[0].key
        }
    },
    watch: {
        selectedContainerId(newSelectedContainerId, oldSelectedContainerId) {
            this.containerDatasetError = false
            this.containerResourceError = false
            this.containerCommanderError = false
            this.containerImageError = false
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
                    this.selectedContainerCommand = this.docker.docker_softwares[did].command
                    this.containerImage = this.docker.docker_softwares[did].user_image_name
                    this.selectedDataset = "None"
                }
            }
        }
    }
}
</script>
