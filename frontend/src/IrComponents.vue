<template>
  <v-container class="text-center">
    <v-img class="mx-auto" height="300px" max-width="100%" width="300px" src="@/assets/tirex-modules.jpg"/>
    <section>
      <h1 class="text-h3 text-sm-h3 py-4">Components in TIREx</h1>
      <p class="mx-auto py-4 tira-explanation">
        This is a click dummy/early prototype to search/slice/dice the components/tutorials/resources available in <a href="/tirex">TIREx</a> together with related resources. We currently have <a href="https://opensearchfoundation.org/wows2024/" target="_blank">an open call for components</a> as part of en ECIR workshop and will update the overview below with all submitted components. Please do not hesitate to contribute to this overview by modifying the <a href="https://github.com/tira-io/tira/blob/main/application/src/tirex-components.yml" target="_blank">underlying yml file</a>, we would be happy about all contributions!
      </p>
    </section>
  </v-container>
  <v-container v-if="loading"><loading :loading="loading"/></v-container>
  <div v-if="!loading">
    <v-form>
      <v-row class="justify-center mx-2">
        <v-col :cols="is_mobile() ? '12' : '4'">
          <v-select v-model="component_types" :items="available_component_types" label="Select Types" multiple hint="Which components do you want to see?"/>
        </v-col>
        <v-col :cols="is_mobile() ? '12' : '4'">
          <v-select v-model="focus_types" :items="available_focus_types" label="Select Your Focus" multiple hint="Which aspect should be fulfilled by a component?"/>
        </v-col>
        <v-col :cols="is_mobile() ? '12' : '4'">
          <v-responsive min-width="220px" id="task-search">
             <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="component_filter"  @input="(i:any) => filter_f(i)"/>
          </v-responsive>
        </v-col>
      </v-row>
    </v-form>
    <div>
      <v-row class="justify-center mx-2 mb-5">
        <v-col v-for="i in 6" :cols="is_mobile() ? '12' : '2'">
          <v-row v-for="(row, index) in vectorizedComponents">
            <v-menu>
            <template v-slot:activator="{ props }">
              <v-card v-bind="props" v-if="vectorizedComponents[index][i-1] && vectorizedComponents[index][i-1]?.display_name && !vectorizedComponents[index][i-1].hide" class="ma-1 w-100 text-start" :max-width="max_width" :color="vectorizedComponents[index][i-1]?.color" variant="tonal" style="cursor: pointer;">
                <v-card-item><span class="text-h6 mb-1">{{ vectorizedComponents[index][i-1]?.display_name }}</span><span style="font-size: .7em;" v-if="vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">&nbsp;&nbsp;(+&nbsp;{{ vectorizedComponents[index][i-1].subItems }})</span></v-card-item>
              </v-card>
            </template>

            <v-list>
              <v-list-item v-for="link in vectorizedComponents[index][i-1].links">
                <v-list-item-title><a :href="link.href" :target="link.target">{{ link.display_name }}</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="vectorizedComponents[index][i-1].tirex_submission_id">
                <v-dialog>
                    <template v-slot:activator="{ props }">
                      <v-list-item-title v-bind="props" class="show-code-button" @click="fetch_code(index, i-1)">Show code</v-list-item-title>
                    </template>
                  <template v-slot:default="{ isActive }">
                    <v-card class="bg-grey-darken-3">
                      <v-card-text content="code">
                        <loading v-if="!code" loading="true"/>
                        <code-snippet v-if="code" :title="'Example code snippet for ' + vectorizedComponents[index][i-1]?.display_name" :code="code" expand_message=""/>
                      </v-card-text>

                      <v-card-actions>
                        <v-spacer></v-spacer>

                        <v-btn
                          text="Close code snippet"
                          @click="isActive.value = false"
                        ></v-btn>
                      </v-card-actions>
                    </v-card>
                  </template>
                </v-dialog>
              </v-list-item>
              <v-list-item v-if="!vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="collapseItem(vectorizedComponents[index][i-1].display_name)">Collapse sub-items</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="expandItem(vectorizedComponents[index][i-1].display_name)">Expand {{ vectorizedComponents[index][i-1].subItems }} items</a></v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          </v-row>
        </v-col>
      </v-row>
    </div>
  </div>
</template>


<script lang="ts">
import { inject } from 'vue'

import {is_mobile, Loading} from './components'
import {compareArrays, extractComponentTypesFromCurrentUrl, extractFocusTypesFromCurrentUrl, extractSearchQueryFromCurrentUrl, get, inject_response, reportError} from './utils';
import CodeSnippet from "@/components/CodeSnippet.vue";

interface Component {
  identifier: string;
  display_name: string;
  components?: Component[];
  links?: { display_name: string; href: string; target: string }[];
}

type ComponentSet = Map<string, { ancestors: string[]; children: string[] }>;




