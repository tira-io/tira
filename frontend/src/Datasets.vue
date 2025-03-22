<template>
    <tira-breadcrumb />
    
    <h3 class="text-h3 py-5">Datasets</h3>
    <div class="py-5"></div>
    <v-skeleton-loader type="card" v-if="datasets === undefined"/>

    <div v-if="datasets !== undefined">
      <div class="d-flex">
        <v-responsive min-width="220px" id="task-search">
          <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="query" />
        </v-responsive>
      </div>
      <div class="py-2"></div>

      <v-data-table :headers="headers_xs" :items="datasets" :itemsPerPage="10" :search="query" density="compact" fixed-footer show-expand>
        <template #item.display_name="{ item }">
            <router-link v-if="item.default_task" :to="'/task-overview/' + item.default_task + '/' + item.dataset_id" style="text-decoration: none !important;">{{ item.display_name }}</router-link>
            <span v-if="!item.default_task">{{ item.display_name }}</span>
        </template>
        <template #item.default_task="{ item }">
            <router-link v-if="item.default_task" :to="'/task-overview/' + item.default_task + '/' + item.dataset_id" style="text-decoration: none !important;">{{ item.default_task_name }}</router-link>
            <span v-if="!item.default_task">No Task</span>
        </template>
        <template #item.ir_datasets_id="{ item }">
            <div v-for="[name, url] of Object.entries(ir_datasets_urls(item))">
              <a :href="url" style="text-decoration: none !important;" target="_blank">{{name}}</a>
            </div>
        </template>
        <template #item.search="{ item }">
            <a v-if="chatnoir_url(item)" :href="chatnoir_url(item)" style="text-decoration: none !important;" target="_blank">ChatNoir</a>
        </template>
        <template v-slot:expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length">
              <div v-if="!item.description">No description is available.</div>
              <div v-if="item.description" v-html="item.description"/>
              <directory-inspector :file_listing="item.file_listing"/>
            </td>
          </tr>
        </template>
        <template #item.type="{ item }">
          <span v-if="item.is_confidential">Private Test</span>
          <span v-if="!item.is_confidential">Public Training</span>
        </template>
        <template #item.mirrors="{ item }">
          <p v-for="[k, v] of Object.entries(mirrored_resources(item.mirrors))">
            <a :href="v + ''"  style="text-decoration: none !important;" target="_blank">{{k}}</a>
          </p>
          <p v-for="[k, v] of Object.entries(tira_resources(item))">
            <a :href="v + ''"  style="text-decoration: none !important;" target="_blank">{{k}}</a>
          </p>
        </template>
      </v-data-table>
    </div>
  </template>
  
  <script lang="ts">
  import { inject } from 'vue'
  
  import { get_from_archive, reportError, chatNoirUrl, irDatasetsUrls, type UserInfo, type DatasetInfo } from './utils';
  import { Loading, TiraBreadcrumb, DirectoryInspector } from './components'
  
  export default {
    name: "datasets",
    components: { Loading, TiraBreadcrumb, DirectoryInspector },
    data() {
      return {
        userinfo: inject('userinfo') as UserInfo,
        query: undefined as string|undefined,
        datasets: [] as DatasetInfo[],
        headers_xs: [
        { title: 'Dataset', key: 'display_name' },
        { title: 'Task', value: 'default_task' },
        { title: 'Type', value: 'type' },
        { title: 'TIRA ID', key: 'id' },
        { title: 'IR Datasets ID', key: 'ir_datasets_id' },
        { title: 'Search', key: 'search' },
        { title: 'Download', key: 'mirrors' },
      ],
      }
    },
    methods: {
      chatnoir_url(dataset: DatasetInfo) { return chatNoirUrl(dataset)},
      ir_datasets_urls(dataset: DatasetInfo) { return irDatasetsUrls(dataset)},
      mirrored_resources(mirrors: any) {
        let ret : Record<string, string> = {}
        for (let resource_type of Object.keys(mirrors)) {
          for (let resource_name of Object.keys(mirrors[resource_type])) {
            if (resource_type.includes('md5_sum') || resource_type.includes('subdirectory') || resource_type.includes('rename_to')) {
              continue
            }
            ret[resource_name + ' (' + resource_type + ')'] = mirrors[resource_type][resource_name]
          }
        }

        return ret
      },
      tira_resources(item: any) {
        let ret : Record<string, string> = {}
        if (item.dataset_id && !item.is_confidential && item.mirrors && Object.getOwnPropertyNames(this.mirrored_resources(item.mirrors)).length == 0) {
          ret['Inputs'] = "https://www.tira.io/data-download/" + (item.dataset_id.endsWith('-training') ? 'training' : 'test') + '/input-/' + item.dataset_id + '.zip'
          ret['Truths'] = "https://www.tira.io/data-download/" + (item.dataset_id.endsWith('-training') ? 'training' : 'test') + '/input-truth/' + item.dataset_id + '.zip'
        }
        
        return ret
      }
    },
    beforeMount() {
      this.query = this.$route.query.query as string|undefined
      get_from_archive('/v1/datasets/all')
        .then(
            (result) => { this.$data.datasets = result.filter((i: DatasetInfo) => i.id && i.id.length > 2)}
        )
        .catch(reportError("Problem While Loading the Overview of the Datasets.", "This might be a short-term hiccup, please try again. We got the following error: "))
    },
    watch: {
      query(old_value, new_value) {
        if (this.query) {
          this.$router.push({ path: 'datasets', query: { query: this.query }})
        } else {
          this.$router.push({ path: 'datasets', query: { }})
        }
      },
    },
  }
  
  </script>
  