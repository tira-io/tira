<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="software_to_review" density="compact">
      <template v-slot:item="row">
          <tr>
            <td>{{row.item.team}}</td>
            <td>{{row.item.display_name}}</td>
            <td>{{row.item.latest_automatic_verdict || 'not reviewed'}}</td>
            <td>{{row.item.code_review}} / {{row.item.execution_review}}</td>
            <td>
              <a :href="row.item.link_submission">link to {{row.item.team}}`s submission page</a>
            </td>
          </tr>
      </template>
    </v-data-table>
</template>

<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, inject_response, reportError } from '../utils'

interface SoftwareToReview {
  docker_software_id: number,
  team: string,
  display_name: string,
  latest_automatic_verdict: string | null,
  code_review: string,
  execution_review: string,
  link_submission: string,
}

export default {
  name: "overview-software-to-review",
  components: { Loading },
  props: ['task'],
  data() {
    return {
      loading: true,
      software_to_review: [] as SoftwareToReview[],
      rest_url: inject("REST base URL"),
      table_headers: [
        { title: 'Team', key: 'team' },
        { title: 'Software', key: 'display_name' },
        { title: 'Automatic Review', key: 'latest_automatic_verdict' },
        { title: 'Human Review (Code / Execution)', key: 'code_review' },
        { title: 'Submission Page', key: 'link_submission' },
      ],
    }
  },
  beforeMount() {
    this.loading = true
    get(this.rest_url + '/api/software-to-review/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Software to Review", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
