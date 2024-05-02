<template>
    <v-dialog width="85%" height="85%" scrollable>
      <template v-slot:activator="{ props }">
        <v-btn :disabled="disabled" class="d-sm-none" color="primary" icon="mdi-plus" v-if="newDataset()" v-bind="props" @click="clicked()"/>
        <v-btn :disabled="disabled" class="d-none d-sm-flex" color="primary" prepend-icon="mdi-plus" v-if="newDataset()" size="large" v-bind="props" @click="clicked()">New Dataset</v-btn>
    
        <v-btn :disabled="disabled" class="d-none d-sm-flex" color="primary" v-if="!newDataset()" prepend-icon="mdi-cog" size="large" v-bind="props" @click="clicked()">Edit Dataset</v-btn>
        <v-btn :disabled="disabled" class="d-sm-none" color="primary" icon="mdi-cog" v-if="!newDataset()" v-bind="props" @click="clicked()"/>
      </template>
      <template v-slot:default="{ isActive }">
        <v-card class="pb-1">
          <loading :loading="loading" />
          <card-title>
            <v-toolbar color="primary" :title="title"/>
          </card-title>
        
          <v-card-text>
            <v-form v-if="!loading" ref="form" v-model="valid">
                <p>
                  By default, datasets in TIRA remain private, so that only organizers of a shared task can see the datasets and outputs of submissions. We recommend to have one tiny training dataset (e.g., 10 instances) publicly available so that participants can test their submissions easily.
                  <br><br>
                </p>
                <v-text-field v-if="!newDataset()" v-model="dataset_id" :disabled="!newDataset()" label="Dataset ID" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>
                <v-text-field v-model="display_name" label="Dataset Name" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>

                <v-text-field v-model="default_upload_name" label="Default Upload Name" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>

                <v-radio-group v-if="newDataset()" v-model="dataset_type">
                  <v-radio label="This is a training dataset (participants see their outputs/evaluations)" value="training"></v-radio>
  <v-radio label="This is a test dataset (participants see only explicitly unblinded outputs/evaluations)" value="test"></v-radio>
                </v-radio-group>
                <p v-if="!newDataset() && dataset_id_from_props.endsWith('-training')">
                  This is a training dataset, i.e., users see results/outputs of their submission.
                  <br><br>
                </p>

                <p v-if="!newDataset() && dataset_id_from_props.endsWith('-test')">
                  This is a test dataset.  
                  By default, users see no results/outputs.
                  Organizers have to manually unblind the submissions or evaluations so that users see the evaluations and/or results/outputs.
                  <br><br>
                </p>


                <v-divider/>
                <h2 class="my-1">Public Access to the Data and Submissions</h2>
                <p>
                  You can make the data public so that users can download the data and submissions, e.g., after the shared task is finished or for participants to verify their software.
                </p>

                <v-radio-group v-model="is_confidential">
                  <v-radio label="This dataset is public (users can access the data and published submissions)" value="false"></v-radio>
                  <v-radio label="This dataset is confidential (only organizers can access the data and submissions)" value="true"></v-radio>
                </v-radio-group>

                <v-divider/>
                <h2 class="my-1">Provide the Actual Data</h2>
                <v-radio-group v-if="newDataset()" v-model="upload_type">
                  <v-radio label="I want to provide the data later" value="upload-1"></v-radio>
                  <v-radio label="I want to manually upload the data now" value="upload-2"></v-radio>
                  <v-radio label="I want to use the ir_datasets integration" value="upload-3"></v-radio>
                </v-radio-group>

                <v-file-input v-model="systemFileHandle" v-if="(newDataset() && upload_type === 'upload-2') || !newDataset()" label="Input Data for Systems (.zip file)"></v-file-input>
                <v-file-input  v-model="truthFileHandle" v-if="(newDataset() && upload_type === 'upload-2') || !newDataset()" label="Ground Truth for Evaluation (.zip file)"></v-file-input>

                <v-text-field v-if="irds_image !== '' || upload_type === 'upload-3'" v-model="irds_image" label="Docker Image of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                <v-text-field v-if="irds_image !== '' || upload_type === 'upload-3'" v-model="irds_command" label="Command of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>

                <p v-if="!newDataset()">
                  ToDo: Short description how access data via CephFS.
                  <br><br>
                </p>

                <v-divider/>
                <h2 class="my-1">Evaluation</h2>
                <p v-if="newDataset()">Please specify how you want to evaluate submissions. An evaluator has a submissions and the ground truth as input to produce an evaluation. We have prepared evaluators covering common evaluation scenarious.
                </p>

                <v-radio-group v-if="newDataset()" v-model="evaluation_type">
                  <v-radio label="I want to configure the evaluation later" value="eval-1"/>
                  <v-radio value="eval-2">
                    <template v-slot:label>
                      Evaluate with Huggingface Metrics&nbsp;(<a href="https://github.com/tira-io/hf-evaluator" target="_blank">documentation</a>).
                    </template>
                  </v-radio>
                  <v-radio value="eval-3">
                    <template v-slot:label>
                      Evaluate with ir_measures&nbsp;(<a href="https://github.com/tira-io/ir-experiment-platform/tree/main/ir-measures" target="_blank">documentation</a>).
                    </template>
                  </v-radio>
                  <v-radio value="eval-4">
                    <template v-slot:label>
                      Evaluate with a custom evaluator&nbsp;(<a href="https://github.com/tira-io/ir-experiment-platform/tree/main/ir-measures" target="_blank">documentation</a>).
                    </template>
                  </v-radio>
                </v-radio-group>
                <v-text-field v-model="git_runner_image" v-if="evaluation_type !== 'eval-1'" label="Docker Image of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                <v-text-field  v-model="git_runner_command" v-if="evaluation_type !== 'eval-1'" label="Command of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>
              </v-form>
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-row>
            <v-col cols="6"><v-btn variant="outlined" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6" v-if="!loading"><v-btn variant="outlined" :loading="submitInProgress" @click="submit(isActive)" block>Submit</v-btn></v-col>
          </v-row>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
    </template>
        
    <script lang="ts">
    import { Loading } from '.'
    import {VAutocomplete} from "vuetify/components";
    import { get, post, post_file, reportError, slugify, reportSuccess, inject_response } from '../utils'
    
    export default {
      name: "edit-dataset",
      components: {Loading, VAutocomplete},
      emits: ['add-dataset'],
      props: {task_id: {}, dataset_id_from_props: {type: String, default: ''}, disabled: {type: Boolean, default: false}, is_ir_task: {type: Boolean, default: false}},
      data: () => ({
        loading: true, valid: false, submitInProgress: false, dataset_id: '',
        display_name: '', is_confidential: 'true', dataset_type: 'test', upload_type: 'upload-1',
        irds_image: '', irds_command: '',is_deprecated: false, default_upload_name: "predictions.jsonl",
        irds_docker_image: "", irds_import_command: "", irds_import_truth_command: "",
        git_runner_image: "ubuntu:18.04", git_runner_command: "echo 'this is no real evaluator'", evaluation_type: "eval-1",
        systemFileHandle: undefined, truthFileHandle: undefined,
        git_repository_id: ''
      }),
      computed: {
        title() {
          return this.newDataset() ? 'Add New Dataset' : 'Edit Dataset ' + this.dataset_id_from_props;
        }
      },
      methods: {
        clicked: function() {
          this.loading = true
          this.default_upload_name = this.is_ir_task ? "run.txt" : "predictions.jsonl"

          if (this.newDataset()) {
            this.loading = false
          } else {
            get(`/api/dataset/${this.dataset_id_from_props}`)
              .then(inject_response(this, {'loading': false}, true, ['dataset', 'evaluator']))
              .catch(reportError("Problem loading the dataset.", "This might be a short-term hiccup, please try again. We got the following error: "))
              .then(() => {this.is_confidential = '' + this.is_confidential; this.evaluation_type = 'eval-3'})
          }
        },
        newDataset: function() {
          return !this.disabled && this.dataset_id_from_props === '';
        },
        isValid: async function() {
          const form = this.$refs.form as any
          if (!form) {
            return false
          }
    
          return await form.validate()
        },
        fileUpload(fileHandle: any, dataset_type: string) {
          const task_id = this.task_id
          return function(message: any) {
            const dataset_id = message['context']['dataset_id']

            if (dataset_id === undefined || '' + dataset_id === 'undefined' || fileHandle === undefined || '' + fileHandle === 'undefined' || fileHandle[0] == undefined || '' + fileHandle[0] === 'undefined') {
              return message
            }

            let formData = new FormData()
            formData.append("file", fileHandle[0]);
            return post_file(`/tira-admin/upload-dataset/${task_id}/${dataset_id}/${dataset_type}`, formData)
            .then(reportSuccess("Uploaded File"))
            .then(() => {return message})
          }
        },
        submit: async function(isActive: any) {
          const {valid} = await this.isValid()

          if (!valid) {
            return
          }
        
          this.submitInProgress = true
          this.dataset_id = this.newDataset() ? slugify(this.display_name) : this.dataset_id_from_props
          
          let params: any = {
              'dataset_id': this.dataset_id, 'name': this.display_name, 'task': this.task_id,
              'type': this.dataset_type,'upload_name': this.default_upload_name, 
              'is_confidential': this.is_confidential !== 'false',
              'irds_docker_image': this.irds_docker_image, 'irds_import_command': this.irds_import_command, 'irds_import_truth_command': this.irds_import_truth_command, 
              'git_runner_image': this.git_runner_image,'git_runner_command': this.git_runner_command, 'is_git_runner': true, 'use_existing_repository': false,
              'working_directory': 'obsolete', 'command': 'obsolete', 'publish': this.is_confidential === 'false', 'evaluator_command': 'obsolete', 'evaluator_image': 'obsolete', 'evaluator_working_directory': 'obsolete',
          }

          if (!this.newDataset()) {
            params['git_repository_id'] = this.git_repository_id
          }

          const url = this.newDataset() ? '/tira-admin/add-dataset/' + this.task_id : '/tira-admin/edit-dataset/' + this.dataset_id_from_props
          post(url, params)
          .then(this.fileUpload(this.systemFileHandle, 'input'))
          .then(this.fileUpload(this.truthFileHandle, 'truth'))
          .then(newDataset => {
            if(this.newDataset()) {
              this.$emit('add-dataset', {'dataset_id': newDataset['context']['dataset_id'], 'display_name': newDataset['context']['display_name']})
            }
            isActive.value = false
            this.submitInProgress = false
            this.display_name = ''
            
          })
          .then(reportSuccess("Creation of dataset was successfull."))
          .catch(reportError("Problem While Adding the Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: "))
        },
      },
    }
    </script>
