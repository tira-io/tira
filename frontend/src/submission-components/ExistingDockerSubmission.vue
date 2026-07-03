<template>
  <loading :loading="loading"/>
  <v-container v-if="!loading">
    <v-card class="px-5">
      <div :class="$vuetify.display.mdAndUp ? 'w-100 d-flex justify-end mt-4' : 'w-100 d-flex justify-space-evenly mt-4'">
          <edit-submission-details
              type='docker'
              :id="docker_software_id"
              :user_id="user_id"
              :is_ir_task="is_ir_task"
              @edit="updateDockerSoftwareDetails"
          />
          <v-btn class="ml-4" variant="outlined" color="red" @click="deleteDockerImage()">
            <v-tooltip
                activator="parent"
                location="bottom"
            >Attention! This deletes the container and ALL runs associated with it
            </v-tooltip>
            <v-icon>mdi-delete-alert-outline</v-icon>
            Delete
          </v-btn>
      </div>

      <v-card-subtitle class="my-4">{{ docker_software_details.description }}</v-card-subtitle>
      <v-form id="docker-submission-readonly-input">
        <v-text-field label="Previous Stages (Immutable for Reproducibility)" v-if="docker_software_details.previous_stages" v-model="docker_software_details.previous_stages" readonly/>

        <div v-if="docker_software_details.mount_hf_model_display && docker_software_details.mount_hf_model_display[0].href != 'loading...'">
        This software mounts the Hugging Face models 
        <span v-for="hf_model in docker_software_details.mount_hf_model_display">
          <a :href="hf_model.href" target="_blank">{{hf_model.display_name}}</a>&nbsp;
        </span>
        into the Docker image.
        </div>

        <div v-if="docker_software_details.source_code_active_branch && docker_software_details.source_code_commit && docker_software_details.source_code_remotes">
        This software was created from the git repository 
        <span v-for="link in docker_software_details.source_code_remotes">
          <a v-if="link.href" :href="link.href" target="_blank">{{link.name}}</a><span v-if="!link.href">{{link.name}}</span>&nbsp;
        </span>
        <br>(Branch: {{ docker_software_details.source_code_active_branch }}. Commit: {{ docker_software_details.source_code_commit }}).<br>
        </div>
        <v-text-field label="Docker Image (Immutable for Reproducibility)" v-model="docker_software_details.user_image_name" readonly/>
        <v-text-field label="Command (Immutable for Reproducibility)" v-model="docker_software_details.command" v-if="workflow_fields.length == 0" readonly/>
        <v-text-field :label="w.label" v-model="w.command" readonly v-for="w in workflow_fields"/>
      </v-form>

      <v-divider></v-divider>
      
      <v-card-title>Run the Software</v-card-title>
      <v-form ref="form" v-model="valid">
        <v-autocomplete v-model="selectedResource" :items="allResources" label="Resources" item-title="display_name" item-value="resource_id" :rules="[v => !!(v && v.length) || 'Please select the resources for the execution.']" />
        <v-autocomplete v-model="selectedDataset" v-if="!docker_software_details.ir_re_ranker" :items="datasets" item-title="display_name" item-value="dataset_id" label="Dataset" :rules="[v => !!(v && v.length) || 'Please select on which dataset the software should run.']" />
        <v-autocomplete v-model="selectedRerankingDataset" v-if="docker_software_details.ir_re_ranker" :items="re_ranking_datasets" item-title="display_name" item-value="dataset_id" label="Re-ranking Dataset" :rules="[v => !!(v && v.length) || 'Please select which system your software should re-rank.']" />
        <div v-if="forward_environment_variable_fields.length > 0" class="text-subtitle-1 mt-4 mb-2">
          Environment variables
        </div>
        <v-text-field
          v-for="field in forward_environment_variable_fields"
          :key="field.name"
          v-model="forward_environment_variable_values[field.name]"
          :label="field.label"
          :rules="[v => !!(v && v.length) || `${field.name} is required.`]"
        />
        <div v-if="mount_config_fields.length > 0" class="text-subtitle-1 mt-4 mb-2">
          Additional mounted directories
        </div>
        <div
          v-for="field in mount_config_fields"
          :key="`mount-config-${field.name}`"
          class="mb-4"
        >
          <v-card variant="outlined" class="pa-3">
            <div class="text-subtitle-2 mb-2">{{ field.label }}</div>
            <v-radio-group
              v-model="mount_config_values[field.name]"
              density="compact"
              hide-details="auto"
              :rules="[
                v => !!v || `${field.name} is required.`
              ]"
            >
              <v-radio
                label="Mount a new empty directory"
                :value="mount_config_options.emptyDirectory"
              />
              <v-radio
                label="Mount the output of some other execution"
                :value="mount_config_options.previousExecution"
              />
              <v-radio
                label="Upload directory"
                :value="mount_config_options.uploadDirectory"
              />
            </v-radio-group>
            <v-file-input
              v-if="mount_config_values[field.name] === mount_config_options.uploadDirectory"
              v-model="mount_config_uploads[field.name]"
              accept=".zip,application/zip"
              label="Zip archive for uploaded directory"
              prepend-icon="mdi-folder-zip"
              show-size
              class="mt-3"
              :rules="[v => validateMountConfigUpload(field.name, v)]"
            />
            <v-text-field
              v-if="mount_config_values[field.name] === mount_config_options.previousExecution"
              v-model="mount_config_previous_execution_run_ids[field.name]"
              label="Run ID to mount"
              class="mt-3"
              :rules="[v => validateMountConfigPreviousExecutionRunId(field.name, v)]"
            />
          </v-card>
        </div>
        
        <v-btn class="mb-1" block color="primary" variant="outlined" :loading="runSoftwareInProgress" @click="runSoftware()" text="Run"/>
      </v-form>
    </v-card>

  </v-container>

  <h2>Submissions</h2>
  <run-list :task_id="task_id" :organizer="organizer" :organizer_id="organizer_id" :vm_id="user_id" :docker_software_id="docker_software_id" from_archive="false"/>
