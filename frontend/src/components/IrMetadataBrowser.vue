<template>
  <v-autocomplete
    clearable
    auto-select-first
    label="Browse Metadata &hellip;"
    prepend-inner-icon="mdi-magnify"
    :items="items"  variant="underlined"
    v-model="selected_metadata"
  />
  <p v-if="uuid && selected_metadata">
    <div v-if="resource_plots">
      <h1>Resources</h1>
    </div>

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

      <v-sheet color="transparent" >
        <v-sparkline :line-width="3" :model-value="used_process" stroke-linecap="round" auto-draw label="Process" color="#80D8FF"/>
        <v-sparkline :line-width="3" :model-value="used_system" stroke-linecap="round" auto-draw color="#4CAF50"/>
      </v-sheet>
    </v-card>

    <code-snippet v-if="raw_metadata" title="IR-Metadata" :code="raw_metadata" expand_message=""/>
  </p>
</template>

<script lang="ts">
import { inject } from 'vue'
import {get, reportError} from "@/utils";
import {CodeSnippet} from '../components'


export default {
  name: "ir-metadata-browser",
  components: {CodeSnippet},
  props: ['items', 'uuid'],
  data() {
    return {
      selected_metadata: undefined,
      rest_url: inject("REST base URL"),
      loading: true,
      metadata: undefined,
      raw_metadata: undefined,
      pos: 0
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
        if ((this.pos % keys.length) == k) {
          return keys[k]
        }
      }

      return undefined
    },
    used_process() {
      return this.resource_plots[this.measurement]['process']
    },
    used_system() {
      return this.resource_plots[this.measurement]['system']
    },
    resource_plots() {
      if (!this.metadata || !('resources' in this.metadata)) {
        return undefined
      }
      let ret: Record<string, any> = {}
      for (let k of Object.keys(this.metadata['resources'])) {
        let resources = this.metadata['resources'][k]
        if (!resources || !('used process' in resources) || !('used system' in resources)) {
            continue
        }

        let used_process = resources['used process']['timeseries']['values']
        let used_system = resources['used system']['timeseries']['values']
        
        ret[k] = {'process': used_process, 'system': used_system}
      }

      return ret
    }
  }
}
</script>
