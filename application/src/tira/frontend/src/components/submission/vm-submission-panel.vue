<template>
<button class="uk-button uk-button-primary uk-button-small uk-margin-medium-right" @click="addSoftware()">
    Add Software <font-awesome-icon icon="fas fa-folder-plus" /></button>

<button v-for="sw in software"
        class="uk-button uk-button-default uk-button-small"
        @click="selectedSoftwareId=sw.software.id"
        :class="{ 'tira-button-selected': selectedSoftwareId === sw.software.id }">
          {{ sw.software.id }}</button>

<div v-if="selectedSoftware" class="uk-card uk-card-body uk-card-default uk-card-small">
    <form class="software_form">
        <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf }}">  <!-- TODO: this might not be needed anymore -->
        <div class="uk-grid-medium uk-margin-small" uk-grid>
            <div class="uk-width-1-6">
                <label class="uk-form-label"> Working Directory
                <input class="uk-input" type="text" @change="checkInputFields(true)"
                       v-model="selectedWorkingDir" :placeholder="workingDirPlaceholder">
                </label>
            </div>
            <div class="uk-width-1-2">
                <label class="uk-form-label">Command
                <input class="uk-input" type="text" @change="checkInputFields(true)"
                       :class="{ 'uk-form-danger': softwareCommanderError}"
                       v-model="selectedCommand" placeholder="ls $inputDataset >> $outputDir/test.txt"></label>
            </div>
            <div class="uk-width-expand">
                <div class="uk-form-controls">
                    <label class="uk-form-label">Input Dataset
                    <select class="uk-select upload-select" v-model="selectedDataset"
                            @change="checkInputFields(true)"
                            :class="{ 'uk-form-danger': softwareIdError}">
                        <option :disabled="selectedDataset !== 'None'" value="None">Select Dataset</option>
                        <option v-for="dataset in datasetOptions" :value="dataset.at(0)">{{ dataset.at(1) }}</option>
                    </select>
                    </label>
                </div>
            </div>
        </div>
    </form>
    <div class="uk-text-danger"><span v-html="softwareFormError"></span></div>
    <div class="software-form-buttons">
        <a class="uk-button uk-button-small uk-width-1-6"
           :class="{ 'uk-button-default': !checkInputFields(), 'uk-button-primary': checkInputFields() }"
                uk-tooltip="title: If the VM is 'running': Execute this software. Only one Software can be executed at a time. Software will be saved when executing a run.; delay: 500"
                @click="checkInputFields(true) && runSoftware()"
                :disabled="!checkInputFields()">
          run</a>
        <a class="uk-button uk-button-small uk-button-default"
           :class="{ 'flash-red': saveFailed, 'flash-green': saveSuccess }"
                @click="saveSoftware()">
            <font-awesome-icon icon="fas fa-save" />
        </a>
        <a class="uk-button uk-button-small uk-button-default"
            uk-tooltip="title: Click to show the help for Commands; delay: 500"
                uk-toggle="target: #modal-command-help"><font-awesome-icon icon="fas fa-info" /></a>

        <delete-confirm
            tooltip="Delete Software"
            :in-progress="false"
            :disable="!softwareCanBeDeleted()"
            @confirmation="() => deleteSoftware()"
        />
<!--        <a class="uk-button uk-button-small uk-button-danger software-delete-button"-->
<!--           @click="deleteSoftware()">-->
<!--          <font-awesome-icon icon="fas fa-trash-alt" /></a>-->
        <div class="uk-align-right">
            <span class="uk-text-small uk-text-lead">last edit: {{ selectedSoftware.last_edit }}</span>
        </div>
    </div>
</div>

<div v-if="selectedSoftware" class="uk-margin-small">
    <review-list
        v-if="selectedRuns"
        :runs="selectedRuns"
        :task_id="task.task_id"
        :user_id="user_id"
        display="participant"
        :csrf="csrf"
        :running_evaluations="running_evaluations"
        @add-notification="(type, message) => $emit('addNotification', type, message)"
        @remove-run="(runId) => $emit('removeRun', runId, 'vm')"
        @poll-evaluations="$emit('pollEvaluations')"/>
</div>

