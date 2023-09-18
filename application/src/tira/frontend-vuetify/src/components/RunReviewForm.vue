<template>
  <loading :loading="loading"/>

  <v-row v-if="!loading">
    <v-col cols="6">
      <h2>Metadata</h2>
      <metadata-items :items="metadata_items"/>
    </v-col>
    <v-col>
      <h2>Review</h2>
      <v-form fast-fail @submit.prevent>
          <v-checkbox v-model="review.noErrors" label="No Errors"/>
          <v-checkbox v-model="review.invalidOutput" label="Output Error"/>
          <v-checkbox v-model="review.otherErrors" label="Software Error"/>
          <v-text-field v-model="review.comment" label="Comment"/>
      </v-form>
      <metadata-items :items="[{'key': 'Reviewer', 'value': review.reviewer}]"/>
      <v-btn @click="submitReview">Update Review</v-btn>
    </v-col>
  </v-row>

  <v-row class="py-6" v-if="!loading">
    <v-col cols="6">
      <v-btn v-if="review.published" @click="togglePublish" variant="outlined" block>
        Unpublish Run
        <v-tooltip>The run is currently published, i.e., visible on the leaderboard. Click to unpublish the run.</v-tooltip>
      </v-btn>
      <v-btn v-if="!review.published" @click="togglePublish" variant="outlined" block>
        Publish Run
        <v-tooltip>The run is currently not published, i.e., not visible on the leaderboard. Click to publish the run, i.e., adding it to the leaderboard.</v-tooltip>
      </v-btn>
    </v-col>
    <v-col cols="6">
      <v-btn v-if="review.blinded" @click="toggleVisible" variant="outlined" block>
        Unblind Run
        <v-tooltip>The run is currently blinded, i.e., outputs are not visible to the participant. Click to unblind the run, i.e., the participant will see the run outputs.</v-tooltip>
      </v-btn>
      <v-btn v-if="!review.blinded" @click="toggleVisible" variant="outlined" block>
        Blind Run
        <v-tooltip>The run is currently unblinded, i.e., outputs are visible to the participant. Click to blind the run, i.e., the participant will not see the run outputs.</v-tooltip>
      </v-btn>
    </v-col>
  </v-row>

  <v-divider class="py-6" v-if="!loading"/>

  <h2 v-if="!loading">Output</h2>
  <v-tabs v-model="tab" align-tabs="title" v-if="!loading">
    <v-tab v-for="item in detailed_tabs" :key="item.key" :value="item.key" >{{ item.key }}</v-tab>
  </v-tabs>
  <v-window v-if="!loading" v-model="tab">
    <v-window-item v-for="item in detailed_tabs" :key="item.key" :value="item.key">
      <v-card flat>
        <v-code tag="pre">{{item.content }}</v-code>
      </v-card>
    </v-window-item>
  </v-window>
</template>
      
<script lang="ts">
import Loading from './Loading.vue'
import MetadataItems from './MetadataItems.vue'
import { get, post, reportError, inject_response, extractDatasetFromCurrentUrl } from '../utils'
    
export default {
  name: "run-review-form",
  components: { Loading, MetadataItems },
  props: ['run_id', 'vm_id', 'dataset_id_from_props'],
  data() {
    return {
      loading: true,
      dataset_id: extractDatasetFromCurrentUrl(),
      run: { software: "", dataset: "", run_id: ""},
      review: { reviewer: "", noErrors: true, missingOutput: false, extraneousOutput: false, invalidOutput: false, hasErrorOutput: false, otherErrors: false, comment: "", hasErrors: false, hasWarnings: false, hasNoErrors: true, published: false, blinded: false},
      runtime: { time: ""},
      files: null,
      stdout: null,
      stderr: null,
      tab: null,
    }
  },
  computed: {
    detailed_tabs() {
      return [{'key': 'Files', 'content': this.files}, {'key': 'StdOut', 'content': this.stdout}, {'key': 'StdErr', 'content': this.stderr}] 
    },
    metadata_items() {
      return [{'key': 'Software', 'value': this.run.software }, {'key': 'Input Dataset', 'value': this.run.dataset }, {'key': 'Run', 'value': this.run.run_id },  {'key': 'Time', 'value': this.runtime.time }, ]
    }
  },
  methods: {
    togglePublish() {
      get('/publish/' + this.vm_id + '/' + this.dataset_id + '/' + this.run_id + '/' + !this.review.published)
      	.then(message => {this.review.published = message.published})
      	.catch(reportError("Problem While (un)publishing the run.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    toggleVisible() {
      get(`/blind/${this.vm_id}/${this.dataset_id}/${this.run_id}/${!this.review.blinded}`)
        .then(message => {this.review.blinded = message.blinded})
      	.catch(reportError("Problem While (un)blinding the run.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    submitReview() {
      post(`/tira-admin/edit-review/${this.dataset_id}/${this.vm_id}/${this.run_id}`, {
            'no_errors': this.review.noErrors,
            'output_error': this.review.invalidOutput,
            'software_error': this.review.otherErrors,
            'comment': this.review.comment,
        }, true).catch(reportError("Problem while Saving the Review.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
  },
  beforeMount() {
    this.loading = true
    let ds_id = this.dataset_id ? this.dataset_id : this.dataset_id_from_props

    get('/api/review/' + ds_id + '/' + this.vm_id + '/' + this.run_id)
        .then(inject_response(this, {'loading': false}))
        .catch(reportError("Problem While Loading the Review", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
