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
<!---
    <div>
      <v-row class="justify-center mx-2" v-for="(row, _) of vectorizedComponents">
        <v-col v-for="(cell, i) in row" cols="cell.cols">
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-card v-bind="props" v-if="cell && cell?.display_name && !cell.hide" class="mx-auto" :max-width="max_width" :color="cell?.color" variant="tonal" style="cursor: pointer;">
                <v-card-item><span class="text-h6 mb-1">{{ cell?.display_name }}</span><span style="font-size: .7em;" v-if="cell.collapsed && cell.subItems > 0">&nbsp;&nbsp;(+&nbsp;{{ cell.subItems }})</span></v-card-item>
              </v-card>
            </template>

            <v-list>
              <v-list-item v-for="link in cell.links">
                <v-list-item-title><a :href="link.href" :target="link.target">{{ link.display_name }}</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="!cell.collapsed && cell.subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="collapseItem(cell.display_name)">Collapse sub-items</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="cell.collapsed && cell.subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="expandItem(cell.display_name)">Expand {{ cell.subItems }} items</a></v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>      
        </v-col>
      </v-row>
    </div>
    -->
    <div>
      <v-row class="justify-center mx-2">
        <v-col v-for="i in 6" cols="2">
          <v-row v-for="(row, index) in vectorizedComponents" class="ma-1">
            <v-menu>
            <template v-slot:activator="{ props }">
              <v-card @click="logger(tirex_components)" v-bind="props" v-if="vectorizedComponents[index][i-1] && vectorizedComponents[index][i-1]?.display_name && !vectorizedComponents[index][i-1].hide" class="mx-auto w-100 text-start" :max-width="max_width" :color="vectorizedComponents[index][i-1]?.color" variant="tonal" style="cursor: pointer;">
                <v-card-item><span class="text-h6 mb-1">{{ vectorizedComponents[index][i-1]?.display_name }}</span><span style="font-size: .7em;" v-if="vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">&nbsp;&nbsp;(+&nbsp;{{ vectorizedComponents[index][i-1].subItems }})</span></v-card-item>
              </v-card>
            </template>

            <v-list>
              <v-list-item v-for="link in vectorizedComponents[index][i-1].links">
                <v-list-item-title><a :href="link.href" :target="link.target">{{ link.display_name }}</a></v-list-item-title>
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
import { Loading, is_mobile } from './components'
import { get, reportError, inject_response } from './utils';
export default {
  name: "ir-components",
  components: {Loading},
  data() {
    return {
      max_width: 1500,
      loading: true,
      tirex_components: [
        {'display_name': 'loading', 'components': [{'display_name': 'loading'}], 'links': [{'display_name': '.', 'href': '.', 'target': '.'}]},
      ],
      colors: {
        'Dataset': 'green', 'Document Processing': 'yellow-lighten-1',
        'Query Processing': 'yellow-darken-4', 'Retrieval': 'cyan-lighten-1',
        'Re-Ranking': 'cyan-darken-3', 'Evaluation': 'blue-grey-lighten-1'
      } as {[key: string]: string},
      expanded_entries: ['does-not-exist'],
      component_filter: '',
      component_types: ['Code', 'TIREx', 'Tutorial'],
      available_component_types: ['Code', 'TIREx', 'Tutorial'],
      focus_types: ['Precision', 'Recall'],
      available_focus_types: ['Precision', 'Recall'],
      refresh: 0,
    }
  },
  methods: {
    logger(row : any) {
      console.log(this.tirex_components)
      console.log(this.vectorizedComponents)
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
    filtered_sub_components(component:any) : {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null}[] {
      let ret: {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null}[] = []

      if (this.is_collapsed(component)) {
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
          })

          for (let sub_c of this.filtered_sub_components(c)) {
            ret.push({
              'display_name': sub_c['display_name'],
              'subItems': sub_c['subItems'],
              'pos': ret.length + 1,
              'links': sub_c['links'],
              'focus_type': sub_c.hasOwnProperty('focus_type') ? sub_c['focus_type'] : null,
              'component_type': sub_c.hasOwnProperty('component_type') ? sub_c['component_type'] : null,
            })
          }
        }

        return ret
    },
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
    parent_contains_match (component: any) : boolean {
      console.log(component)
      console.log("testing parent-matching: ")
      console.log(component.parents)
      let contains_match = false;
      for(let i in component.children) {
        if (component.parents[i].toLowerCase().includes(this.component_filter.toLowerCase())) {
          contains_match = true;
        }
      }
      return contains_match;
    },
    child_contains_match (component: any) : boolean {
      console.log(component)
      console.log("testing child-matching: ")
      console.log(component.children)
      let contains_match = false;
      for(let i in component.children) {
      if(component.children[i].toLowerCase().includes(this.component_filter.toLowerCase())) {
        contains_match = true;
      }}
      return contains_match;
    },
    hide_component(c: any) : boolean {
      const component_search_is_active = this.component_types.length != 0 && this.component_types.length != this.available_component_types.length
      const focus_search_is_active = this.focus_types.length != 0 && this.focus_types.length != this.available_focus_types.length
      const text_search_is_active = this.component_filter + '' != '' || this.component_filter + '' != 'null' || this.component_filter + '' != 'undefined'
      if (!c || (!component_search_is_active && !focus_search_is_active && !text_search_is_active)) {
        return false
      }

      let component_match = !component_search_is_active || this.matches(c, 'component_type', this.component_types)
      let focus_match = !focus_search_is_active || this.matches(c, 'focus_type', this.focus_types)
      let search_match = !text_search_is_active || c.display_name.toLowerCase().includes(this.component_filter.toLowerCase()) || this.parent_contains_match(c) || this.child_contains_match(c)

      return !component_match || !focus_match || !search_match
    },
    list_subcomponents(component : any) : string[] {
      if(component.display_name.toLowerCase().includes("dense retrieval")) {
          return ["tbd 1", "tbd 2", "tbd 3"]
      }
      return ['']
    },
    list_parent_components(component : any) : [string] {
       if(component.display_name.toLowerCase().includes("tbd 1")) {
          return ["dense retrieval"]
      }
      return ['']
    },
  },
  beforeMount() {
    get('/api/tirex-components')
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the overview of the components.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  computed: {
    computed_expanded_entries() {
      let ret = [...this.expanded_entries];
      if(!is_mobile()) {
        ret = ret.concat(['Dataset', 'Document Processing', 'Query Processing', 'Retrieval',
        'Re-Ranking', 'Evaluation'])
      }

      return ret
    },
    vectorizedComponents() {
      // this.refresh

      //initialize array of rows for each category in ['Dataset', 'Document Processing', 'Query Processing', 'Retrieval', 'Re-Ranking', 'Evaluation']
      let ret: [any[]] = [[{}, {}, {}, {}, {}, {}]]
      let cols = is_mobile() ? 12 : 2;

      // for each category in tirex_components
      for (let i in this.tirex_components) {
        // c is an array of all components in category i
        let c = this.tirex_components[i]

        // we set row 0
        ret[0][i] = {'display_name': c.display_name, 'cols': cols, 'links': c.links, 'collapsed': this.is_collapsed(c), 'subItems':this.countSubItems(c), 'hide': false, 'children':this.list_subcomponents(c), 'parents': this.list_parent_components(c)}

        for (let subcomponent of this.filtered_sub_components(c)) {
          if (subcomponent['pos'] >= ret.length) {
            ret.push([{}, {}, {}, {}, {}, {}])
          }
          ret[subcomponent['pos']][i] = {
            'display_name': subcomponent['display_name'],
            'color': this.colorOfComponent(c.display_name),
            'subItems': subcomponent['subItems'],
            'links': subcomponent.links,
            'cols': cols,
            'collapsed': this.is_collapsed(subcomponent),
            'hide': this.hide_component(subcomponent),
            'children': this.list_subcomponents(subcomponent),
            'parents': this.list_parent_components(subcomponent)
          }
        }
      }

      if (is_mobile()) {
        let new_ret = []
        for(let i=0; i< 100; i++) {
          for (let j=0; j< ret.length && i < ret[j].length ; j++) {
            const cell = ret[j][i]
            if(cell && cell.hasOwnProperty('display_name')) {
              new_ret.push([cell])
            }
          }
        }

        return new_ret
      }

      return ret
    },
  }
}
</script>