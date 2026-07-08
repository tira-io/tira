<template>
  <v-dialog width="85%" height="85%" scrollable>
    <template v-slot:activator="{ props }">
      <v-btn class="d-sm-none" color="primary" icon="mdi-plus" v-if="task_id_for_edit === ''" v-bind="props"
        @click="clicked()" />
      <v-btn class="d-none d-sm-flex" color="primary" prepend-icon="mdi-plus" v-if="task_id_for_edit === ''"
        size="large" v-bind="props" @click="clicked()">New Task</v-btn>

      <v-btn class="d-none d-sm-flex" color="primary" v-if="task_id_for_edit !== ''" prepend-icon="mdi-cog" size="large"
        v-bind="props" @click="clicked()">Edit Task</v-btn>
      <v-btn class="d-sm-none" color="primary" icon="mdi-cog" v-if="task_id_for_edit !== ''" v-bind="props"
        @click="clicked()" />
    </template>
    <template v-slot:default="{ isActive }">
      <v-card class="pb-1">
        <loading :loading="loading" />
        <card-title>
          <v-toolbar color="primary" :title="title">
            <div>
              <v-avatar class="mx-1" v-if="!loading" style="cursor: pointer" :color="step === 1 ? 'secondary' : 'grey'"
                size="24" v-text="1" @click="() => go_to_step(1)" />
              <v-avatar class="mx-1" v-if="!loading" style="cursor: pointer" :color="step === 2 ? 'secondary' : 'grey'"
                size="24" v-text="2" @click="() => go_to_step(2)" />
              <v-avatar class="mx-1" v-if="!loading" style="cursor: pointer" :color="step === 3 ? 'secondary' : 'grey'"
                size="24" v-text="3" @click="() => go_to_step(3)" />
            </div>
          </v-toolbar>
        </card-title>

        <v-card-text>
          <v-window v-model="step" v-if="!loading" :touch="{ left: () => { }, right: () => { } }">
            <v-window-item :value="1">
              <v-card-text>
                <h2 class="my-1">Organize your Task</h2>
                <p>This form will guide you through the configuration of your shared task with TIRA.</p>
                <v-divider />
                <p>While you can add your new task without preparation, we recommend that you prepare the following to
                  make the participation as simple as possible (please note that you can also add and modify those
                  components at any later point in time):</p>

                <h3 class="my-1">Component 1 (optional): A Smoke Test Dataset</h3>
                <p>A very small dataset (e.g., of 5 input instances) that can be used that participants get very fast
                  feedback that their software is compatible with the data format for the task. This is intended to be
                  fully public so that participants can use the smoke test dataset to test their software on their
                  machine</p>
                <v-divider />
                <h3 class="my-1">Component 2 (optional): An Evaluator</h3>
                <p>A docker image that uses the ground-truth data and the outputs of some software as input to test if
                  the outputs are valid and to measure their effectiveness. We already have many evaluators for many
                  different scenarious available. Please look <a
                    href="https://tira-io.github.io/tira/organizers/organizing-tasks.html#create-a-docker-image-for-your-evaluator">at
                    the documentation</a> for existing evaluators and a step-by-step guide to build a new evaluator.</p>
                <v-divider />
                <h3 class="my-1">Component 3 (optional): Datasets</h3>
                <p>You can upload as many datasets (consisting of the inputs for software submissions and the ground
                  truth for evaluation) as you like in whatever format you want. TIRA distinguishes between public
                  datasets for which participants can see the outputs to verify that their software submission is
                  correct and test datasets for which all outputs and evaluations are blinded and not visible to
                  participants.</p>
                <v-divider />
                <h3 class="my-1">Component 4 (optional): Baselines</h3>
                <p>In the best case, you provide the code, a published docker image, and instructions on how to compile
                  the code into a docker image to simplify participation in your shared tasks. We have some examples on
                  baselines that you can adopt for your shared task <a
                    href="https://tira-io.github.io/tira/organizers/organizing-tasks.html#provide-public-baselines-to-simplify-participation">in
                    the documentation</a>.</p>
              </v-card-text>
            </v-window-item>

            <v-window-item :value="2">
              <v-card-text>
                <v-form ref="form" v-model="valid">
                  <v-text-field v-model="task_name" label="Task Name"
                    :rules="[v => v && v.length > 2 || 'Please provide a name.']" required />
                  <v-checkbox v-model="featured" label="Featured" />
                  <v-textarea v-model="task_description" label="Task Description"
                    :rules="[v => v && v.length > 2 || 'Please provide a task description.']" required />

                  <v-divider v-if="task_id_for_edit === ''" />
                  <h2 class="my-1" v-if="task_id_for_edit === ''">Details on the Organizer</h2>

                  <p v-if="task_id_for_edit === ''">If you are not yet part of an organizer group or want to create a
                    new group please <a
                      href="https://www.tira.io/new-message?username=tira_org_webis&title=Request%20&body=message%20body">contact
                      us</a>, we usually respond within one day.</p>

                  <v-autocomplete v-if="task_id_for_edit === ''" v-model="selected_organizer"
                    :items="userinfo.organizer_teams" label="Organizer"
                    :rules="[v => !!(v && v.length) || 'Please select the organizer of your task.']" required />
                  <v-text-field v-model="web" label="Website"
                    :rules="[v => v && v.length > 2 || 'Please provide a task website.']" required />

                  <v-divider />
                  <h2 class="my-1">Registration of Teams</h2>
                  <v-checkbox v-model="require_registration"
                    label="Require Registration (When checked, users must register before submission. They must provide their name, email, and affiliation. You can view the registration data afterwards.)" />
                  <v-checkbox v-model="require_groups"
                    label="Require Teams (When checked, users must register in a team. Their runs will be displayed with the teams's name. Other users can join these teams.)" />
                  <v-checkbox v-model="restrict_groups"
                    label="Restrict Teams (When checked, users can not create and name their own groups. They can only sign up to groups provided by you.)" />
                  <v-textarea v-if="restrict_groups" v-model="allowed_task_teams"
                    label="Allowed Teams for Task (leave empty if all teams are allowed)" />

                  <v-divider />
                  <h2 class="my-1">Help for Participants</h2>
                  <v-text-field v-model="command_placeholder" label="Help Command" />
                  <v-textarea v-model="command_description" label="Help Text" />
                  <v-text-field label="Link to Baseline" />
                  <v-textarea
                    v-model="upload_form_fields_json"
                    label="Upload Form Fields (JSON)"
                    :hint="upload_form_fields_hint"
                    persistent-hint
                    :rules="[validateUploadFormFieldsJson]"
                  />
                  <v-textarea
                    v-model="submission_tabs_json"
                    label="Submission Tabs (JSON)"
                    :hint="submission_tabs_hint"
                    persistent-hint
                    :rules="[validateSubmissionTabsJson]"
                  />

                  <v-divider />
                  <h2 class="my-1">IR-Datasets integration</h2>
                  <v-checkbox v-model="is_ir_task" label="The task is an information retrieval task with ir_datasets" />
                  <v-text-field v-if="is_ir_task" v-model="irds_re_ranking_image"
                    label="Docker Image for Re-Ranking with ir_datasets" />
                  <v-text-field v-if="is_ir_task" v-model="irds_re_ranking_command"
                    label="Command for Re-Ranking with ir_datasets" />
                  <v-text-field v-if="is_ir_task" v-model="irds_re_ranking_resource"
                    label="Resource for Re-Ranking with ir_datasets" />

                </v-form>
              </v-card-text>
            </v-window-item>

            <v-window-item :value="3">
              <v-card-text>
                <h2>Do you want to create the new Task?</h2>
                (A detailed summary of what will be created will be shown here soon)
              </v-card-text>
            </v-window-item>
          </v-window>
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-row>
            <v-col cols="6"><v-btn variant="outlined" @click="isActive.value = false" block>Close</v-btn></v-col>
            <v-col cols="6" v-if="!loading && step < 3"><v-btn variant="outlined" @click="go_to_step(step + 1)"
                block>Next Step</v-btn></v-col>
            <v-col cols="6" v-if="!loading && step === 3"><v-btn variant="outlined" @click="submit(isActive)"
                :loading="submitInProgress" block>Submit</v-btn></v-col>
          </v-row>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
