<template>
    <div class="row justify-content-center" id="runName">
      <div class="col">
        <h6 id="Run1Name" style="text-align: center;"></h6>
      </div>
      <div class="col">
        <h6 id="Run2Name" style="text-align: center;"></h6>
      </div>
    </div>
    <div class="row" v-for="run in rendered_run">
      <div class="card" style="width: 95%" :href="chatnoir_url(run.doc_id)" target="_blank">
        <div class="card-header">
          <div class="docid" :style="'right: 0px; width=100%; background-color: ' + run.relevanceColor"><div class="docid-value">{{ run.doc_id }}</div></div>
          <h6 class="badge badge-info" title="Relevant" :style="'cursor: help; background-color:' + run.relevanceColor">Rel: {{run.relevance}}</h6>
          <h6 class="badge">Score: {{run.score}}</h6>
          <div class="snippet">
            <div><span style="color: #999;" v-html="run.snippet"/></div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script lang="ts">
  import { chatNoirUrl, type DatasetInfo } from '../utils'

  function markup(text: any, weights: any) {
    weights = weights.filter(function (e: any) {
      return (e[2] > 0 || typeof e[2] === 'string');
    })
  
    if (weights.length === 0) {
      return '<div>' + text + '</div>'
    }
  
    var ret = text.substring(0, weights[0][0])
    for (let i in weights) {
      let weight = weights[parseInt(i)]
      if (typeof weight[2] === 'string') {
        var weightColor = weight[2];
      } else {
        var weightColor = 'rgba(255, 237, 140, ' + weight[2].toString() + ')';
      }
  
      ret += '<mark background="' + weightColor + ' run1="' + weight[3] + '" run2="0">' + text.substring(weight[0], weight[1]) + '</mark>'
  
      if (i + 1 < weights.length) {
        ret += '<span>' + text.substring(weight[1], weights[i + 1][0]) + '</span>'
      }
    }
  
    ret += '<span>' + text.substring(weights[weights.length - 1][1], text.length) + '</span>'
  
    return '<div><span>' + ret + '</span></div>'
  }
  
  export default {
    name: "diff-ir",
    props: ['run', 'reference_run', 'docs', 'ir_dataset', 'qrels', 'chatnoir_id'],
    data() {
      return {
        allWeightsA: {},
        allWeightsB: {},
        mergedWeights: {},
        COLOR_A: '236, 154, 8',
        COLOR_B: '121, 196, 121',
        meta: {
          relevanceColors: {
            '0': "red",
            '1': "green",
            '2': "green",
            '3': "green",
          } as Record<string, string>,
          'qrelDefs': {0: 'Not Relevant', 1: 'Related', '2': 'Relevant', '3': 'Highly Relevant'},
        },
      }
    },
    methods: {
        chatnoir_url(docid: string) {return chatNoirUrl({'chatnoir_id': this.chatnoir_id} as DatasetInfo, docid)}
    },
    computed: {
      rendered_run() {
        var ret = []
        for(let i of this.run) {
          let doc = this.docs[i.doc_id]
          let judgment = 'Unjudged'
          if (doc === undefined) {
            ret.push({'score': i['score'], 'doc_id': i['doc_id'], 'snippet': 'no snippet available', 'relevance': judgment})
            continue
          }
  
          if (this.qrels && this.qrels[i.doc_id] !== undefined) {
            judgment = this.qrels[i.doc_id]
          }
  
          let relevanceColor : string | undefined = undefined
          if (judgment in this.meta.relevanceColors) {
            relevanceColor = this.meta.relevanceColors[judgment]
          }
  
          ret.push({
            'score': i['score'],
            'doc_id': i['doc_id'],
            'snippet': markup(doc['snippet'], doc['weights']),
            'relevance': judgment,
            'relevanceColor': relevanceColor
          })
        }
  
        return ret
      }
    }
  }
  </script>
  
  
  <style scoped>
      .card {
        margin: 5px !important;
      }
  
      .highlight {
        background-color: #ffffd3;
      }
  
      #DocumentOverlay {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: rgba(0, 0, 0, .25);
      }
  
      #DocumentDetails {
        position: fixed;
        top: 60px;
        left: 10%;
        right: 10%;
        bottom: 60px;
        background-color: white;
        padding: 20px;
        border: 1px solid rgba(0, 0, 0, .125);
        border-radius: 0.25rem;
        box-shadow: 0 0 16px black;
        overflow: auto;
      }
  
      .close-overlay {
        position: absolute;
        top: 4px;
        right: 4px;
        border-radius: 100%;
        background-color: #111;
        font-size: 17px;
        padding: 9px;
        color: white;
        width: 30px;
        height: 30px;
        text-align: center;
        font-weight: normal;
        line-height: 11px;
        cursor: pointer;
      }
  
      .docid {
        background-color: rgb(224, 135, 55);
        position: absolute;
        top: 0;
        bottom: 0;
        width: 20px;
        overflow: hidden;
        margin-bottom: 0;
        border-radius: 0;
        font-weight: normal;
        white-space: nowrap;
      }
  
      .docid-value {
        transform: rotate(90deg);
        font-size: 0.7em;
        padding-left: 8px;
      }
  
      .fields th {
        vertical-align: top;
        text-align: right;
        padding-right: 12px;
        color: #999;
        font-weight: normal;
      }
  
      #query-container {
        max-width: 600px;
        border: 1px solid #999;
        border-radius: 0.25rem;
        margin: 20px auto;
        padding: 10px;
      }
  
      .other-rank {
        font-size: 1.2em;
        display: inline-block;
        width: 20px;
        margin-top: 46px;
        margin-left: 3px;
        margin-right: 3px;
        cursor: help;
      }
  
      mark {
        padding: 0;
        font-weight: bold;
      }
  
      .snippet {
        font-size: 0.9em;
        line-height: 1.2;
      }
  
      .elip {
        text-align: center;
        margin: 16px;
        color: gray;
      }
  
      .doc-info {
        white-space: nowrap;
      }
  
      .card-header {
        min-height: 128px;
        cursor: pointer;
      }
  
      .swatch {
        display: inline-block;
        width: 16px;
        height: 16px;
        vertical-align: middle;
      }
  
      .form-group {
        width: 150px;
        height: 20px;
        padding-left: 10px;
        padding-top: 10px;
      }
  
      .nobackground {
        background: transparent !important;
        font-weight: normal;
      }
      .styled-table {
        margin-left: 0px;
        margin-top: 10px;
        border-collapse: collapse;    
        font-size: 0.9em;
        /* font-family: sans-serif;       */
        min-width: 350px;      
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
      }
      .styled-table thead tr {
        background-color: #17a2b8;
        color: #ffffff;
        text-align: left;
      }    
      /* .styled-table th, */
      .styled-table td {
        /* padding: 12px 15px; */
        text-align: center;
      }    
      .styled-table tbody tr {
        color: #ffffff;
      }
      /*
      .styled-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
      } */
  
      .styled-table tbody tr:last-of-type {
        border-bottom: 2px solid #009879;
      }
  
      #ranking-summary ul li span {
        margin-right: 5px;
      }    
  </style>