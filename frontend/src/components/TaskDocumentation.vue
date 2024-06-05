<template>
  <v-card>
    <v-toolbar color="primary" title="TIREx Submission Documentation"/>
    <div class="px-6">
    <h2>Existing Starters</h2>
    <p>You can start your submission following several starters that implement various retrieval approaches. Please find an complete overview of starters for five frameworks <a href="">here</a>, including an <a href="">Jupyter notebook that retrieves with BM25</a>.</p>

    <h2>Data Interface</h2>
    <p>Your retrieval approaches must be compatible with <a href="">ir_datasets</a> for data wrangling. This data format is specified as:</p>
    <v-tabs v-model="tab" show-arrows>
      <v-tab key="1" value="1">Full-Rank with ir_datasets</v-tab>
      <v-tab key="2" value="2">Re-Rank with ir_datasets</v-tab>
      <v-tab key="3" value="3">Full-Rank Standalone</v-tab>
      <v-tab key="4" value="4">Re-Rank Standalone</v-tab>
    </v-tabs>

    <v-card-text>
      <v-window v-model="tab" :touch="{left: () => {}, right: () => {}}">
        <v-window-item value="1">
          <p>The following code assumes you have installed the `tira` utility (<v-code tag="span">pip3 install tira</v-code>) in your Docker image. TIRA executes software in a sandbox. This ir_datasets integration loads the data provided by TIRA if executed in the sandbox, otherwise the specified data.</p>
          <v-code tag="pre">
            from tira.third_party_integrations import ir_datasets<br>
            dataset = ir_dataset.load("DATASET-ID")<br>
            for doc in dataset.docs_iter():<br>
                # doc.doc_id, doc.default_text(), ...<br>
            for query in dataset.queries_iter():<br>
                # query.query_id, query.default_text(), ...
          </v-code>
        </v-window-item>

        <v-window-item value="2">
            <p>The following code assumes you have installed the `tira` utility (<v-code tag="span">pip3 install tira</v-code>) in your Docker image. TIRA executes software in a sandbox. This ir_datasets integration loads the data provided by TIRA if executed in the sandbox, otherwise the specified data.</p>
          <v-code tag="pre">
            from tira.third_party_integrations import ir_datasets<br>
            rerank_data = ir_dataset.load_rerank_data("DATASET-ID")<br>
            for query_id, query, doc_id, doc in rerank_data:<br>
                # query.defautl_text, ..., doc.default_text(), ...
          </v-code>
        </v-window-item>

        <v-window-item value="3">
          <v-code tag="pre">
            import json<br>
            import os<br>
            input_directory = os.environ["inputDir"]
            for doc in open(f'{input_directory}'/documents.jsonl'):<br>
                # json.parse(doc)<br>
            for query in open(f'{input_directory}'/queries.jsonl'):<br>
                # json.parse(query)
          </v-code>
        </v-window-item>

        <v-window-item value="4">
          <v-code tag="pre">
            import json<br>
            import os<br>
            input_directory = os.environ["inputDir"]
            for query_document_pair in open(f'{input_directory}'/re-rank.jsonl'):<br>
                # json.parse(query_document_pair)
          </v-code>
        </v-window-item>
      </v-window>
    </v-card-text>

    
    </div>
  </v-card>
</template>
  
<script lang="ts">
  export default {
    name: "task-documentation",
    props: ['task'],
    data() { return {
        tab: null,
      }
    }
  }
</script>
