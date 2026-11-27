<template>
  <v-card class="mb-4" variant="outlined">
    <v-card-title>Review of Docker Submission</v-card-title>
    <v-card-text>
      <loading :loading="loading" />
      <v-form v-if="!loading">
        <v-select label="Code review" v-model="review.code_review" :items="states" density="compact" />
        <v-select label="Review of executions" v-model="review.execution_review" :items="states" density="compact" />
        <v-textarea label="Comment" v-model="review.comment" rows="3" auto-grow density="compact" />
        <div v-if="review.reviewer_id" class="text-caption mb-2">Last reviewed by {{ review.reviewer_id }} ({{ review.review_date }})</div>
        <v-btn color="primary" :loading="saving" @click="save()">Save review</v-btn>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import { inject } from 'vue'

import Loading from './Loading.vue'
import { get, reportError, reportSuccess, type UserInfo } from '../utils'

export default {
  name: "docker-software-review",
  components: { Loading },
  props: ['docker_software_id'],
  data() {
    return {
      userinfo: inject('userinfo') as UserInfo,
      rest_url: inject("REST base URL"),
      states: ['pending', 'approved', 'rejected'],
      review: { code_review: 'pending', execution_review: 'pending', comment: '', reviewer_id: '', review_date: '' } as any,
      loading: true,
      saving: false,
    }
  },
  methods: {
    fetchData() {
      this.loading = true
      get(this.rest_url + '/v1/admin/docker-software-review/' + this.docker_software_id)
        .then((r: any) => { this.review = r.context; this.loading = false })
        .catch(reportError("Problem while loading the review", "Please try again. We got the following error: "))
    },
    async save() {
      this.saving = true
      try {
        const response = await fetch(this.rest_url + '/v1/admin/docker-software-review/' + this.docker_software_id, {
          method: 'PUT',
          credentials: 'include',
          headers: { 'Accept': 'application/json', 'Content-Type': 'application/json', 'X-CSRFToken': this.userinfo.csrf },
          body: JSON.stringify({ code_review: this.review.code_review, execution_review: this.review.execution_review, comment: this.review.comment }),
        })
        const result = await response.json()
        if (!response.ok || result.status !== 0) {
          throw new Error(result.message || ('Status ' + response.status))
        }
        this.review = result.context
        reportSuccess('Review saved.')
      } catch (e: any) {
        reportError("Problem while saving the review", "We got the following error: ")(e)
      }
      this.saving = false
    },
  },
  mounted() { this.fetchData() },
  watch: { docker_software_id() { this.fetchData() } },
}
</script>
