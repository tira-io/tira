<template>
    <v-dialog width="85%" height="85%" scrollable>
      <template v-slot:activator="{ props }">
        <v-btn :disabled="disabled" class="d-sm-none" color="primary" icon="mdi-plus" v-if="dataset_id === ''" v-bind="props" @click="clicked()"/>
        <v-btn :disabled="disabled" class="d-none d-sm-flex" color="primary" prepend-icon="mdi-plus" v-if="dataset_id === ''" size="large" v-bind="props" @click="clicked()">New Dataset</v-btn>
    
        <v-btn :disabled="disabled" class="d-none d-sm-flex" color="primary" v-if="dataset_id !== ''" prepend-icon="mdi-cog" size="large" v-bind="props" @click="clicked()">Edit Dataset</v-btn>
        <v-btn :disabled="disabled" class="d-sm-none" color="primary" icon="mdi-cog" v-if="dataset_id !== ''" v-bind="props" @click="clicked()"/>
      </template>
      <template v-slot:default="{ isActives }">
        <v-card class="pb-1">
          <loading :loading="loading" />
          <card-title>
            <v-toolbar color="primary" :title="title"/>
          </card-title>
        
          <v-card-text>
            <v-form ref="form" v-model="valid">
                <v-text-field v-model="dataset_id_field" label="Dataset ID" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>
                <v-text-field v-model="dataset_name" label="Dataset Name" :rules="[v => v && v.length > 2 || 'Please provide a name.']" required/>
                
                <v-radio-group v-model="dataset_type">
                  <v-radio label="This is a training dataset (users see results/outputs)" value="training"></v-radio>
  <v-radio label="This is a test dataset (users see no results/outputs)" value="test"></v-radio>
</v-radio-group>

                <v-checkbox v-model="is_public" label="Public" />

                <v-divider/>
                <h2 class="my-1">Provide the Actual Data</h2>
                Some description here.

                <v-radio-group v-model="upload_type">
                    <v-radio label="I want to manually upload the data now" value="upload-1"></v-radio>
                    <v-radio label="I want to use the ir_datasets integration to upload an dataset in ir_datasets" value="upload-2"></v-radio>
                    <v-radio label="I want to upload the data via CephFS" value="upload-3"></v-radio>
</v-radio-group>

                <v-file-input v-if="upload_type === 'upload-1'" label="Input Data for Systems (.zip file)"></v-file-input>
                <v-file-input v-if="upload_type === 'upload-1'" label="Ground Truth for Evaluation (.zip file)"></v-file-input>

                <v-text-field v-if="upload_type === 'upload-2'" v-model="irds_image" label="Docker Image of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                <v-text-field v-if="upload_type === 'upload-2'" v-model="irds_command" label="Command of the ir_datasets integration" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>

                <p v-if="upload_type === 'upload-3'">
                    You can see the commands to upload your data via CephFS after the dataset was created.
                </p>

                <v-divider/>
                <h2 class="my-1">Evaluation</h2>
                Some description here.
                <v-text-field v-model="evaluation_image" label="Docker Image of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a docker image.']" required/>
                <v-text-field  v-model="evaluation_command" label="Command of the Evaluator" :rules="[v => v && v.length > 2 || 'Please provide a command.']" required/>
              </v-form>
          </v-card-text>
          <v-card-actions class="justify-end">
            <v-row>
            <v-col cols="6"><v-btn variant="outlined" @click="isActives.value = false" block>Close</v-btn></v-col>
            <v-col cols="6" v-if="!loading"><v-btn variant="outlined" :loading="submitInProgress" :disabled="valid" block>Submit</v-btn></v-col>
          </v-row>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
    </template>
        
    <script lang="ts">
    import { Loading } from '.'
    import {VAutocomplete} from "vuetify/components";
    import { get, post, reportError, slugify, extractRole, extractOrganizations, inject_response } from '../utils'
    
    export default {
      name: "edit-dataset",
      components: {Loading, VAutocomplete},
      props: {task_id: {}, dataset_id: {type: String, default: ''}, disabled: {type: Boolean, default: false}},
      data: () => ({
        loading: true, valid: false, submitInProgress: false,
        dataset_id_field: '', dataset_name: '', is_public: false, dataset_type: 'test',
        evaluation_image: '', evaluation_command: '', upload_type: 'upload-1',
        irds_image: '', irds_command: '',
      }),
      computed: {
        title() {
          return this.dataset_id === '' ? 'Add New Dataset' : 'Edit Dataset ' + this.dataset_id;
        }
      },
      methods: {
          clicked: function() {
            console.log('assaassa')
            if (this.dataset_id === '') {
              this.loading = false
            } else {
              this.loading = false
            }
          },
          isValid: async function() {
            const form = this.$refs.form as any
            if (!form) {
              return false
            }
    
            return await form.validate()
          },
        },
    }
    </script>
    