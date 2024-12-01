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
      <v-skeleton-loader type="card" v-if="dataset === undefined || submissionToClaim === undefined"/>
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
          for task <a :href="'/task-overview/' + dataset.default_task">{{ dataset.default_task }}</a>.
        </p>

        <div class="py-2"></div>

        <p v-if="userinfo.role === 'guest'">
          Please <a href='/login'>login</a> to claim ownership.
        </p>
        <div v-if="userinfo.role !== 'guest'">
          <v-divider/>
          <h3 class="my-1">Public Access to the Data and Submissions</h3>
          <p>You can make the data public so that users can download the data and submissions, e.g., after the shared task is finished or for participants to verify their software.</p>

          <v-radio-group v-model="new_software">
            <v-radio label="This dataset is public (users can access the data and published submissions)" value="false"></v-radio>
            <v-radio label="This dataset is confidential (only organizers can access the data and submissions)" value="true"></v-radio>
          </v-radio-group>
          <v-btn>Claim Ownersip</v-btn>
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
  
import { get, chatNoirUrl, irDatasetsUrls, type UserInfo, type DatasetInfo, type ClaimSubmissionInfo } from './utils';
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
      rest_url: inject("REST base URL"),
      new_software: false,
    }
  },
  methods: {
    loadData() {
      this.dataset = undefined
      this.submissionToClaim = undefined
      this.$router.push({ path: '/claim-submission/' + this.uuid})

      get(this.rest_url + '/v1/anonymous/' + this.uuid)
        .then((i) => {this.submissionToClaim = i as ClaimSubmissionInfo})
        .then(() => {
          if (this.submissionToClaim && this.submissionToClaim.dataset_id) {
            get(this.rest_url + '/v1/datasets/view/' + this.submissionToClaim.dataset_id).then((i) => this.dataset = i as DatasetInfo)
          }
        })
    },
  },
  
  computed: {
    link_chatnoir() { return  chatNoirUrl(this.dataset) },
    link_ir_datasets() { 
      let ret = irDatasetsUrls(this.dataset)

      if (ret && Object.keys(ret).length == 1) {
        return ret[Object.keys(ret)[0]]
      } else {
        return undefined
      }
    },
  },
  beforeMount() {
    this.uuid = this.$route.params.uuid as string
    this.loadData()
  }
}
</script>
  