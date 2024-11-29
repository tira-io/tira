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

      <v-data-table :headers="headers_xs" :items="datasets" :itemsPerPage="10" :search="query" density="compact" fixed-footer>
        <template #item.display_name="{ item }">
            <a v-if="item.default_task" :href="'/task-overview/' + item.default_task.task_name + '/' + item.dataset_id" style="text-decoration: none !important;">{{ item.display_name }}</a>
            <span v-if="!item.default_task">{{ item.display_name }}</span>
        </template>
        <template #item.default_task="{ item }">
          <a v-if="item.default_task" :href="'/task-overview/' + item.default_task.task_name" style="text-decoration: none !important;">{{ item.default_task.task_name }}</a>
            <span v-if="!item.default_task"> No Task </span>
        </template>
        <template #item.ir_datasets_id="{ item }">
            <a v-if="item.ir_datasets_id" :href="'https://ir-datasets.com/' + item.ir_datasets_id.split('/')[0] + '.html#' + item.ir_datasets_id" style="text-decoration: none !important;" target="_blank">{{item.ir_datasets_id}}</a>
        </template>
        <template #item.search="{ item }">
            <a v-if="item.chatnoir_id" :href="'https://chatnoir.web.webis.de/?index=' + item.chatnoir_id" style="text-decoration: none !important;" target="_blank">ChatNoir</a>
        </template>
        <template #item.type="{ item }">
          Public Training
        </template>
        <template #item.mirrors="{ item }">
          <!--<a v-if="item.default_task" href="https://chatnoir.web.webis.de" style="text-decoration: none !important;">Zenodo</a>
          <a v-if="!item.default_task" href="https://chatnoir.web.webis.de" style="text-decoration: none !important;">Huggingface</a>-->
        </template>
      </v-data-table>
    </div>
  </template>
  
  <script lang="ts">
  import { inject } from 'vue'
  
  import { get, reportError, type UserInfo, type DatasetInfo } from './utils';
  import { Loading, TiraBreadcrumb } from './components'
  
  export default {
    name: "datasets",
    components: { Loading, TiraBreadcrumb },
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
      logData(toLog: any) {
        console.log(toLog)
      }
    },
    beforeMount() {
      this.query = this.$route.query.query as string|undefined
      get(inject("Archived base URL") + '/v1/datasets/all')
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
  