</template>

<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { VAutocomplete } from "vuetify/components";
import { get, post, reportError, slugify, inject_response, type UserInfo } from '../utils'

const AVAILABLE_SUBMISSION_TABS = [
  'code-submission',
  'docker-submission',
  'upload-submission',
  'upload-submission-simplified',
  'upload-models',
]

export default {
  name: "edit-task",
  components: { Loading, VAutocomplete },
  props: {
    'task_id_for_edit': {
      type: String,
      required: true,
    },
    'userinfo': {
      type: Object as () => UserInfo,
      required: true,
    },
  },
  data: () => ({
    loading: true, valid: false, step: 1, submitInProgress: false, selected_organizer: '', organizer_id: '',
    task_name: '', featured: false, web: '', task_description: '', command_description: '', command_placeholder: '',
    require_registration: false, require_groups: false, restrict_groups: false, allowed_task_teams: '',
    is_ir_task: false, irds_re_ranking_image: '', irds_re_ranking_command: '', irds_re_ranking_resource: '',
    submission_tabs: null as null | string[],
    submission_tabs_json: '',
    submission_tabs_hint: 'Optional JSON array of submission tabs, e.g. ["docker-submission","upload-submission-simplified"]. Allowed values: code-submission, docker-submission, upload-submission, upload-submission-simplified, upload-models.',
    upload_form_fields: null as null | { name: string, display_name: string, type: string, required?: boolean, options?: { id: string, display_value: string }[] }[],
    upload_form_fields_json: '',
    upload_form_fields_hint: 'Optional JSON array of fields, e.g. [{"name":"run_id","display_name":"Run ID","type":"text"},{"name":"track","display_name":"Track","type":"select","options":[{"id":"main","display_value":"Main Track"},{"id":"bio","display_value":"Biomedical Track"}]}]. Select fields require a non-empty options array with id and display_value.',
    rest_endpoint: inject("REST base URL") as string
  }),
  computed: {
    title() {
      return this.task_id_for_edit === '' ? 'Add New Task' : 'Edit Task ' + this.task_id_for_edit;
    }
  },
  methods: {
    clicked: function () {
      if (this.task_id_for_edit === '') {
        this.loading = false
        this.submission_tabs_json = this.formatSubmissionTabs(null)
        this.upload_form_fields_json = this.formatUploadFormFields(null)
      } else {
        get(this.rest_endpoint + '/api/task/' + this.task_id_for_edit)
          .then(inject_response(this, { 'loading': false }, true, 'task'))
          .then(() => {
            this.submission_tabs_json = this.formatSubmissionTabs(this.submission_tabs)
            this.upload_form_fields_json = this.formatUploadFormFields(this.upload_form_fields)
          })
          .catch(reportError("Problem loading the data of the task.", "This might be a short-term hiccup, please try again. We got the following error: "))
      }
    },
    formatSubmissionTabs: function (submissionTabs: null | string[]) {
      return submissionTabs && submissionTabs.length > 0 ? JSON.stringify(submissionTabs, null, 2) : ''
    },
    formatUploadFormFields: function (uploadFormFields: null | { name: string, display_name: string, type: string, required?: boolean, options?: { id: string, display_value: string }[] }[]) {
      return uploadFormFields && uploadFormFields.length > 0 ? JSON.stringify(uploadFormFields, null, 2) : ''
    },
    parseSubmissionTabs: function () {
      if (!this.submission_tabs_json.trim()) {
        return null
      }

      try {
        const parsed = JSON.parse(this.submission_tabs_json)
        if (!Array.isArray(parsed)) {
          return undefined
        }

        for (const tab of parsed) {
          if (
            typeof tab !== 'string'
            || tab.trim() === ''
            || !AVAILABLE_SUBMISSION_TABS.includes(tab.trim())
          ) {
            return undefined
          }
        }

        return parsed.map(tab => tab.trim())
      } catch {
        return undefined
      }
    },
    parseUploadFormFields: function () {
      if (!this.upload_form_fields_json.trim()) {
        return null
      }

      try {
        const parsed = JSON.parse(this.upload_form_fields_json)
        if (!Array.isArray(parsed)) {
          return undefined
        }

        for (const field of parsed) {
          if (
            !field
            || typeof field.name !== 'string'
            || typeof field.display_name !== 'string'
            || typeof field.type !== 'string'
            || field.name.trim() === ''
            || field.display_name.trim() === ''
            || field.type.trim() === ''
          ) {
            return undefined
          }

          if (field.type.trim() === 'select') {
            if (!Array.isArray(field.options) || field.options.length === 0) {
              return undefined
            }

            for (const option of field.options) {
              if (
                !option
                || typeof option.id !== 'string'
                || typeof option.display_value !== 'string'
                || option.id.trim() === ''
                || option.display_value.trim() === ''
              ) {
                return undefined
              }
            }
          }
        }

        return parsed
      } catch {
        return undefined
      }
    },
    validateUploadFormFieldsJson: function () {
      const parsed = this.parseUploadFormFields()
      return parsed !== undefined || 'Please provide a valid JSON array of fields with name, display_name, and type. Select fields must also define non-empty options with id and display_value.'
    },
    validateSubmissionTabsJson: function () {
      const parsed = this.parseSubmissionTabs()
      return parsed !== undefined || `Please provide a valid JSON array of submission tab IDs: ${AVAILABLE_SUBMISSION_TABS.join(', ')}.`
    },
    go_to_step: async function (step: number) {
      if (this.submitInProgress) {
        return
      }

      if (step > 1 && this.userinfo.role == 'guest') {
        window.alert('Please login to continue.')
        location.href = '/login'
        this.step = 1
      }

      if (step > 2) {
        const { valid } = await this.isValid()
        if (!valid) {
          window.alert('Please fill out all required fields.')
          this.step = 2
          return
        }
      }

      this.step = Math.max(Math.min(step, 3), 1)
    },
    isValid: async function () {
      const form = this.$refs.form as any
      if (!form) {
        return false
      }

      return await form.validate()
    },
    submit: async function (isActive: any) {
      const { valid } = await this.isValid()

      if (!valid) {
        window.alert('Please fill out all required fields.')
        this.step = 2
        return
      }

      this.submitInProgress = true
      const submissionTabs = this.parseSubmissionTabs()
      const uploadFormFields = this.parseUploadFormFields()
      if (submissionTabs === undefined) {
        this.submitInProgress = false
        window.alert('Please provide valid submission tab JSON.')
        this.step = 2
        return
      }

      if (uploadFormFields === undefined) {
        this.submitInProgress = false
        window.alert('Please provide valid upload form field JSON.')
        this.step = 2
        return
      }

      post(this.url(), this.task_representation(), this.userinfo)
        .then(() => {
          isActive.value = false
          this.step = 1
          this.submitInProgress = false
          location.reload()
        }).catch(reportError("Problem While Adding/Editing a Shared Task.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    url: function () {
      return this.rest_endpoint + (this.task_id_for_edit === '' ? '/tira-admin/' + this.selected_organizer + '/create-task' : '/tira-admin/edit-task/' + this.task_id_for_edit)
    },
    task_representation: function () {
      const task_id = this.task_id_for_edit === '' ? slugify(this.task_name) : this.task_id_for_edit
      const organizer = this.task_id_for_edit === '' ? this.selected_organizer : this.organizer_id
      const submissionTabs = this.parseSubmissionTabs()
      const uploadFormFields = this.parseUploadFormFields()

      return {
        'task_id': task_id, 'name': this.task_name, 'featured': this.featured,
        'website': this.web, 'description': this.task_description, 'help_text': this.command_description, 'help_command': this.command_placeholder,
        'require_registration': this.require_registration, 'require_groups': this.require_groups, 'restrict_groups': this.restrict_groups,
        'task_teams': this.allowed_task_teams, 'is_information_retrieval_task': this.is_ir_task,
        'irds_re_ranking_image': this.irds_re_ranking_image, 'irds_re_ranking_command': this.irds_re_ranking_command, 'irds_re_ranking_resource': this.irds_re_ranking_resource, 'organizer': organizer,
        'submission_tabs': submissionTabs === undefined ? null : submissionTabs,
        'upload_form_fields': uploadFormFields === undefined ? null : uploadFormFields,
      }
    }
  },
}
</script>
