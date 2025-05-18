<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="count_of_team_submissions" density="compact">
      <template v-slot:item="row">
          <tr>
            <td>{{row.item.team}}</td>
            <td>{{row.item.token}}</td>
            <td>{{row.item.reviewed}}</td>
            <td>{{row.item.to_review}}</td>
            <td>{{row.item.total}}</td>
            <td>
                <a :href="row.item.link">
                    link to {{row.item.team}}`s page
                </a>
            </td>
            <td>
                <a :href="row.item.link_submission">
                    link to {{row.item.team}}`s page
                </a>
            </td>
          </tr>
      </template>
    </v-data-table>
</template>
  
<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, reportError, inject_response} from '../utils'

interface CountOfTeamSubmissions {
  team: string,
  reviewed: number,
  to_review: number,
  total: number,
  link: string,
  token: boolean,
  link_submission: string
}

export default {
  name: "overview-registered-teams",
  components: {Loading},
  props: ['task'],
  data() { return {
    loading: true,
    count_of_team_submissions:[] as CountOfTeamSubmissions[],
    table_headers: [
      { title: 'Team', key: 'team' },
      { title: 'Has Token', key: 'token' },
      { title: 'Reviewed Submissions', key: 'reviewed' },
      { title: 'To review', key: 'to_review' },
      { title: 'Total', key: 'total' },
      { title: 'Team Page', key: 'link' },
      { title: 'Submission Page', key: 'link_submission' }
    ],
  }},
   beforeMount() {
    this.loading = true
    get(inject("REST base URL")+'/api/count-of-team-submissions/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of Submissions per Team", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
