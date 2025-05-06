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
        <Scatter :data="resource_plots_chart" :options="chart_options"/>
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
  Legend,

} from 'chart.js'
import { Scatter} from 'vue-chartjs'

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale)


export default {
  name: "ir-metadata-browser",
  components: {CodeSnippet, Scatter},
  props: ['items', 'uuid', "vm_id", "dataset_id", "run_id", "task_id"],
  data() {
    return {
      selected_metadata: undefined,
      rest_url: inject("REST base URL"),
      loading: true,
      metadata: undefined,
      raw_metadata: undefined,
      pos: 0,
      chart_options: {
        showLine: true,
        scales: {
          x: {
            grid: {display: false},
            ticks: {
              callback: function(value: any, index: any, ticks: any) {
                if (value < (3*60*1000)) {
                  return (value/1000) + 's';
                } else {
                  return (value/(1000*60)) + 'min';
                }
              }
            }
          },
          y: {
            grid: {display: false},
            ticks: {
              callback: function(value: any, index: any, ticks: any) {
                if (value < (5*1024)) {
                  return value;
                } else if (value < (1024*1024)){
                  return (value/(1024)).toFixed(1) + 'MB';
                } else {
                  return (value/(1024*1024)).toFixed(1) + 'GB';
                }
              }
            }
          }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context: any) {
                        let label = context.dataset.label || '';

                        if (label) {
                          if (context.parsed.x !== null) {
                            let x = context.parsed.x
                            if (x < (3*60*1000)) {
                              x = (Math.round((x/100))/10) + 's';
                            } else {
                              x = (Math.round(x/(100*60))/10) + 'min';
                            }

                            label += ' (' + x + ')'
                          }

                          label += ': ';
                        }
                        if (context.parsed.y !== null) {
                          let y = context.parsed.y 

                          if (y < (5*1024)) {
                            y = y
                          } else if (y < (1024*1024)){
                            y = (y/(1024)).toFixed(1) + 'MB';
                          } else {
                            y = (y/(1024*1024)).toFixed(1) + 'GB';
                          }
                          label += y
                        }
                        return label;
                    }
                }
            }
        }
      },
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
      let remote_url = this.rest_url + "/task/" + this.task_id + "/user/" + this.vm_id + "/dataset/" + this.dataset_id + "/view/" + this.run_id
      console.log(remote_url)
      
      if (this.vm_id && this.dataset_id && this.run_id && this.task_id) {
        
      } else if (!this.uuid || this.uuid + '' === 'undefined' || !this.selected_metadata || this.selected_metadata + '' === 'undefined') {
        return
      } else {
        remote_url = this.rest_url + '/v1/anonymous/view/' + this.uuid
      }

      this.loading = true

      get(remote_url + '/metadata/' + this.selected_metadata)
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
      if (!p && !s) {
        return undefined;
      }
      let datasets: any[] = []
      if (p) {
        datasets.push({label: 'Process', backgroundColor: '#80D8FF', borderColor: '#80D8FF', data: p})
      }
      if (s) {
        datasets.push({label: 'System', backgroundColor: '#4CAF50', borderColor: '#4CAF50', data: s})
      }
      return {
        datasets: datasets
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
        if (!resources || (!('process' in resources) && !('system' in resources))) {
            continue
        }

        ret[k] = resources
      }

      return ret
    }
  }
}
</script>
