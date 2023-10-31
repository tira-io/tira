<template>
  <v-container class="text-center">
    <section>
      <h1 class="text-h3 text-sm-h3 py-4">Components available in TIREx</h1>
      <p class="mx-auto py-4 tira-explanation">
        lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.
      </p>
    </section>
  </v-container>
  <v-container v-if="loading"><loading :loading="loading"/></v-container>
  <div v-if="!loading">
    <div class="d-none d-md-block">
      <v-row class="justify-center mx-2">
        <v-col cols="4">
          <v-select v-model="component_types" :items="available_component_types" label="Select Types" multiple hint="Which components do you want to see?"/>
        </v-col>
        <v-col cols="4">
          <v-select v-model="focus_types" :items="available_focus_types" label="Select Your Focus" multiple hint="Which aspect should be fulfilled by a component?"/>
        </v-col>
        <v-col cols="4">
          <v-responsive min-width="220px" id="task-search">
             <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="component_filter"/>
          </v-responsive>
        </v-col>
      </v-row>
    </div>

    <v-row class="justify-center mx-2 d-md-none">
      <v-col cols="12">
        <v-select v-model="component_types" :items="available_component_types" label="Select Types" multiple hint="Which components do you want to see?"/>
      </v-col>
      <v-col cols="12">
        <v-select v-model="focus_types" :items="available_focus_types" label="Select Your Focus" multiple hint="Which aspect should be fulfilled by a component?"/>
      </v-col>
      <v-col cols="12">
        <v-responsive min-width="220px" id="task-search">
           <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="component_filter"/>
        </v-responsive>
      </v-col>
    </v-row>


    <div class="d-none d-md-block">
      <v-row class="justify-center mx-2" v-for="(row, _) of vectorizedComponents">
        <v-col v-for="(cell, i) in row" cols="cell.cols">
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-card v-bind="props" v-if="cell && cell?.display_name" class="mx-auto" :max-width="max_width" :color="cell?.color" variant="tonal" style="cursor: pointer;">
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
    <div class="d-md-none">
      <v-row class="justify-center mx-2" v-for="display_name in colors">
        <v-col cols="12">
          <v-card class="mx-auto" :max-width="max_width" variant="tonal" style="cursor: pointer;">
            <v-card-item><span class="text-h6 mb-1">{{ display_name }}</span><span style="font-size: .7em;" >TODO...</span></v-card-item>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </div>
</template>


<script lang="ts">
import { Loading } from './components'
import { get, reportError, inject_response } from './utils';
export default {
  name: "components",
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
      expanded_entries: ['Dataset', 'Document Processing', 'Query Processing', 'Retrieval', 'Re-Ranking', 'Evaluation'],
      component_filter: null,
      component_types: ['TIREx Submission', 'Tutorial'],
      available_component_types: ['Code', 'TIREx Submission', 'Tutorial'],
      focus_types: ['Precision', 'Recall'],
      available_focus_types: ['Precision', 'Recall'],
    }
  },
  methods: {
    colorOfComponent(c:string) {
      return this.colors[c] ?? "grey"
    },
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
      return !this.expanded_entries.includes(component.display_name)
    },
    filtered_sub_components(component:any) : {display_name: string, subItems: number, pos: number, links: any[]}[] {
      let ret: {display_name: string, subItems: number, pos: number, links: any[]}[] = []

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
          })

          for (let sub_c of this.filtered_sub_components(c)) {
            ret.push({
              'display_name': sub_c['display_name'],
              'subItems': sub_c['subItems'],
              'pos': ret.length + 1,
              'links': sub_c['links'],
            })
          }
        }

        return ret
    },
    mobileLayout() {
      return window.innerWidth < 1000;
    },
  },
  beforeMount() {
    get('/api/tirex-components')
      .then(inject_response(this, {'loading': false}))
      .catch(reportError("Problem While Loading the overview of the components.", "This might be a short-term hiccup, please try again. We got the following error: "))
  },
  computed: {
    vectorizedComponents() {
      let ret: [any[]] = [[{}, {}, {}, {}, {}, {}]]
      let cols = 2;//this.mobileLayout() ? 12 : 2;

      for (let i in this.tirex_components) {
        let c = this.tirex_components[i]

        ret[0][i] = {'display_name': c.display_name, 'cols': cols, 'links': c.links, 'collapsed': this.is_collapsed(c), 
            'subItems':this.countSubItems(c)}

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
          }
        }
      }
      
      return ret
    },
  }
}
</script>