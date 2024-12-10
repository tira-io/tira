<template>
    <tira-breadcrumb />

    <v-container>
      <h3 class="text-h3 py-5">Claim Ownership</h3>
      <p>By entering the ownership UUID of a submission you can become registered as the owner of a submission. Being the owner of a submission allows you to submit it to a shared task.</p>


      <div class="py-2"></div>
      <v-text-field label="Ownership UUID" v-model="uuid" append-inner-icon="mdi-send" @click:append-inner="loadData" class="px-10"></v-text-field>
      <div class="py-2"></div>
    </v-container>

    <v-container>
      <v-divider/>

      <h3>Details</h3>
      <div class="py-2"></div>
      <v-skeleton-loader type="card" v-if="(dataset === undefined || submissionToClaim === undefined) && !error"/>
      <div v-if="error">
        No submission with ownership UUID {{ uuid }} exists.
      </div>
      <div v-if="dataset !== undefined && submissionToClaim !== undefined">
        <p>
        The run was submitted on {{ submissionToClaim.created }} to the dataset <a :href="'/datasets?query=' + dataset.dataset_id">{{ dataset.display_name }}</a>
          <span v-if="link_chatnoir !== undefined && link_ir_datasets !== undefined">
            (browse in <a :href="link_chatnoir" target="_blank">ChatNoir</a> or <a :href="link_ir_datasets" target="_blank">ir_datasets</a>)
          </span>
          <span v-if="link_chatnoir !== undefined && link_ir_datasets === undefined">
            (browse in <a :href="link_chatnoir" target="_blank">ChatNoir</a>)
          </span>
          <span v-if="link_chatnoir === undefined && link_ir_datasets !== undefined">
            (browse in <a :href="link_ir_datasets" target="_blank">ir_datasets</a>)
          </span>
          for task <a :href="'/task-overview/' + dataset.default_task">{{ dataset.default_task }}</a> <span v-if="download_link !== undefined">(<a :href="download_link" target="_blank">Download</a></span>).
        </p>

        <div class="py-2"></div>

        <p v-if="userinfo.role === 'guest'">
          Please <a href='/login'>login</a> to claim ownership.
        </p>
        <p v-if="userinfo.role !== 'guest' && !registered">
          You are not registered for the task, please <a :href="'/task-overview/' + dataset.default_task">register</a> to claim ownership.
        </p>
        <div v-if="userinfo.role !== 'guest' && registered">
          <v-divider/>
          <h3 class="my-1">Please Describe Your Run</h3>
          <p>We need a description of your submission, specifically on the approach that produced the run:</p>

          <v-radio-group v-model="new_software">
            <v-radio label="I have submitted a run from the approach before (I.e., the approach is already described in TIRA)" value="false"></v-radio>
            <v-radio label="I have not yet submitted a run from the approach (I.e., the approach has not yet a description in TIRA)" value="true"></v-radio>
          </v-radio-group>

        <v-form ref="form">
          <div v-if="new_software !== undefined && ('' + new_software) == 'true'">
            <v-text-field v-model="display_name" label="Name" counter="30" required="True" :rules="[title_rule]"/>
            <v-textarea v-model="description" label="Description" counter="500" :rules="[description_rule]"/>
            <v-text-field v-model="paper_link" label="Link your Paper"/>
          </div>
          <v-autocomplete v-if="new_software !== undefined && ('' + new_software) == 'false'" clearable auto-select-first label="Choose approach &hellip;" prepend-inner-icon="mdi-magnify"
          :items="upload_groups" item-title="display_name" item-value="id" variant="underlined" v-model="selected_upload_group" :rules="[select_rule]"/>
        </v-form>
          <v-btn :disabled="new_software === undefined || claim_in_progress" :loading="claim_in_progress" @click="submitForm()">Claim Ownersip</v-btn>
          <div class="py-2"></div>
          <v-divider/>
          <!--<h3 class="my-1">Inspect Submission</h3>
          <run-page :dataset_id="dataset.dataset_id" :chatnoir_id="dataset.chatnoir_id" :run_uuid="uuid"/>-->
        </div>
      </div>
    </v-container>
</template>
  
<script lang="ts">
import { inject } from 'vue'
  
import { get, post, vm_id, inject_response, reportError, chatNoirUrl, irDatasetsUrls, type UserInfo, type DatasetInfo, type ClaimSubmissionInfo, type UploadGroupInfo } from './utils';
import { Loading, TiraBreadcrumb } from './components'
import RunPage from './tirex/RunPage.vue'