</template>

<script lang="ts">
import { inject } from 'vue'

import {Loading, RunList} from "../components"
import { get, post_file, reportError, reportSuccess, inject_response, extractTaskFromCurrentUrl, type UserInfo } from '../utils'
import {VAutocomplete} from 'vuetify/components'
import EditSubmissionDetails from "@/submission-components/EditSubmissionDetails.vue";

export default {
  name: "existing-docker-submission",
  components: {Loading, RunList, VAutocomplete, EditSubmissionDetails},
  emits: ['refresh_running_submissions', 'deleteDockerImage', 'modifiedSubmissionDetails'],
  props: ['user_id', 'datasets', 're_ranking_datasets', 'resources', 'docker_software_id', 'organizer', 'organizer_id', 'is_ir_task'],
  data: () => ({
      loading: true, runSoftwareInProgress: false, selectedDataset: '', valid: false, selectedResource: '',
      docker_software_details: {
        'display_name': 'loading ...', 'user_image_name': 'loading', 'command': 'loading',
        'description': 'loading ...', 'previous_stages': 'loading ...', 'paper_link': 'loading ...', 'ir_re_ranker': false, 'mount_hf_model_display': [{'href': 'loading...', 'display_name': 'loading...', }],
        'source_code_active_branch': undefined, 'source_code_commit': undefined, 'source_code_remotes': [{'href': 'loading...', 'name': 'loading...'}],
        'workflow_configuration': {} as { [key: string]: string },
        'forward_environment_variable': [] as string[],
        'mount_config': {} as Record<string, string>
      },
      forward_environment_variable_values: {} as Record<string, string>,
      mount_config_values: {} as Record<string, string>,
      mount_config_uploads: {} as Record<string, File | File[] | null>,
      mount_config_previous_execution_run_ids: {} as Record<string, string>,
      mount_config_options: {
        emptyDirectory: 'EMPTY_DIR',
        previousExecution: 'OUTPUT_OF_OTHER_EXECUTION',
        uploadDirectory: 'UPLOAD_DIRECTORY'
      },
      task_id: extractTaskFromCurrentUrl(), selectedRerankingDataset: '',
      rest_url: inject("REST base URL"),
      userinfo: inject('userinfo') as UserInfo,
  }),
  methods: {
    deleteDockerImage() {
      this.$emit('deleteDockerImage');
    },
    async runSoftware() {
      const { valid } = await (this.$refs.form as any).validate()

      if (valid) {
        this.runSoftwareInProgress = true
        var reranking_dataset = 'none'

        if (this.docker_software_details.ir_re_ranker) {
          reranking_dataset = this.selectedRerankingDataset
                
          for (const r of this.re_ranking_datasets) {
            if (reranking_dataset == r.dataset_id) {
              this.selectedDataset = r.original_dataset_id
            }
          }
        }

        const params = new FormData()

        if (this.forward_environment_variable_fields.length > 0) {
          params.append('forward_environment_variable', JSON.stringify(this.forward_environment_variable_payload))
        }

        if (this.mount_config_fields.length > 0) {
          params.append('mount_config', JSON.stringify(this.mount_config_payload))

          for (const field of this.mount_config_fields) {
            if (this.mount_config_values[field.name] !== this.mount_config_options.uploadDirectory) {
              continue
            }

            const upload = this.selectedMountConfigUpload(field.name)

            if (upload) {
              params.append(this.mountConfigUploadFieldName(field.name), upload, upload.name)
            }
          }
        }

        post_file(this.rest_url + `/grpc/${this.task_id}/${this.user_id}/run_execute/docker/${this.selectedDataset}/${this.docker_software_id}/${this.selectedResource}/${reranking_dataset}`, params, this.userinfo)
        .then(reportSuccess("Software was scheduled in the cluster. It might take a few minutes until the execution starts.", "Started run on: " + this.selectedDataset + " dataset with " + this.selectedResource))
        .catch(reportError("Problem starting the software.", "This might be a short-term hiccup, please try again. We got the following error: "))
        .then(() => {this.$emit('refresh_running_submissions'); this.runSoftwareInProgress = false; })
      }
    },
    showEditModal() {
      (this.$refs.editModal as any).show();
    },
    updateDockerSoftwareDetails(editedDetails: any) {
      this.docker_software_details.display_name = editedDetails.display_name
      this.docker_software_details.description = editedDetails.description
      this.docker_software_details.paper_link = editedDetails.paper_link
      this.$emit('modifiedSubmissionDetails', editedDetails)
    },
    initializeForwardEnvironmentVariableValues() {
      let values: Record<string, string> = {}

      for (const field of this.forward_environment_variable_fields) {
        const existingValue = this.forward_environment_variable_values[field.name]
        values[field.name] = existingValue !== undefined ? existingValue : ''
      }

      this.forward_environment_variable_values = values
    },
    initializeMountConfigValues() {
      let values: Record<string, string> = {}

      for (const field of this.mount_config_fields) {
        const existingValue = this.mount_config_values[field.name]
        values[field.name] = existingValue !== undefined ? existingValue : this.mount_config_options.emptyDirectory
      }

      this.mount_config_values = values
    },
    initializeMountConfigUploads() {
      let uploads: Record<string, File | File[] | null> = {}

      for (const field of this.mount_config_fields) {
        const existingValue = this.mount_config_uploads[field.name]
        uploads[field.name] = existingValue !== undefined ? existingValue : null
      }

      this.mount_config_uploads = uploads
    },
    initializeMountConfigPreviousExecutionRunIds() {
      let runIds: Record<string, string> = {}

      for (const field of this.mount_config_fields) {
        const existingValue = this.mount_config_previous_execution_run_ids[field.name]
        runIds[field.name] = existingValue !== undefined ? existingValue : ''
      }

      this.mount_config_previous_execution_run_ids = runIds
    },
    selectedMountConfigUpload(fieldName: string) {
      const upload = this.mount_config_uploads[fieldName]

      if (Array.isArray(upload)) {
        return upload[0] ?? null
      }

      return upload ?? null
    },
    mountConfigUploadFieldName(fieldName: string) {
      return `mount_config_upload_${encodeURIComponent(fieldName)}`
    },
    validateMountConfigUpload(fieldName: string, value: File | File[] | null) {
      if (this.mount_config_values[fieldName] !== this.mount_config_options.uploadDirectory) {
        return true
      }

      const upload = Array.isArray(value) ? (value[0] ?? null) : value

      if (!upload) {
        return 'Please upload a zip archive.'
      }

      return upload.name.toLowerCase().endsWith('.zip') ? true : 'Please select a .zip file.'
    },
    validateMountConfigPreviousExecutionRunId(fieldName: string, value: string) {
      if (this.mount_config_values[fieldName] !== this.mount_config_options.previousExecution) {
        return true
      }

      return value && value.trim().length > 0 ? true : 'Please provide a run ID.'
    }
  },
  computed: {
    allResources() {
      let ret = []

      for (var k of Object.keys(this.resources)) {
        ret.push({"resource_id": k, "display_name": this.resources[k]['description']})
      }
      
      return ret
    },
    workflow_fields() {
      let ret: { label: string; command: string }[] = []

      if (!this.docker_software_details.workflow_configuration) {
        return ret
      }

      for (let k of Object.keys(this.docker_software_details.workflow_configuration)) {
        if (k != "workflow_configuration") {
          ret.push({"label": k + " (Immutable for Reproducibility)", "command": "" + this.docker_software_details.workflow_configuration[k]})
        }
      }

      return ret
    },
    forward_environment_variable_fields() {
      let ret: { name: string; label: string }[] = []
      const envVars = this.docker_software_details.forward_environment_variable

      if (!Array.isArray(envVars) || envVars.length === 0) {
        return ret
      }

      for (const envVar of envVars) {
        ret.push({"name": envVar, "label": envVar})
      }

      return ret
    },
    mount_config_fields() {
      let ret: { name: string; label: string }[] = []
      const mountConfig = this.docker_software_details.mount_config

      if (!mountConfig || Array.isArray(mountConfig) || Object.keys(mountConfig).length === 0) {
        return ret
      }

      for (const mountName of Object.keys(mountConfig)) {
        ret.push({"name": mountName, "label": mountName})
      }

      return ret
    },
    forward_environment_variable_payload() {
      let ret: Record<string, string> = {}

      for (const field of this.forward_environment_variable_fields) {
        ret[field.name] = this.forward_environment_variable_values[field.name]
      }

      return ret
    },
    mount_config_payload() {
      let ret: Record<string, string | { source: string, run_id: string }> = {}

      for (const field of this.mount_config_fields) {
        const selectedMountSource = this.mount_config_values[field.name]

        if (selectedMountSource === this.mount_config_options.previousExecution) {
          ret[field.name] = {
            source: selectedMountSource,
            run_id: this.mount_config_previous_execution_run_ids[field.name].trim()
          }
          continue
        }

        ret[field.name] = selectedMountSource
      }

      return ret
    }
  },
  beforeMount() {
    this.loading = true
    get(inject("REST base URL")+'/api/docker-softwares-details/' + this.user_id + '/' + this.docker_software_id)
        .then((message) => {
          inject_response(this, {'loading': false})(message)
          this.initializeForwardEnvironmentVariableValues()
          this.initializeMountConfigValues()
          this.initializeMountConfigUploads()
          this.initializeMountConfigPreviousExecutionRunIds()
        })
        .catch(reportError("Problem While Loading the details of the software", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  watch: {
    details(old_value, new_value) {
    }
  }
}
</script>
