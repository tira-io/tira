<template>
    <div class="d-flex" v-if="!paste_mode">
      <!--<v-data-table v-model="selected_runs" :items="filtered_runs" item-value="client_side_identifier" :headers="filtered_headers" show-select hover dense>
      <template v-slot:header.dataset="{ header }">
        <v-autocomplete clearable label="Filter datasets &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="dataset_filter" multiple :items="uniqueElements(topics, 'dataset')"/>
        Dataset
      </template>
  
      <template v-slot:item.run="{ item }">
        <span v-if="!item.system_link">{{item.run}}</span>
        <a v-if="item.system_link" :href="item.system_link" target="_blank">{{item.run}}</a>
      </template>
  
      <template v-slot:header.team="{ header }">
        <v-text-field clearable label="Filter teams &hellip;" variant="underlined" v-model="team_filter"/>
        Team
      </template>
  
      <template v-slot:header.run="{ header }">
        <v-text-field clearable label="Filter systems &hellip;" variant="underlined" v-model="system_filter"/>
        System
      </template>
  
      <template v-slot:footer.prepend>
          <v-select menu-icon="mdi-cog" variant="plain" v-model="selected_headers" item-title="name" item-value="value" :items="available_headers" hide-headers multiple style="max-width: 100px;" class="ma-2">
            <template v-slot:selection="{ item, index }"/>
          </v-select>
        </template>
      </v-data-table>
      -->
    </div>
  
    <div class="d-flex" v-if="paste_mode">
      Please paste a run to render or &nbsp;<a href="javascript:void(0);" @click="paste_run(false)"> select an existing one</a>.
    </div>
  
    <div class="d-flex" v-if="paste_mode">
      <v-row class="justify-center ma-0 pa-0" dense>
        <v-col cols="12" class="ma-0 pa-0">
          <v-autocomplete clearable label="Select dataset" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="dataset_filter" :items="uniqueElements(topics, 'dataset')"/>
        </v-col>
        <v-col cols="12" class="ma-0 pa-0">
          <v-textarea variant="filled" auto-grow label="Paste your run file (Format: <TOPIC> <Q0> <DOCNO> <RANK> <SCORE> <SYSTEM>)" rows="4" row-height="30" shaped :disabled="!dataset_filter" v-model="manual_run" />
        </v-col>
        <v-col cols="12" class="text-caption ma-0 pa-0">
          Rendered with <a href="https://github.com/capreolus-ir/diffir" target="_blank">DiffIR</a>:
        </v-col>
        <v-col cols="12" class="ma-0 pa-0">
          <v-select class="ma-0 pa-0" :items="topics_from_run" item-value="client_side_identifier" item-title="default_text" v-model="selected_topic" label="Topic" @update:modelValue="update_manual_run" :disabled="!dataset_filter || !manual_run"/>
        </v-col>
      </v-row>
    </div>
  
    <div class="d-flex" v-if="paste_mode && manual_run && selected_topic">
      <v-row class="justify-center mx-2">
        <v-col cols="12">
          <diff-ir :run="rendered_manual_run" :docs="manual_docs" :qrels="manual_qrels" :ir_dataset="dataset_id" />
        </v-col>
      </v-row>
    </div>

    <div class="d-flex" v-if="!selected_runs && !paste_mode">
      Please select runs to render above or &nbsp;<a href="javascript:void(0);" @click="paste_run(true)"> paste your run</a>.
    </div>

    <div class="d-flex" v-if="selected_runs">
      <v-row class="justify-center ma-0 pa-0" dense>
        <v-col cols="8" class="text-caption ma-0 pa-0">
          Rendered with <a href="https://github.com/capreolus-ir/diffir" target="_blank">DiffIR</a>:
        </v-col>
        <v-col cols="8" class="ma-0 pa-0">
          <v-select class="ma-0 pa-0" :items="filtered_topics" item-value="identifier" item-title="default_text" v-model="selected_topic" label="Topic" @update:modelValue="fetch_run_data"/>
        </v-col>
      </v-row>
    </div>

    <!--<div class="d-flex" v-if="selected_runs">Reference run: {{ reference_run_id }}</div>-->
    <div class="d-flex" v-if="selected_runs">
      <v-row v-if="topic" class="justify-center mx-2">
        <v-col :cols="columns" v-for="selected_run of selected_runs">
          <serp :run="selected_run" :topic="topic" :topic_details="topic" :reference_run_id="reference_run_id" @activate_run="activate_run"/>
        </v-col>
      </v-row>
    </div>
  </template>
    
  <script lang="ts">
    import { get } from "@/utils"
    import { type Topic, type RunDetails, uniqueElements } from "./utils"
    import Serp from './Serp.vue'
    import DiffIr from './DiffIr.vue'
    import {is_mobile} from "@/main";
    
    
    export default {
      components: {Serp, DiffIr},
      props: {dataset_id: {type: String}, chatnoir_id: {type: String}},
      data: () => ({
        topics: [] as Topic[],
        runs: [] as RunDetails[],
        selected_runs: [] as string[],
        team_filter: null,
        dataset_filter: undefined as string | undefined,
        system_filter: null,
        selected_topic: undefined as string|undefined,
        manual_run: null,
        paste_mode: false,
        selected_headers: is_mobile() ? ['dataset', 'run', 'nDCG@10'] : ['dataset', 'team', 'run', 'nDCG@10', 'P@10'],
        headers: [
          { title: 'Dataset', value: 'dataset', sortable: false},
          { title: 'Team', value: 'team', sortable: false},
          { title: 'System', value: 'run', sortable: false},
          { title: 'nDCG@10',  value: 'nDCG@10', sortable: true},
          { title: 'P@10',  value: 'P@10', sortable: true},
        ],
        available_headers: [
          {name: 'Dataset', value: 'dataset'},
          {name: 'System', value: 'run'},
          {name: 'Team', value: 'team'},
          {name: 'nDCG@10', value: 'nDCG@10'},
          {name: 'P@10', value: 'P@10'},
        ],
        'reference_run_id': undefined as string|undefined,
      }),
      methods: {
        uniqueElements(element: any[], key: string) {
          return uniqueElements(element, key)
        },
        activate_run(run: string) {
          this.reference_run_id = run
        },
        fetch_run_data(i: any) {
            throw Error('Re-Implement...')
            /*get(this.topic['run_details'], this)
          get(this.topic['qrel_details'], this)*/
        },
        update_manual_run(i: any) {
          throw Error('Re-Implement...')
          /*get(this.topic['run_details'], this)
          get(this.topic['qrel_details'], this)*/
        },
        paste_run(i: boolean) {
          this.paste_mode = i
        }
      },
      computed: {
        topic() {
          return this.selected_topic ? this.filtered_topics_map[this.selected_topic] : undefined;
        },
        filtered_topics() {
          let ret = []
          for (let i in this.filtered_topics_map) {
            ret.push(this.filtered_topics_map[i])
          }
  
          return ret
        },
        manual_docs() {
          /*let key = this.topic['run_details'].start + '-' + this.topic['run_details'].end
  
          if (this.cache['run-details.jsonl'][key] !== undefined) {
            return this.cache['run-details.jsonl'][key]['docs'];
          } else {
            return {}
          }*/
         return {}
        },
        rendered_manual_run() {
          let ret = []
          for (let i of (this.manual_run + '\n').split('\n')) {
            let lines = i.split(' ') as string[]
            if (this.selected_topic && lines.length == 6 && lines[0] == this.selected_topic.split('___')[1]) {
              ret.push({'score': lines[4], 'doc_id': lines[2]})
            }
          }
  
          return ret
        },
        manual_qrels() {
          throw Error('Re-Implement')
          /*
          let qrels = this.cache['qrel-details.jsonl'][this.topic['qrel_details'].start + '-' + this.topic['qrel_details'].end]
          let ret = {}
  
          if (qrels !== undefined) {
            for (let i of qrels['qrels']) {
              ret[i['doc_id']] = i['relevance']
            }
          } 
          
          return ret*/
        },
        topics_from_run() {
          let ret = []
          let topics = new Set()
  
          for (let i of (this.manual_run + '\n').split('\n')) {
            topics.add(i.split(' ')[0]);
          }
  
          for (let i of this.filtered_topics) {
            if (i.dataset_id == this.dataset_filter && topics.has(i.qid)) {
              ret.push(i)
            }
           }
  
           return ret;
        },
        filtered_topics_map() : Record<string, Topic> {
          let ret : Record<string, Topic> = {}
          let datasets = new Set()

          for (let run of this.filtered_runs) {
            datasets.add(run['dataset'])
          }

          for (let topic of this.topics) {
            if (datasets.has(topic.dataset_id)) {
              topic = {...topic}
              topic.client_side_identifier = topic.dataset_id + '___' +topic.qid
              ret[topic.client_side_identifier] = topic
            }
          }

          return ret
        },
        filtered_headers() {
          let headers = this.headers
          if (this.selected_headers.length > 0) {
            headers = headers.filter(header => this.selected_headers.includes(header.value))
          }
          /*var add_separator = false
          for (let header of this.headers) {
            header = {...header}
            if (!header.children) {
              continue
            }
            header.children = header.children.filter(child => this.selected_headers.includes(child.value))
  
            if (header.children.length > 0) {
              if (add_separator) {
                headers.push({title: '', value: header.value + '_sep', sortable: false})
              }
              add_separator = true
  
              headers.push(header)
            }
          }*/
  
          return headers
        },
        filtered_runs() {
          let ret = []
  
          for (let run of this.runs) {
            run = {...run}
            run.client_side_identifier = run.dataset + '____' + run.tira_run
            if (this.dataset_filter && !this.dataset_filter.includes(run.dataset)) {
              continue
            }
  
            if (this.team_filter && !run['team'].includes(this.team_filter)) {
              continue
            }
  
            if (this.system_filter && !run['run'].includes(this.system_filter)) {
              continue
            }

            ret.push(run)
          }
  
          return ret;
        },
        columns() {
          if(is_mobile()) {
            return 12
          }
  
          return Math.floor(12 / this.selected_runs.length)
        },
      },
      watch: {
        ir_dataset: function () {}
      },
      beforeMount() {},
    }
  </script>
    