<template>
  <tira-breadcrumb />

  <h3 class="text-h3 py-5" v-if="team === undefined">Published Systems</h3>
  <h3 class="text-h3 py-5" v-if="team !== undefined">Published Systems by {{ team }}</h3>
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

      <template #item.team="{ item }">
        <router-link :to="'/systems/' + item.team">{{ item.team }}</router-link>
      </template>

      <template #item.name="{ item }">
        <router-link :to="'/systems/' + item.team + '/' + item.name ">{{ item.name }}</router-link>
      </template>

      <template #item.tasks="{ item }">
        <span v-for="task in item.tasks">
          <router-link :to="'/task-overview/' + task">{{ task }}</router-link>
        </span>
      </template>

    </v-data-table>
  </div>
</template>
  
<script lang="ts">
  import { inject } from 'vue'
  
  import { get_from_archive, reportError, type UserInfo, type SystemInfo } from './utils';
  import { Loading, TiraBreadcrumb } from './components'
  
  export default {
    name: "systems",
    components: { Loading, TiraBreadcrumb },
    data() {
      return {
        userinfo: inject('userinfo') as UserInfo,
        team: undefined as undefined | string,
        query: undefined as undefined | string,
        systems: [] as SystemInfo[],
        headers: [
        { title: 'Team', value: 'team' },
        { title: 'System', key: 'name' },
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
      this.query = this.$route.query.query as undefined | string
      if (this.$route.params.team) {
        this.team = this.$route.params.team as undefined | string
      }

      get_from_archive('/v1/systems/all')
        .then(
            (result) => { 
              if (this.team) {
                result = (result as SystemInfo[]).filter(i => i.team.toLowerCase() == this.team?.toLowerCase())
              }

              this.$data.systems = result
            }
        )
        .catch(reportError("Problem While Loading the Overview of the Systems.", "This might be a short-term hiccup, please try again. We got the following error: "))
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
  