export default {
  name: "ir-components",
  components: {CodeSnippet, Loading},
  data() {
    return {
      max_width: 1500,
      loading: true,
      tirex_components: [
        {'identifier': 'loading', 'display_name': 'loading', 'components': [{'identifier': 'loading', 'display_name': 'loading'}], 'links': [{'display_name': '.', 'href': '.', 'target': '.'}], 'tirex_submission_id': null},
      ],
      code: '',
      colors: {
        'Dataset': 'green', 'Document Processing': 'yellow-lighten-1',
        'Query Processing': 'yellow-darken-4', 'Retrieval': 'cyan-lighten-1',
        'Re-Ranking': 'cyan-darken-3', 'Evaluation': 'blue-grey-lighten-1'
      } as {
        [key: string]: string
      },
      expanded_entries: ['does-not-exist'],
      component_filter: extractSearchQueryFromCurrentUrl(),
      component_types: compareArrays(extractComponentTypesFromCurrentUrl(), []) ? ['Code', 'TIREx', 'Tutorial'] : extractComponentTypesFromCurrentUrl(),
      available_component_types: ['Code', 'TIREx', 'Tutorial'],
      focus_types: compareArrays(extractFocusTypesFromCurrentUrl(), []) ? ['Precision', 'Recall'] : extractFocusTypesFromCurrentUrl(),
      available_focus_types: ['Precision', 'Recall'],
      refresh: 0
    }
  },
  methods: {
    // this function recursively computes the parent and child component for each element in tirex_components. used in search evaluation
    constructComponentSet(components: Component[]): ComponentSet {
      const componentSet: ComponentSet = new Map();

      function traverse(current: Component, ancestors: string[] = []) {
        const componentKey = current.display_name;

        if (!componentSet.has(componentKey)) {
          componentSet.set(componentKey, { ancestors, children: [] });
        } else {
          componentSet.get(componentKey)?.ancestors.push(...ancestors);
        }

        if (current.components && current.components.length > 0) {
          for (const child of current.components) {
            traverse(child, [componentKey, ...ancestors]);
            const childChildren = componentSet.get(child.display_name)?.children ?? [];
            componentSet.get(componentKey)?.children.push(child.display_name, ...childChildren);
          }
        }
      }

      components.forEach((component) => traverse(component));

      return componentSet;
    },
    fetch_code(index: number, i: number) {
      this.code = ''
      get(inject("REST base URL")+'/api/tirex-snippet?component='+ this.vectorizedComponents[index][i].tirex_submission_id)
        .then((message) => {this.code = message['context']['snippet']})
    },
    colorOfComponent(c:string) : string {
      return this.colors[c] ?? "grey"
    },
    is_mobile() {return is_mobile()},
    collapseItem(c:string) {
      this.expanded_entries = this.expanded_entries.filter(e => e != c)
    },
    expandItem(c:string) {
      this.expanded_entries.push(c)
    },
    countSubItems(component:any) {
      let ret = 0

      if (component.hasOwnProperty('components') && component['components'].length > 0) {
        for (let c of component['components']) {
              ret += 1 + this.countSubItems(c)
        }
      }

      return ret
    },
    is_collapsed(component:any) {
      return !this.computed_expanded_entries.includes(component.display_name)
    },
    filtered_sub_components(component:any) : {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null, tirex_submission_id: string|undefined|null}[] {
      let ret: {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null, tirex_submission_id: string|undefined|null}[] = []

      if (this.is_collapsed(component) || !component['components']) {
        return ret
      }

      for (let i=0; i< component['components'].length; i++) {
          const c = component['components'][i]
          ret.push({
            'display_name': c.display_name,
            'subItems': this.countSubItems(c),
            'pos': ret.length + 1,
            'links': c.hasOwnProperty('links') ? c['links'] : null,
            'focus_type': c.hasOwnProperty('focus_type') ? c['focus_type'] : null,
            'component_type': c.hasOwnProperty('component_type') ? c['component_type'] : null,
            'tirex_submission_id': c['tirex_submission_id']
          })

          for (let sub_c of this.filtered_sub_components(c)) {
            ret.push({
              'display_name': sub_c['display_name'],
              'subItems': this.countSubItems(sub_c),
              'pos': ret.length + 1,
              'links': sub_c['links'],
              'focus_type': sub_c.hasOwnProperty('focus_type') ? sub_c['focus_type'] : null,
              'component_type': sub_c.hasOwnProperty('component_type') ? sub_c['component_type'] : null,
              'tirex_submission_id': sub_c['tirex_submission_id']
            })
          }
        }

        return ret
    },
    // used in hide_component to check whether component matches selected focus or types
    matches(c: any, t:string, available:any) {
      if (!c || c[t] + '' == 'null' ||  c[t] + '' == 'undefined' || typeof c[t][Symbol.iterator] != 'function') {
        return false
      }

      for (let i of c[t]) {
        if (available.includes(i)) {
          return true
        }
      }

      return false
    },
    filter_f(f: any) {
      this.refresh++
    },
    // this function is used in the hide_component to evaluate whether a component matches a search query
    // to determine this it searches a computed map of all parent and children nodes and tries to find a match with the search string
    component_matches_search_query (elementKey: string): boolean {
        const ancestors = this.tirex_component_relationship_set.get(elementKey)?.ancestors || [];
        const children = this.tirex_component_relationship_set.get(elementKey)?.children || [];
        const filter_adjusted_for_being_empty = this.component_filter ? this.component_filter.toLowerCase() : ''
        const matchesItself = elementKey.toLowerCase().includes(filter_adjusted_for_being_empty)

        return ancestors.some((ancestor : string) => ancestor.toLowerCase().includes(filter_adjusted_for_being_empty)) || children.some((child : string) => child.toLowerCase().includes(filter_adjusted_for_being_empty)) || matchesItself;
      },

    // used in VectorizeComponents. Calculates whether a component should be hidden based on search criteria
    hide_component(c: any) : boolean {
      const component_search_is_active = this.component_types.length != 0 && this.component_types.length != this.available_component_types.length
      const focus_search_is_active = this.focus_types.length != 0 && this.focus_types.length != this.available_focus_types.length
      const text_search_is_active = this.component_filter + '' != '' || this.component_filter + '' != 'null' || this.component_filter + '' != 'undefined'
      if (!c || (!component_search_is_active && !focus_search_is_active && !text_search_is_active)) {
        return false
      }
      let component_match = !component_search_is_active || this.matches(c, 'component_type', this.component_types)
      let focus_match = !focus_search_is_active || this.matches(c, 'focus_type', this.focus_types)
      let search_match = !text_search_is_active || this.component_matches_search_query(c.display_name)

      return !component_match || !focus_match || !search_match
    },
    updateUrlToCurrentSearchCriteria() {
      this.$router.replace({name: 'tirex', params: {component_types: this.component_types.join(), focus_types: this.focus_types.join(), search_query: this.component_filter}})
    },
    findMatchingParents(componentSet: ComponentSet, targetKey: string): string[] {
      const lowercaseTargetKey = targetKey.toLowerCase();
      const matchingParents: string[] = [];

      for (const [key, value] of componentSet) {
        const lowercaseKey = key.toLowerCase();

        if (lowercaseKey.includes(lowercaseTargetKey) || (value.children && value.children.length > 0 && value.children.map(child => child.toLowerCase()).includes(lowercaseTargetKey))) {
          matchingParents.push(key, ...value.ancestors);
        }
      }

      return matchingParents;
    },
  },
  beforeMount() {
    get(inject("REST base URL")+'/api/tirex-components')
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem while loading the overview of the components.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  computed: {
    computed_expanded_entries() : string[] {
      let ret = [...this.expanded_entries];
      if(!is_mobile()) {
        ret = ret.concat(['Dataset', 'Document Processing', 'Query Processing', 'Retrieval',
        'Re-Ranking', 'Evaluation'])
      }
      if(this.component_filter !== '') {
        let terms = this.findMatchingParents(this.tirex_component_relationship_set, this.component_filter)
        terms = [...new Set(terms)];
        if(terms && terms.length > 0){
          for (let i = 0; i < terms.length; i++) {
            ret = ret.concat(terms[i]);
          }
        }
      }

      return ret
    },

    // computed variable to store the map of ancestor and child nodes for all components
    tirex_component_relationship_set() : ComponentSet {
      return this.constructComponentSet(this.tirex_components)
    },

    //computes a modified view of the tirex components to display in a grid like manner.
    vectorizedComponents() {
      //initialize array of rows for each category i.e. ['Dataset', 'Document Processing', 'Query Processing', 'Retrieval', 'Re-Ranking', 'Evaluation']
      let ret: [any[]] = [[{}, {}, {}, {}, {}, {}]]

      // for each category in tirex_components
      for (let i in this.tirex_components) {
        // c is an array of all components in category i
        let c = this.tirex_components[i]

        // we set row 0, aka the headers
        ret[0][i] = {'display_name': c.display_name, 'links': c.links, 'collapsed': this.is_collapsed(c), 'subItems':this.countSubItems(c), 'hide': false, 'tirex_submission_id': ''}

        // we loop through each categories subcomponents and enrich them with information needed for the grid display
        for (let subcomponent of this.filtered_sub_components(c)) {
          if (subcomponent['pos'] >= ret.length) {
            ret.push([{}, {}, {}, {}, {}, {}])
          }
          ret[subcomponent['pos']][i] = {
            'display_name': subcomponent['display_name'],
            'color': this.colorOfComponent(c.display_name),
            'subItems': subcomponent['subItems'],
            'links': subcomponent.links,
            'collapsed': this.is_collapsed(subcomponent),
            'hide': this.hide_component(subcomponent),
            'tirex_submission_id': subcomponent['tirex_submission_id'] || null
          }
        }
      }
      return ret
    },
  },
  watch: {
    component_types(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    },
    focus_types(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    },
    component_filter(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    }
  }
}
</script>
<style>
.show-code-button {
  cursor: pointer;
}
.show-code-button:hover {
    color: #4F81E4 /* primary color*/
  }
</style>