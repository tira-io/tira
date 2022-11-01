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
            <div class="uk-width-1-1">
                <label class="uk-form-label">Command
                <input class="uk-input command-input" type="text"
                       :disabled="!docker.docker_images"
                       v-model="addContainerCommand" :placeholder="task.command_placeholder"></label>
            </div>
            <div class="uk-width-1-1">
                <a @click="toggleCommandHelp = !toggleCommandHelp" :command_description="task.command_description"><u>Toggle Command Help</u></a><br>
                <span v-show="toggleCommandHelp">{{ task.command_description }}</span>
            </div>
            <div class="uk-width-1-2">
                <label class="uk-form-label" for="selector_docker_image">Docker Image</label>
                <select id="selector_docker_image" :disabled="!docker.docker_images" class="uk-select upload-select" v-model="containerImage" >
                    <option v-if="docker.docker_images" value="None" :disabled="containerImage !== 'None'">Select Docker Image</option>
                    <option v-else value="None" disabled>Upload an image first</option>
                    <option v-for="image in docker.docker_images" :value="image">{{ image }}</option>
                </select>
                
            </div>
            <div class="uk-width-1-2">
              <label class="uk-form-label" for="add_container_button">&nbsp;</label>
              <div><a class="uk-button" id="add_container_button" 
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
<div v-else class="uk-card uk-card-body uk-card-default uk-card-small">
    <form id="docker-form" class="docker_form">
        <div class="uk-grid-medium" uk-grid>
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

                <label>&nbsp;
                <a uk-tooltip="title: Attention! This deletes the container and ALL RUNS; delay: 1"
                        class="uk-button uk-button-small uk-button-danger uk-margin-small"
                        @click="deleteContainer()">
                    <font-awesome-icon icon="fas fa-trash-alt" /></a></label>
            </div>
            <div class="uk-text-danger uk-width-expand">{{ dockerFormError }}</div>
        </div>
    </form>
</div>

<div v-if="!showNewImageForm && ! showUploadVm" class="uk-margin-small">
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
                this.addNotification('error', `Uploading failed with ${response.status}: ${await response.text()}`)
            } else if (r.status === 1){
                this.dockerFormError = 'Error: ' + r.message
            } else {
                this.dockerFormError = ''
                this.$emit('addcontainer', r)
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
                    this.$emit('deletecontainer', this.selectedContainerId)
                    this.showNewImageForm = true
                })
                .catch(error => {
                    this.$emit('addnotification', 'error', error.message)
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
                this.addNotification('error', `Error fetching endpoint: ${url} with ${response.status}`)
            }
            let results = await response.json()
            if (results.status === 1) {
                this.addNotification('error', `Running Container ${this.selectedContainerId} failed with ${response.status}. Message = ${response.message}`)
                return
            }
            this.$emit('pollrunningcontainer')
            this.$refs['runContainerButton'].text = "Run Container"
            this.startingContainer = false
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