<div id="modal-command-help" class="uk-modal-container" uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-margin-auto-vertical">
        <button class="uk-modal-close-default" type="button" uk-close></button>
        <h2 class="uk-modal-title">Commands Help for {{ task.task_name }}</h2>
        <p>
        The <em>Command</em> will be executed on your Virtual Machine. By default, it will be run from your user's home directory.
            You can select a different location in the <em>Working Directory</em> input.
        </p>
        <table v-if="isDefaultCommand"
            class="uk-table uk-table-small uk-table-divider uk-align-center uk-margin-bottom">
            <thead>
                <tr><td colspan="2">You can use the following variables in your Commands:</td></tr>
                <tr><th>Variable</th><th>Description</th></tr>
            </thead>
            <tfoot>
            <tr><td class="uk-text-bold">$inputDataset</td><td>This will resolve to the full path to the directory that contains the <em>dataset you have selected</em>.</td></tr>
            <tr><td class="uk-text-bold">$outputDir</td><td>This will resolve to the full path to the directory where <em>your software must write it's output</em></td></tr>
            </tfoot>
        </table>
        <div v-if="!isDefaultCommand">{{ task.command_description }}</div>

        <div v-if="isDefaultCommandPlaceholder">
            <label class="uk-form-label">Example Command in TIRA</label>
            <pre><code>my-software/run.sh -i $inputDataset -o $outputDir</code></pre>
            <label class="uk-form-label">Example Command in the Virtual Machine</label>
            <pre><code>my-software/run.sh -i /media/training-datasets/{{ task.task_id }}/&lt;Input Dataset&gt; -o /tmp/{{ user_id }}/&lt;RUN&gt;/output</code></pre>
        </div>
        <div v-if="!isDefaultCommandPlaceholder">
            <label class="uk-form-label">Example Command in TIRA</label>
            <pre><code>{{ task.command_placeholder }}</code></pre>
        </div>
    </div>
</div>
</template>

<script>
import ReviewList from "../runs/review-list";
import DeleteConfirm from "../elements/delete-confirm";

