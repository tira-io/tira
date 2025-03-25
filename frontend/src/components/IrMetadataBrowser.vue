<template>
  <v-autocomplete
    clearable
    auto-select-first
    label="Browse Metadata &hellip;"
    prepend-inner-icon="mdi-magnify"
    :items="items"  variant="underlined"
    v-model="selected_metadata"
  />
  <v-skeleton-loader type="card" v-if="loading && selected_metadata"/>

  <code-snippet v-if="!loading && selected_metadata && raw_metadata" title="IR-Metadata (Preview)" :code="raw_metadata" expand_message=""/>

  <p v-if="!loading && uuid && selected_metadata">
    <v-card v-if="measurement" class="mx-auto" color="surface-light">
      <template v-slot:prepend>
        <v-btn class="align-self-start" icon="mdi-arrow-left-thick" size="34" variant="text" @click="pos = pos - 1"/>
      </template>

      <template v-slot:title>
        <div class="text-caption text-uppercase"><h1>{{ measurement }} of <span style="color: #80D8FF;">Process</span>/<span style="color: #4CAF50;">System</span> </h1></div>
      </template>

      <template v-slot:append>
        <v-btn class="align-self-start" icon="mdi-arrow-right-thick" size="34" variant="text" @click="pos = pos + 1"/>
      </template>

      
      <div v-if="resource_plots && resource_plots_chart">
        <Line :data="resource_plots_chart" :options="chart_options"/>
      </div>
    </v-card>
  </p>
</template>

<script lang="ts">
import { inject } from 'vue'
import {get, reportError} from "@/utils";
import {CodeSnippet} from '../components'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale)


export default {
  name: "ir-metadata-browser",
  components: {CodeSnippet, Line},
  props: ['items', 'uuid'],
  data() {
    return {
      selected_metadata: undefined,
      rest_url: inject("REST base URL"),
      loading: true,
      metadata: undefined,
      raw_metadata: undefined,
      pos: 0,
      chart_options: {
        scales: {
          x: {grid: {display: false}},
          y: {grid: {display: false}}
        }
      }
    }
  },
  watch: {
    selected_metadata(old_value, new_value) {
      this.loadData()
    }
  },
  methods: {
    loadData() {
      this.loading = false
      this.metadata = undefined
      this.raw_metadata = undefined
      if (!this.uuid || this.uuid + '' === 'undefined' || !this.selected_metadata || this.selected_metadata + '' === 'undefined') {
        return
      }

      this.loading = true
      get(this.rest_url + '/v1/anonymous/view/' + this.uuid + '/metadata/' + this.selected_metadata)
      .then(message => {
        this.loading = false
        this.metadata = message.metadata
        this.raw_metadata = message.raw_metadata
      })
      .catch(reportError("Problem While Loading the Metadata.", "This might be a short-term hiccup, please try again. We got the following error: "))
    }
  },
  computed: {
    measurement() {
      if (!this.resource_plots) {
        return undefined
      }
      let keys = Object.keys(this.resource_plots)
      if (this.pos < 0) {
        this.pos = keys.length - 1
      }

      for (let k in keys) {
        if ((this.pos % keys.length) + '' == '' + k) {
          return keys[k]
        }
      }

      return undefined
    },
    resource_plots_chart() {
      let p = this.used_process
      let s = this.used_system
      if (!p || ! s) {
        return undefined;
      }
      let labels: string[] = Array.from({ length: s.length }, () => "");

      return {
        labels: labels,
        datasets: [
          {label: 'Process', backgroundColor: '#80D8FF', borderColor: '#80D8FF', data: p},
          {label: 'System', backgroundColor: '#4CAF50', borderColor: '#4CAF50', data: s},
        ]
      }
    },
    used_process() {
      if (!this.measurement || !this.resource_plots) {
        return undefined
      }

      return this.resource_plots[this.measurement]['process']
    },
    used_system() {
      if (!this.measurement || !this.resource_plots) {
        return undefined
      }

      return this.resource_plots[this.measurement]['system']
    },
    resource_plots() {
      if (!this.metadata || !('resources' in this.metadata)) {
        return undefined
      }

      let ret: Record<string, any> = {}
      for (let k of Object.keys(this.metadata['resources'])) {
        let resources = this.metadata['resources'][k]
        if (!resources || !('process' in resources) || !('system' in resources)) {
            continue
        }

        ret[k] = resources
      }

      return ret
    }
  }
}
</script>