export default {
  name: "claim-submission",
  components: { Loading, TiraBreadcrumb, RunPage },
  data() {
    return {
      userinfo: inject('userinfo') as UserInfo,
      uuid: '' as string,
      dataset: undefined as DatasetInfo | undefined,
      submissionToClaim: undefined as ClaimSubmissionInfo | undefined,
      error: false,
      rest_url: inject("REST base URL"),
      new_software: undefined,
      vm: undefined,
      user_vms_for_task: [] as string[],
      additional_vms: undefined,
      user_id: undefined,
      task: undefined,
      upload_groups: [] as UploadGroupInfo[],
      selected_upload_group: undefined,
      display_name: '' as string,
      description: '' as string,
      paper_link: '' as string,
      claim_in_progress: false
    }
  },
  methods: {
    title_rule(v: any) {if (v && v.length < 30 && v.length > 0) return true; return 'Please enter a name for your approach'},
    select_rule(v: any) {if (v) return true; return 'Please select an approach'},
    description_rule(v: any) {if (v && v.length < 500 && v.length > 0) return true; return 'Please enter a description for your approach (less than 500 characters)'},
    loadData() {
      this.dataset = undefined
      this.submissionToClaim = undefined
      this.error = false
      this.$router.push({ path: '/claim-submission/' + this.uuid})

      get(this.rest_url + '/v1/anonymous/' + this.uuid)
        .then((i) => {this.submissionToClaim = i as ClaimSubmissionInfo})
        .then(() => {
          if (this.submissionToClaim && this.submissionToClaim.dataset_id) {
            get(this.rest_url + '/v1/datasets/view/' + this.submissionToClaim.dataset_id).then((i) => {
              get(this.rest_url + '/api/task/' + i.default_task)
                .then(inject_response(this, { 'loading': false }, true))
                .then(() => {
                  this.dataset = i as DatasetInfo
                  if (this.registered) {
                    get(this.rest_url + '/api/submissions-for-task/' + this.dataset.default_task + '/' + this.vm_id + '/upload')
                    .then((uploads) => {
                      this.upload_groups = uploads['context']['all_uploadgroups']
                    })
                  }
                })
          })
        }
      }).catch(() => { this.error = true })
    },
    async submitForm() {
      const form = this.$refs.form as any
      const { valid } = await form.validate()
      if (valid && this.dataset) {
        let params : Record<string, string> = {}
        let task_id = this.dataset.default_task
        if (this.new_software !== undefined && ('' + this.new_software) == 'true') {
          params['display_name'] = this.display_name + ''
          params['description'] = this.description + ''
          params['paper_link'] = this.paper_link + ''
        } else {
          params['upload_group'] = this.selected_upload_group + ''
        }
        this.claim_in_progress = true
        post(this.rest_url + `/v1/anonymous/claim/` + this.vm_id + '/' + this.uuid, params, this.userinfo)
        .then((i) => {this.$router.push({ path: '/submit/' +  task_id + '/user/' + this.vm_id + '/upload-submission/' + i['upload_group']})})
        .catch(reportError("Could not claim submission."))
        .finally(() => this.claim_in_progress = false)
      }
    }
  },
  computed: {
    link_chatnoir() { return  chatNoirUrl(this.dataset) },
    download_link() { 
      if (this.submissionToClaim && this.submissionToClaim.dataset_id && this.dataset) {
        return this.rest_url + `/v1/anonymous/download/` + this.submissionToClaim.uuid
      }
    },
    registered() { return this.vm_id && this.vm_id !== undefined && ('' + this.vm_id) !== 'undefined' && ('' + this.vm_id) !== 'null'},
    link_ir_datasets() { 
      let ret = irDatasetsUrls(this.dataset)

      if (ret && Object.keys(ret).length == 1) {
        return ret[Object.keys(ret)[0]]
      } else {
        return undefined
      }
    },
    vm_id() {
      return vm_id(this.vm_ids, this.vm, this.user_vms_for_task, this.additional_vms, this.user_id, this.task)
    },
    vm_ids() {
      return this.user_vms_for_task.length > 1 ? this.user_vms_for_task : null;
    },
  },
  beforeMount() {
    this.uuid = this.$route.params.uuid as string
    this.loadData()
  }
}
</script>
  