export default {
    name: "vm-submission-panel",
    components: {
        ReviewList, DeleteConfirm
    },
    props: ['csrf', 'datasets', 'software', 'user_id', 'running_evaluations', 'task'],
    emits: ['addNotification', 'pollEvaluations', 'pollRunningSoftware', 'removeRun', 'addSoftware', 'deleteSoftware'],
    data() {
        return {
            runningEvaluationIds: [],
            selectedSoftwareId: null,
            selectedSoftware: null,
            selectedRuns: null,
            softwareFormError: "",
            softwareCommanderError: false,
            softwareIdError: false,
            selectedDataset: "None",
            selectedCommand: null,
            selectedWorkingDir: null,
            saveFailed: false,
            saveSuccess: false,
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
        addSoftware() {
            this.get(`/task/${this.task.task_id}/vm/${this.user_id}/add_software/vm`).then(message => {
                const new_software = {"software":
                    {"id": message.context.software.id,
                    "count": "",
                    "task_id": message.context.task,
                    "vm_id": message.context.vm_id,
                    "command": message.context.software.command,
                    "working_directory": message.context.software.working_directory,
                    "dataset": message.context.software.dataset,
                    "run": "none",
                    "creation_date": message.context.software.creation_date,
                    "last_edit": message.context.software.last_edit_date},
                    "runs": []}
                this.$emit('addSoftware', new_software)
                this.selectedSoftwareId = message.context.software.id
            }).catch(error => {
                this.$emit('addNotification', 'error', error.message)
            })
        },
        deleteSoftware() {
            // delete selected software
            this.get(`/task/${this.task.task_id}/vm/${this.user_id}/delete_software/vm/${this.selectedSoftwareId}`)
                .then(message => {
                    this.$emit('deleteSoftware', this.selectedSoftwareId)
                    if (this.software.length > 1) {
                        let listWithoutSoftware = this.software.filter(e => { return e.software.id !== this.selectedSoftwareId })
                        this.selectedSoftwareId = listWithoutSoftware[listWithoutSoftware.length-1].software.id
                        console.log("software id changed")
                        console.log(this.selectedSoftwareId)
                    } else {
                        this.selectedSoftwareId = null
                    }
                })
                .catch(error => {
                    this.$emit('addNotification', 'error', error.message)
                })
        },
        async saveSoftware(confirm=true) {
            if (!this.checkInputFields()) return false
            const id = this.selectedSoftwareId
            const command = this.selectedCommand
            const wd = this.selectedWorkingDir
            const ds = this.selectedDataset
            const sw = this.selectedSoftware

            const headers = new Headers({
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrf
            })
            const params = {
                command: command,
                working_dir: wd,
                input_dataset: ds,
                input_run: null,
                csrfmiddlewaretoken: this.csrf,
                action: 'post'
            }

            const response = await fetch(`/task/${this.task.task_id}/vm/${this.user_id}/save_software/vm/${id}`, {
                method: "POST",
                headers,
                body: JSON.stringify(params)
            })

            if (!response.ok) {
                this.addNotification('error', `Error fetching endpoint: ${url} with ${response.status}`)
                if (confirm) {
                    this.saveFailed = true
                }
            }
            let results = await response.json()
            if (results.status === 1) {
                this.addNotification('error', `Saving Software ${id} failed with ${response.status}`)
                if (confirm) {
                    this.saveFailed = true
                }
            }
            sw.command = command
            sw.working_dir = wd
            sw.dataset = ds

            if (confirm) {
                this.saveSuccess = true
            }
            const toggleSaveTimeout = setTimeout(this.toggleSaveTimeout, 3000)
            sw.last_edit = results.last_edit

            return results
        },
        toggleSaveTimeout(){
            console.log('toggle')
            this.saveSuccess = false
            this.saveFailed = false
        },
        async runSoftware () {
            // 0. save software
            if (!this.saveSoftware()) {
                return false
            }
            const response = await fetch(`/grpc/${this.task.task_id}/${this.user_id}/run_execute/vm/${this.selectedSoftwareId}`, {
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
                this.addNotification('error', `Running Software ${this.selectedSoftwareId} failed with ${response.status}`)
                return
            }
            this.$emit('pollRunningSoftware')
        },
        checkInputFields(mutate=false) {
            if (mutate) {
                this.softwareFormError = ""
                this.softwareCommanderError = false
                this.softwareIdError = false
            }

            if (this.selectedCommand === "") {
                if (mutate) {
                  this.softwareFormError += 'The command can not be empty<br>';
                  this.softwareCommanderError = true
                }
                return false
            }
            if (this.selectedDataset === "" || this.selectedDataset === "None" || this.selectedDataset === null){
                if (mutate) {
                    this.softwareFormError += 'The input dataset can not be empty<br>';
                    this.softwareIdError = true
                }
                return false
            }
            return true
        },
        softwareCanBeDeleted(){
            if (this.selectedRuns.length === 0) {
                return true
            }
            for (const run of this.selectedRuns) {
                if (run.review.published ) {
                    return false
                }
                if (run.is_evaluation && run.review.noErrors) {
                    return false
                }
            }
            return true
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
        isDefaultCommand() {
            return (this.task.command_description === 'Available variables: <code>$inputDataset</code>, <code>$inputRun</code>, <code>$outputDir</code>, <code>$dataServer</code>, and <code>$token</code>.')
        },
        isDefaultCommandPlaceholder() {
            return (this.task.command_placeholder === 'mySoftware -c $inputDataset -r $inputRun -o $outputDir')
        },
        workingDirPlaceholder() {
            return `/home/${this.user_id}/`
        },
        inputValid() {
            return (this.softwareIdError && this.softwareCommanderError)
        }
    },
    beforeMount() {
        if (this.software.length > 0) {
            this.selectedSoftwareId = this.software[0].software.id
        }
    },
    watch: {
        selectedSoftwareId(newSelectedSoftwareId, oldSelectedSoftwareId) {
            // this.saveSoftware(false)
            this.softwareFormError = ""
            this.softwareCommanderError = false
            this.softwareIdError = false

            // If we delete the last software
            if (newSelectedSoftwareId == null) {
                this.selectedSoftware = null
                this.selectedRuns = null
                this.selectedSoftware = null
                this.selectedCommand = null
                this.selectedWorkingDir = null
                return
            }

            for (let sw in this.software) {
                /* Fix Ember related problem where the Ember extends the native JS Array by '_super'.
                   Reference: https://github.com/emberjs/ember.js/issues/19289
                   The check may be removed once this issue is marked solved.
                */
                if (sw === '_super') { continue; }
                if (this.software[sw].software.id === newSelectedSoftwareId) {
                    this.selectedRuns = this.software[sw].runs
                    this.selectedSoftware = this.software[sw].software
                    this.selectedCommand = this.selectedSoftware.command
                    this.selectedWorkingDir = this.selectedSoftware.working_dir
                    if (!this.selectedSoftware.dataset) {
                        this.selectedDataset = "None"
                    } else {
                        this.selectedDataset = this.selectedSoftware.dataset
                    }
                }
            }
        }
    }
}
</script>
