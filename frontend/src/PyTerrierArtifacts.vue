<template>
    <tira-breadcrumb />
    
    <h3 class="text-h3 py-5">PyTerrier Artifacts (alpha)</h3>
    <p>This is an proof of concept integration of TIREx into the PyTerrier artifacts API, currently in alpha version. The goal is to condense this list into <router-link to="/tirex/components">a dashboard like this</router-link>.</p>
    <div class="py-5"></div>
    <v-skeleton-loader type="card" v-if="loading"/>

    <div v-if="!loading">
      <div class="d-flex">
        <v-responsive min-width="220px" id="task-search">
          <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="query" />
        </v-responsive>
      </div>
      <div class="py-2"></div>

      <v-data-table :items="verified_approaches" :itemsPerPage="10" :search="query" density="compact" fixed-footer>
      </v-data-table>
    </div>
  </template>
  
  <script lang="ts">
  import { inject } from 'vue'
  
  import { get_from_archive, reportError, type UserInfo, type DatasetInfo, type SystemInfo } from './utils';
  import { Loading, TiraBreadcrumb, DirectoryInspector } from './components'
  
  interface VerifiedApproach {
    dataset_id: string;
    team: string;
    approach: string;
    task: string;
    type: string;
}

  export default {
    name: "datasets",
    components: { Loading, TiraBreadcrumb, DirectoryInspector },
    data() {
      return {
        loading: true,
        userinfo: inject('userinfo') as UserInfo,
        query: undefined as string|undefined,
        datasets: [] as DatasetInfo[],
        systems: [] as SystemInfo[],
        headers_xs: [
        { title: 'Dataset', key: 'dataset_id' },
        { title: 'Type', value: 'type' },
        { title: 'Search', key: 'search' },
        { title: 'Download', key: 'mirrors' },
      ],
      }
    },
    beforeMount() {
      this.query = this.$route.query.query as string|undefined
      this.loading = true
      get_from_archive('/v1/datasets/all')
        .then(
            (result) => { 
              this.$data.datasets = result.filter((i: DatasetInfo) => i.id && i.id.length > 2)

              get_from_archive('/v1/systems/all')
                .then(
                (result) => {
                  this.$data.systems = result
                  this.loading = false
                })
            }
        )
        .catch(reportError("Problem While Loading the Overview of the Datasets.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    computed: {
      verified_approaches() { 
        let ret: VerifiedApproach[] = []

        for (let i of this.systems) {
            if (!i.verified_outputs) {
                continue
            }

            for (let dataset_id of Object.keys(i.verified_outputs)) {
                for (let processing_type of Object.keys(i.verified_outputs[dataset_id])) {
                    ret.push({"dataset_id": dataset_id, "team": i.team, "approach": i.name, "task": i.tasks[0], "type": processing_type})
                }
            }
        }

        return ret },
    },
    watch: {
      query(old_value, new_value) {
        if (this.query) {
          this.$router.push({ query: { query: this.query }})
        } else {
          this.$router.push({ query: { }})
        }
      },
    },
  }
  
  </script>
  