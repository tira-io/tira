<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="count_of_team_submissions" density="compact">
      <template v-slot:item="row">
          <tr>
            <td>{{row.item.team}}</td>
            <td>{{row.item.reviewed}}</td>
            <td>{{row.item.to_review}}</td>
            <td>{{row.item.total}}</td>
            <td>
                <a :href="row.item.link">
                    link to {{row.item.team}}`s page
                </a>
            </td>
          </tr>
      </template>
    </v-data-table>
</template>
  
<script lang="ts">
import { Loading } from '.'
import { get, reportError, inject_response} from '../utils'

interface CountOfTeamSubmissions {
  team: string,
  reviewed: number,
  to_review: number,
  total: number,
  link: string

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
      { title: 'Reviewed Submissions', key: 'reviewed' },
      { title: 'To review', key: 'to_review' },
      { title: 'Total', key: 'total' },
      { title: 'Team Page', key: 'link' }
    ],
  }},
   beforeMount() {
    this.loading = true
    get('/api/count-of-team-submissions/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of Submissions per Team", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
