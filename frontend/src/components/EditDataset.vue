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

            <v-row>
              <v-col cols="12"><v-alert v-if="error_message" title="Creating/Editing the Dataset failed. Maybe a short hiccup?" type="error" closable :text="error_message"/></v-col>
            </v-row>
          </card-title>
        
          <v-card-text>
            <v-form v-if="!loading" ref="form" v-model="valid">
                <p>
                  By default, datasets in TIRA remain private, so that only organizers of a shared task can see the datasets and outputs of submissions. We recommend to have one tiny training dataset (e.g., 10 instances) publicly available so that participants can test their submissions easily.
                  <br><br>
                </p>
                <v-text-field v-if="!newDataset()" v-model="dataset_id" :disabled="!newDataset()" label="Dataset ID" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>
                <v-text-field v-model="display_name" label="Dataset Name" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>

                <v-textarea v-model="description" label="Dataset Description" :rules="[v => v && v.length > 2 || 'Please provide a description of the dataset.']" required/>

                <v-text-field v-model="default_upload_name" label="Default Upload Name" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>

                <v-select v-model="format" :items="serverinfo.supportedFormats" label="Dataset Format" clearable multiple/>
                <v-select v-model="truth_format" :items="serverinfo.supportedFormats" label="Truth Format" clearable multiple/>

                <div>
                  Consider to integrate the data into <a href="https://ir-datasets.com/" target="_blank">ir-datasets</a> and <a href="https://www.chatnoir.eu/" target="_blank">ChatNoir</a> for simplified access and improved visibility.
                </div>
                <v-row>
                  <v-col cols="6">
                    <v-text-field v-model="ir_datasets_id" label="IR-Datasets ID (Optional)"/>
                  </v-col>
                  <v-col cols="6">
                    <v-text-field v-model="chatnoir_id" label="Chatnoir ID (Optional)"/>
                  </v-col>
                </v-row>

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
                <div v-if="file_listing">
                  <h2 class="my-1">Overview of the Actual Data</h2>
                  <directory-inspector :file_listing="file_listing"/>
                </div>
                <div v-if="!file_listing">
                  <h2 class="my-1">Provide the Actual Data</h2>
                  <v-radio-group v-if="newDataset()" v-model="upload_type">
                    <v-radio label="Import from Zenodo (recommended)" value="upload-0"></v-radio>
                    <v-radio label="I want to provide the data later" value="upload-1"></v-radio>
                    <v-radio label="I want to manually upload the data now" value="upload-2"></v-radio>
                    <v-radio label="I want to use the ir_datasets integration" value="upload-3"></v-radio>
                  </v-radio-group>

                  <div v-if="newDataset() && upload_type === 'upload-0'">
                    <v-row>
                      <v-col cols="6">
                        <v-text-field v-model="systemUrlHandle" label="Zenodo Download URL of Inputs for Systems" :rules="[v => v && v.length > 2 || 'Please provide a URL.']"/>
                        </v-col>
                        <v-col cols="6">
                          <v-text-field v-if="!is_zip(systemUrlHandle)" v-model="systemFileRename" label="Rename input for systems for unified access (optional)"/>
                          <div v-if="is_zip(systemUrlHandle)">
                          The URL for the system inputs looks like a .zip file. In case a subdirectory of the zip contains the data, please specify it next (Leave empty otherwise).
                          <v-text-field  v-model="systemUrlDirectory" label="Subdirectory in Zip (optional)"/>
                        </div>
                      </v-col>
                    </v-row>

                    <v-row>
                      <v-col cols="6">
                        <v-text-field v-model="truthUrlHandle" label="Zenodo Download URL for Ground Truth Data."/>
                      </v-col>
                      <v-col cols="6">
                        <v-text-field v-if="!is_zip(truthUrlHandle)" v-model="truthFileRename" label="Rename truth file for unified access (optional)"/>
                        <div v-if="is_zip(truthUrlHandle)">
                          The ground truth data URL looks like a .zip file. In case a subdirectory of the zip contains the data, please specify it next (Leave empty otherwise).
                          <v-text-field v-model="truthUrlDirectory" label="Subdirectory in Zip (optional)"/>
                        </div>
                      </v-col>
                    </v-row>
                  </div>

                  <v-file-input v-model="systemFileHandle" v-if="(newDataset() && upload_type === 'upload-2') || !newDataset()" label="Input Data for Systems (.zip file)"></v-file-input>
                  <v-file-input  v-model="truthFileHandle" v-if="(newDataset() && upload_type === 'upload-2') || !newDataset()" label="Ground Truth for Evaluation (.zip file)"></v-file-input>

                  <v-text-field v-if="irds_image !== '' || upload_type === 'upload-3'" v-model="irds_image" label="Docker Image of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                  <v-text-field v-if="irds_image !== '' || upload_type === 'upload-3'" v-model="irds_command" label="Command of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>

                  <p v-if="!newDataset()">
                    ToDo: Short description how access data via CephFS.
                    <br><br>
                  </p>
                </div>
                <v-divider/>
                <h2 class="my-1">Evaluation (<a href="https://docs.tira.io/organizers/organizing-tasks.html#add-an-evaluator" target="_blank">Documentation</a>)</h2>
                <p>Please specify how you want to evaluate submissions. An evaluator has a submissions and the ground truth as input to produce an evaluation. We have prepared evaluators covering common evaluation scenarious. Evaluators are either trusted evaluators that are implemented in the TIRA python client that can run outside the sandbox (i.e., fast) or custom docker images that are executed in the sandbox.
                </p>


                <v-radio-group v-model="sandboxed">
                  <v-radio label="I want to configure the evaluator later" value="later"/>
                  <v-radio label="I want to use existing trusted evaluators (runs without sandbox)" value="false"/>
                  <v-radio label="I want to use my own custom Evaluator that runs in the sandbox" value="true"/>
                </v-radio-group>

                <v-radio-group v-model="evaluation_type">

                  <span v-if="(sandboxed + '').toLowerCase() == 'false'">
                    <h2>Configure the Evaluation with the <a href="https://github.com/tira-io/tira/blob/main/python-client/tira/evaluators.py" target="_blank">TIRA python client</a></h2>
                    <v-radio label="Use retrieval measures" value="eval-5"/>
                    <v-radio label="Use classification measures" value="eval-6"/>
                  </span>

                  <span v-if="(sandboxed + '').toLowerCase() == 'true'">
                    <h2>Configure the Evaluation with a custom Docker Evaluator</h2>
                    <v-radio v-if="newDataset()" value="eval-2">
                      <template v-slot:label>
                        Evaluate with dockerized Huggingface Metrics&nbsp;(<a href="https://github.com/tira-io/hf-evaluator" target="_blank">documentation</a>).
                      </template>
                    </v-radio>
                    <v-radio v-if="newDataset()" value="eval-3">
                      <template v-slot:label>
                        Evaluate with dockerized ir_measures&nbsp;(<a href="https://github.com/tira-io/ir-experiment-platform/tree/main/ir-measures" target="_blank">documentation</a>).
                      </template>
                    </v-radio>
                    <v-radio v-if="newDataset()" value="eval-4">
                      <template v-slot:label>
                        Evaluate with a custom dockerized evaluator&nbsp;(<a href="https://github.com/tira-io/ir-experiment-platform/tree/main/ir-measures" target="_blank">documentation</a>).
                      </template>
                    </v-radio>
                  </span>
                </v-radio-group>

                <v-text-field v-model="git_runner_image" v-if="use_dockerized_evaluator" label="Docker Image of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                <v-text-field  v-model="git_runner_command" v-if="use_dockerized_evaluator" label="Command of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>

                <v-autocomplete v-model="trusted_measures" v-if="evaluation_type === 'eval-5' && !use_dockerized_evaluator" clearable chips label="Retrieval Measures" :items="serverinfo.trustedEvaluators.Retrieval" multiple :rules="[v => v && v.length >= 1 || 'Please provide at least one retrieval measure.']" required></v-autocomplete>

                <span v-if="evaluation_type === 'eval-6'">
                  The evaluator loads the run and the truth data. From both, it extracts one field as an ID to join the run with the truth data and then compares a label field in the run with a label field in the truth data to calculate the provided measure(s) with the <a href="https://huggingface.co/docs/evaluate/index" target="_blank">HuggingFace evaluate method</a>.

                  <v-autocomplete v-model="trusted_measures" clearable chips label="Classification Measures" :items="serverinfo.trustedEvaluators.Classification" multiple :rules="[v => v && v.length >= 1 || 'Please provide at least one classification measure.']" required></v-autocomplete>

                  <v-text-field v-model="truth_id_column" label="ID field in the Truth data" :rules="[v => v && v.length >= 1 || 'Please provide the name of the ID.']" required/>
                  <v-text-field v-model="truth_label_column" label="Label field in the Truth data" :rules="[v => v && v.length >= 1 || 'Please provide the name of the ID.']" required/>

                  <v-text-field v-model="run_id_column" label="ID field in the runs" :rules="[v => v && v.length >= 1 || 'Please provide the name of the ID.']" required/>
                  <v-text-field v-model="run_label_column" label="Label field in the runs" :rules="[v => v && v.length >= 1 || 'Please provide the name of the ID.']" required/>
                  <v-text-field v-model="additional_args" label="Custom arguments in JSON format for the Huggingface Evaluator (e.g.: {&quot;average&quot;: &quot;micro&quot;})"/>
                </span>
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
    import { inject } from 'vue'

    import { Loading, DirectoryInspector } from '.'
    import {VAutocomplete} from "vuetify/components";
    import { get, post, post_file, reportError, slugify, reportSuccess, inject_response, type UserInfo, type ServerInfo } from '../utils'
    
    export default {
      name: "edit-dataset",
      components: {Loading, VAutocomplete, DirectoryInspector},
      emits: ['add-dataset'],
      props: {task_id: {}, dataset_id_from_props: {type: String, default: ''}, disabled: {type: Boolean, default: false}, is_ir_task: {type: Boolean, default: false}},
      data: () => ({
        loading: true, valid: false, submitInProgress: false, dataset_id: '',
        display_name: '', description: '', is_confidential: 'true', dataset_type: 'test', upload_type: 'upload-0',
        irds_image: '', irds_command: '', format: undefined, truth_format: undefined, is_deprecated: false, default_upload_name: "predictions.jsonl",
        irds_docker_image: "", irds_import_command: "", irds_import_truth_command: "",
        systemUrlHandle: "", systemUrlDirectory: "", truthUrlHandle: "", truthUrlDirectory: "", systemFileRename: "inputs.jsonl", truthFileRename: "labels.jsonl", error_message: "", chatnoir_id: "", ir_datasets_id: "",
        git_runner_image: "ubuntu:18.04", git_runner_command: "echo 'this is no real evaluator'", evaluation_type: "eval-1",
        systemFileHandle: undefined, truthFileHandle: undefined,
        git_repository_id: '', rest_endpoint: inject("REST base URL") as string, file_listing: '',
        userinfo: inject('userinfo') as UserInfo, serverinfo: inject("serverInfo") as ServerInfo,
        trusted_measures: undefined, sandboxed: "later",
        run_id_column:"id", run_label_column:"label", truth_id_column:"id", truth_label_column:"id", additional_args: undefined,
      }),
      computed: {
        title() {
          return this.newDataset() ? 'Add New Dataset' : 'Edit Dataset ' + this.dataset_id_from_props;
        },
        use_dockerized_evaluator() {
          return (this.sandboxed + '').toLowerCase() == 'true' && this.evaluation_type !== 'eval-1' && this.evaluation_type !== 'eval-5' && this.evaluation_type !== 'eval-6';
        }
      },
      watch: {
        sandboxed(new_value, old_value) {
          if (!old_value) {
            return
          }
          if (new_value != old_value && new_value == 'true') {
            this.evaluation_type = "eval-4"
            this.git_runner_image = "ubuntu:18.04"
            this.git_runner_command = "echo 'this is no real evaluator'"
          } else if (new_value != old_value && new_value == 'false') {
            this.evaluation_type = "eval-5"
            this.trusted_measures = undefined
            this.git_runner_image = "ubuntu:18.04"
            this.git_runner_command = "echo 'this is no real evaluator'"
          } else if (new_value != old_value && new_value == 'later') {
            this.evaluation_type = "eval-1"
            this.trusted_measures = undefined
            this.git_runner_image = "ubuntu:18.04"
            this.git_runner_command = "echo 'this is no real evaluator'"
          }
        },
        evaluation_type(new_value, old_value) {
          if (new_value != old_value && (new_value == 'eval-5' || new_value == 'eval-6') && (old_value == 'eval-5' || old_value == 'eval-6')) {
            this.trusted_measures = undefined
          }

          if (this.dataset_id_from_props) {
            return
          }
          if (new_value != old_value && new_value == 'eval-1') {
            this.git_runner_image = "ubuntu:18.04"
            this.git_runner_command = "echo 'this is no real evaluator'"
          }
          else if (new_value != old_value && new_value == 'eval-2') {
            this.git_runner_image = "fschlatt/tira-hf-evaulator:0.0.5"
            this.git_runner_command = "python3 /evaluation.py --metrics precision recall f1 --predictions $inputRun/predictions.jsonl --references $inputDataset/labels.jsonl"
          }
          else if (new_value != old_value && new_value == 'eval-3') {
            this.git_runner_image = "webis/ir_measures_evaluator:1.0.5"
            this.git_runner_command = '/ir_measures_evaluator.py --run ${inputRun}/run.txt --topics ${inputDataset}/queries.jsonl --qrels ${inputDataset}/qrels.txt --output_path ${outputDir} --measures "P@10" "nDCG@10" "MRR"'
          } else if (new_value != old_value && (new_value == 'eval-5' || new_value == 'eval-6')) {
            this.trusted_measures = undefined
            this.git_runner_image = "ubuntu:18.04"
            this.git_runner_command = "echo 'this is no real evaluator'"
          }
        }
      },
      methods: {
        clicked: function() {
          this.loading = true
          this.default_upload_name = this.is_ir_task ? "run.txt" : "predictions.jsonl"

          if (this.newDataset()) {
            this.loading = false
          } else {
            this.evaluation_type = 'eval-3'
            this.sandboxed = ''
            get(this.rest_endpoint + `/api/dataset/${this.dataset_id_from_props}`)
              .then(inject_response(this, {'loading': false}, true, ['dataset', 'evaluator']))
              .catch(reportError("Problem loading the dataset.", "This might be a short-term hiccup, please try again. We got the following error: "))
              .then(() => {
                this.is_confidential = '' + this.is_confidential;
                if (this.evaluation_type == "eval-5" || this.evaluation_type == "eval-6") {
                  this.sandboxed = 'false'
                } else {
                  this.sandboxed = 'true'
                }
              })
          }
        },
        is_zip: function(s: string) {
          return s && s.includes('.zip')
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
        fileUpload(fileHandle: any, dataset_type: string, userinfo: UserInfo) {
          const task_id = this.task_id
          return function(message: any) {
            const dataset_id = message['context']['dataset_id']

            if (dataset_id === undefined || '' + dataset_id === 'undefined' || fileHandle === undefined || '' + fileHandle === 'undefined' || fileHandle[0] == undefined || '' + fileHandle[0] === 'undefined') {
              return message
            }

            let formData = new FormData()
            formData.append("file", fileHandle[0]);
            return post_file(`/tira-admin/upload-dataset/${task_id}/${dataset_id}/${dataset_type}`, formData, userinfo)
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
          this.error_message = ''
          this.dataset_id = this.newDataset() ? slugify(this.display_name) : this.dataset_id_from_props
          
          let params: any = {
              'dataset_id': this.dataset_id, 'name': this.display_name, 'task': this.task_id,
              'type': this.dataset_type,'upload_name': this.default_upload_name, 
              'is_confidential': this.is_confidential !== 'false',
              'irds_docker_image': this.irds_docker_image, 'irds_import_command': this.irds_import_command, 'irds_import_truth_command': this.irds_import_truth_command, 
              'git_runner_image': this.git_runner_image,'git_runner_command': this.git_runner_command, 'is_git_runner': true, 'use_existing_repository': false,
              'working_directory': 'obsolete', 'command': 'obsolete', 'publish': this.is_confidential === 'false', 'evaluator_command': 'obsolete', 'evaluator_image': 'obsolete', 'evaluator_working_directory': 'obsolete', 'format': this.format, 'truth_format': this.truth_format, 'description': this.description,
              'chatnoir_id': this.chatnoir_id, 'ir_datasets_id': this.ir_datasets_id,
          }

          if (this.newDataset() && this.upload_type === 'upload-0') {
            params['systemUrlHandle'] = this.systemUrlHandle
            params['truthUrlHandle'] = this.truthUrlHandle

            if (this.is_zip(this.systemUrlHandle) && this.systemUrlDirectory) {
              params['systemUrlDirectory'] = this.systemUrlDirectory
            } else {
              params['systemFileRename'] = this.systemFileRename
            }

            if (this.is_zip(this.truthUrlHandle) && this.truthUrlDirectory) {
              params['truthUrlDirectory'] = this.truthUrlDirectory
            } else {
              params['truthFileRename'] = this.truthFileRename
            }
          }

          if ((this.sandboxed + '').toLowerCase() == 'false') {
            params['trusted_measures'] = this.trusted_measures

            if (this.evaluation_type === 'eval-6') {
              params['run_id_column'] = this.run_id_column
              params['run_label_column'] = this.run_label_column
              params['truth_id_column'] = this.truth_id_column
              params['truth_label_column'] = this.truth_label_column
              params['additional_args'] = this.additional_args
            }
          }

          if (!this.newDataset()) {
            params['git_repository_id'] = this.git_repository_id
          }

          const url = this.rest_endpoint + (this.newDataset() ? '/tira-admin/add-dataset/' + this.task_id : '/tira-admin/edit-dataset/' + this.dataset_id_from_props)
          post(url, params, this.userinfo)
          .then(this.fileUpload(this.systemFileHandle, 'input', this.userinfo))
          .then(this.fileUpload(this.truthFileHandle, 'truth', this.userinfo))
          .then(newDataset => {
            if(this.newDataset()) {
              this.$emit('add-dataset', {'dataset_id': newDataset['context']['dataset_id'], 'display_name': newDataset['context']['display_name']})
            }
            isActive.value = false
            this.submitInProgress = false
            this.display_name = ''
            this.error_message = ''
          })
          .then(reportSuccess("Creation of dataset was successfull."))
          .catch(error => {
            this.error_message = '' + error
            this.submitInProgress = false
            reportError("Problem While Adding the Details of the Task " + this.task_id, "This might be a short-term hiccup, please try again. We got the following error: ")(error)
          })
        },
      },
    }
    </script>
