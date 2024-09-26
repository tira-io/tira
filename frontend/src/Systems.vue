<template>
  <tira-breadcrumb />

  <h3 class="text-h3 py-5">Published Systems</h3>
  We show systems that have at least one positively validated and published submission.
  <div class="py-5"></div>
  <v-skeleton-loader type="card" v-if="systems === undefined"/>

  <div v-if="systems !== undefined">
    <div class="d-flex">
      <v-responsive min-width="220px" id="task-search">
        <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="query" />
      </v-responsive>
    </div>
    <div class="py-2"></div>

    <v-data-table :headers="headers" :items="systems" :itemsPerPage="10" :search="query" density="compact" fixed-footer>

    </v-data-table>
  </div>
</template>
  
<script lang="ts">
  import { inject } from 'vue'
  
  import { get, reportError, fetchUserInfo, type UserInfo } from './utils';
  import { Loading, TiraBreadcrumb } from './components'
  
  export default {
    name: "systems",
    components: { Loading, TiraBreadcrumb },
    data() {
      return {
        userinfo: { role: 'guest', organizer_teams: [] } as UserInfo,
        query: undefined,
        systems: undefined,
        headers: [
        { title: 'System', key: 'name' },
        { title: 'Team', value: 'team' },
        { title: 'Type', value: 'type' },
        { title: 'Tasks', key: 'tasks' },
      ],
      }
    },
    methods: {
      logData(toLog: any) {
        console.log(toLog)
      }
    },
    beforeMount() {
      this.query = this.$route.query.query
      get(inject("REST base URL") + '/v1/systems/')
        .then(
            (result) => { this.logData(result); this.$data.systems = result}
        )
        .catch(reportError("Problem While Loading the Overview of the Systems.", "This might be a short-term hiccup, please try again. We got the following error: "))
      fetchUserInfo().then((result) => { this.$data.userinfo = result })
    },
    watch: {
      query(old_value, new_value) {
        if (this.query) {
          this.$router.push({ path: 'systems', query: { query: this.query }})
        } else {
          this.$router.push({ path: 'systems', query: { }})
        }
      },
    },
  }
  
  </script>
  