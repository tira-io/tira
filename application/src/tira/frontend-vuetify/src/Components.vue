<template>
    <v-container class="text-center">
      <section>
        <h1 class="text-h3 text-sm-h3 py-4">Components available in TIREx</h1>
        <p class="mx-auto py-4 tira-explanation">
          lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.
        </p>
    </section>
    </v-container>

        <v-row class="justify-center mx-2">
          <v-col cols="4">
            <v-select v-model="component_types" :items="available_component_types" label="Select Types" multiple hint="Which components do you want to see?"/>
          </v-col>
          <v-col cols="4">
            <v-select v-model="focus_types" :items="available_focus_types" label="Select Your Focus" multiple hint="Which aspect should be fulfilled by a component?"/>
          </v-col>
          <v-col cols="4">
            <v-responsive min-width="220px" id="task-search">
              <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify"
                      variant="underlined" v-model="component_filter"/>
             </v-responsive>
          </v-col>
        </v-row>

        <v-row class="justify-center mx-2" v-for="(row, _) of vectorizedComponents">
          <v-col v-for="(cell, i) in row" cols="2">
            <v-menu>
              <template v-slot:activator="{ props }">
                <v-card v-bind="props" v-if="cell && cell?.display_name" class="mx-auto" :max-width="max_width" :color="cell?.color" variant="tonal" style="cursor: pointer;">
                  <v-card-item><span class="text-h6 mb-1">{{ cell?.display_name }}</span><span style="font-size: .7em;" v-if="cell?.collapsed">&nbsp;&nbsp;(+&nbsp;&nbsp;{{ cell.collapsed }})</span></v-card-item>
                </v-card>
              </template>

              <v-list>
                <v-list-item>
                  <v-list-item-title><a href="/task-overview/ir-benchmarks/">Submission in TIREx</a></v-list-item-title>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title><a href="https://github.com/webis-de/ir-pad/blob/public/tutorials/tutorial-02-stopword-lists.ipynb" target="_blank">Tutorial Notebook</a></v-list-item-title>
                </v-list-item>
                <v-list-item v-if="!cell?.collapsed">
                  <v-list-item-title>Collapse items</v-list-item-title>
                </v-list-item>
                <v-list-item v-if="cell?.collapsed">
                  <v-list-item-title>Expand {{ cell.collapsed }} items </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>      
          </v-col>
        </v-row>
</template>


<script lang="ts">
export default {
  name: "components",
  data() {
    return {
      max_width: 1500,
      components: [
        {'display_name': 'Dataset', 'components': [{'display_name': 'ClueWeb09'}, {'display_name': 'ClueWeb12'}, {'display_name': 'ClueWeb22'}]},
        {'display_name': 'Document Processing', 'components': [{'display_name': 'Keyphrase Extraction'}, {'display_name': 'Stemming'}]},
        {'display_name': 'Query Processing', 'components': [{'display_name': 'Query Segmentation'}]},
        {'display_name': 'Retrieval', 'components': [{'display_name': 'BM25'}, {'display_name': 'TF-IDF'}, {'display_name': 'PL2'}]},
        {'display_name': 'Re-Ranking', 'components': [{'display_name': 'monoT5'}]},
        {'display_name': 'Evaluation', 'components': [{'display_name': 'nDCG'}]}
      ],
      colors: {
        'Dataset': 'green', 'Document Processing': 'yellow-lighten-1',
        'Query Processing': 'yellow-darken-4', 'Retrieval': 'cyan-lighten-1',
        'Re-Ranking': 'cyan-darken-3', 'Evaluation': 'blue-grey-lighten-1'
      } as {[key: string]: string},
      component_filter: null,
      component_types: [],
      available_component_types: ['Code', 'TIREx Submission', 'Tutorial'],
      focus_types: [],
      available_focus_types: ['Precision', 'Recall'],
    }
  },
  methods: {
    colorOfComponent(c:string) {
      return this.colors[c] ?? "grey"
    },
  },
  computed: {
    vectorizedComponents() {
      let ret: [{display_name?: string|undefined, color?: string|undefined, collapsed?: number|undefined}[]] = [[{}, {}, {}, {}, {}, {}]]

      for (let i in this.components) {
        let c = this.components[i]
        ret[0][i] = {'display_name': c.display_name}

        for (let j=0; j< c.components.length; j++) {
          if (ret.length <= 1+j) {
            ret.push([{}, {}, {}, {}, {}, {}])
          }

          ret[1+j][i] = {'display_name': c.components[j].display_name, 'color': this.colorOfComponent(c.display_name), 'collapsed': 3}
        }
      }
      
      return ret
    }
  }
}
</script>