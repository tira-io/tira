<template>
    <loading :loading="loading"/>
    <v-data-table v-if="!loading" :headers="table_headers" :items="count_of_team_software" density="compact">
      <template v-slot:item="row">
          <tr>
            <td>{{row.item.team}}</td>
            <td>{{row.item.software_count}}</td>
            <td>{{row.item.deleted_software_count}}</td>
            <td>
              <a :href="row.item.link">link to {{row.item.team}}`s page</a>
            </td>
            <td>
              <a :href="row.item.link_submission">link to {{row.item.team}}`s page</a>
            </td>
          </tr>
      </template>
    </v-data-table>
</template>
  
<script lang="ts">
import { inject } from 'vue'

import { Loading } from '.'
import { get, inject_response, reportError } from '../utils'

interface CountOfTeamSoftware {
  team: string,
  software_count: number,
  deleted_software_count: number,
  link: string,
  link_submission: string,
}

export default {
  name: "overview-registered-team-software",
  components: { Loading },
  props: ['task'],
  data() {
    return {
      loading: true,
      count_of_team_software: [] as CountOfTeamSoftware[],
      rest_url: inject("REST base URL"),
      table_headers: [
        { title: 'Team', key: 'team' },
        { title: 'Software', key: 'software_count' },
        { title: 'Deleted Software', key: 'deleted_software_count' },
        { title: 'Team Page', key: 'link' },
        { title: 'Submission Page', key: 'link_submission' },
      ],
    }
  },
  beforeMount() {
    this.loading = true
    get(this.rest_url + '/api/count-of-team-software/' + this.task.task_id)
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the Overview of Software per Team", "This might be a short-term hiccup, please try again. We got the following error: "))
  }
}
</script>
