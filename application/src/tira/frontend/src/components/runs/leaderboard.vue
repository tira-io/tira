<template>
  <div class="scrollable-table">
    <table class="uk-margin-small uk-table uk-table-small uk-table-middle">
      <thead>
      <tr>
        <th v-if="role === 'admin'">&nbsp;</th>
        <th v-if="role === 'admin'">&nbsp;</th>
        <th>&nbsp;</th>
        <th>&nbsp;</th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('vm_id')">
          <span>Team&nbsp;</span>
          <sort-icon :row_key="'vm_id'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('input_software_name')">
          <span>Software&nbsp;</span>
          <sort-icon :row_key="'input_software_name'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('run_id')">
          <span>Run&nbsp;</span>
          <sort-icon :row_key="'run_id'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort(key)" v-for="key in filteredKeys(keys)">
          <span>{{ key }}&nbsp;</span>
          <sort-icon :row_key="key" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-expand"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
      </tr>
      </thead>
      <tr class="uk-padding-remove" style="visibility: collapse">
        <td class="uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download SERP-data"
             :href="'/serp/' + task_id + '/user/' + filteredEvaluations[0].vm_id + '/dataset/' + dataset_id + '/' + filteredEvaluations[0].input_run_id"><i
              class="fa-solid fa-square-poll-horizontal"></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download the run"
             :href="'/task/' + task_id + '/user/' + filteredEvaluations[0].vm_id + '/dataset/' + dataset_id + '/download/' + filteredEvaluations[0].input_run_id + '.zip'"><i
              class="fas fa-download"></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download the results"
             :href="'/task/' + task_id + '/user/' + filteredEvaluations[0].vm_id + '/dataset/' + dataset_id + '/download/' + filteredEvaluations[0].run_id + '.zip'"><i
              class="fa-solid fa-ranking-star "></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             @click="expandDetails(index)"
             uk-tooltip="Show details about running locally"
          >
            <i :id="'chevron-down-' + index" uk-icon="chevron-down"></i>
            <i :id="'chevron-up-' + index" uk-icon="chevron-up" class="hide-element"></i>
          </a>

        </td>
        <td class="uk-table-shrink uk-padding-remove uk-margin-remove"
            :id="dataset_id + '-' + filteredEvaluations[0].vm_id + '-' + filteredEvaluations[0].run_id"></td>
        <td class="uk-padding-remove-vertical" v-if="role === 'admin'">
          <div uk-tooltip="This run is blinded" v-if="evaluation.blinded" class="dataset-detail-icon">
            <font-awesome-icon icon="fas fa-eye-slash"/>
          </div>
          <div uk-tooltip="This run is visible to the participant" v-else
               class="dataset-detail-icon uk-text-success">
            <font-awesome-icon icon="fas fa-eye"/>
          </div>
        </td>
        <td class="uk-padding-remove-vertical" v-if="role === 'admin'"> <!-- Icons -->
          <div uk-tooltip="This run is on the leaderboards" v-if="evaluation.published"
               class="dataset-detail-icon uk-text-success">
            <font-awesome-icon icon="fas fa-sort-amount-up"/>
          </div>
          <div uk-tooltip="This run is not published" v-else class="dataset-detail-icon">
            <font-awesome-icon icon="fas fa-sort-amount-up"/>
          </div>
        </td>
        <!--    TODO show group name if not none, else show vm_id-->
        <td class="uk-text-nowrap uk-table-expand uk-padding-remove-vertical">{{ filteredEvaluations[0].vm_id }}</td>
        <td class="uk-text-nowrap uk-padding-remove-vertical">{{
            filteredEvaluations[0].input_software_name
          }}
        </td>
        <td class="uk-text-nowrap uk-padding-remove-vertical">{{ filteredEvaluations[0].run_id }}</td>
        <td class="uk-padding-remove-vertical uk-table-shrink uk-text-nowrap"
            v-for="measure in filteredEvaluations[0].measures">{{ measure }}
        </td>
      </tr>
    </table>
    <table :class="index % 2 === 1 ? 'uk-background-muted uk-margin-small uk-table uk-table-small uk-table-middle' : 'uk-margin-small uk-table uk-table-small uk-table-middle'"
           v-for="(evaluation, index) in filteredEvaluations">
      <thead style="visibility: collapse">
      <tr>
        <th v-if="role === 'admin'">&nbsp;</th>
        <th v-if="role === 'admin'">&nbsp;</th>
        <th>&nbsp;</th>
        <th>&nbsp;</th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('vm_id')">
          <span>Team&nbsp;</span>
          <sort-icon :row_key="'vm_id'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('input_software_name')">
          <span>Software&nbsp;</span>
          <sort-icon :row_key="'input_software_name'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort('run_id')">
          <span>Run&nbsp;</span>
          <sort-icon :row_key="'run_id'" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-shrink uk-text-nowrap" @click="sort(key)" v-for="key in keys">
          <span>{{ key }}&nbsp;</span>
          <sort-icon :row_key="key" :selected_key="currentSort" :direction="currentSortDir"/>
        </th>
        <th class="header uk-table-expand"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
        <th class="header uk-table-shrink uk-text-nowrap"></th>
      </tr>
      </thead>
      <!-- naming the loop variable "eval" will lead to an error within webpack (keyword) -->
      <tr class="uk-padding-remove">
        <td class="uk-text-nowrap uk-table-middle uk-padding-remove uk-margin-remove uk-preserve-width">
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download SERP-data"
             :href="'/serp/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/' + evaluation.input_run_id"><i
              class="fa-solid fa-square-poll-horizontal"></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download the run"
             :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.input_run_id + '.zip'"><i
              class="fas fa-download"></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             target="_blank"
             uk-tooltip="Download the results"
             :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.run_id + '.zip'"><i
              class="fa-solid fa-ranking-star "></i> </a>
          <a class="uk-button uk-button-small uk-button-default uk-background-default"
             @click="expandDetails(index)"
             uk-tooltip="Show details about running locally"
          >
            <i :id="'chevron-down-' + index" uk-icon="chevron-down"></i>
            <i :id="'chevron-up-' + index" uk-icon="chevron-up" class="hide-element"></i>
          </a>

        </td>
        <td class="uk-table-shrink uk-padding-remove uk-margin-remove"
            :id="dataset_id + '-' + evaluation.vm_id + '-' + evaluation.run_id"></td>
        <td class="uk-padding-remove-vertical" v-if="role === 'admin'">
          <div uk-tooltip="This run is blinded" v-if="evaluation.blinded" class="dataset-detail-icon">
            <font-awesome-icon icon="fas fa-eye-slash"/>
          </div>
          <div uk-tooltip="This run is visible to the participant" v-else
               class="dataset-detail-icon uk-text-success">
            <font-awesome-icon icon="fas fa-eye"/>
          </div>
        </td>
        <td class="uk-padding-remove-vertical" v-if="role === 'admin'"> <!-- Icons -->
          <div uk-tooltip="This run is on the leaderboards" v-if="evaluation.published"
               class="dataset-detail-icon uk-text-success">
            <font-awesome-icon icon="fas fa-sort-amount-up"/>
          </div>
          <div uk-tooltip="This run is not published" v-else class="dataset-detail-icon">
            <font-awesome-icon icon="fas fa-sort-amount-up"/>
          </div>
        </td>
        <!--    TODO show group name if not none, else show vm_id-->
        <td class="uk-text-nowrap uk-table-expand uk-padding-remove-vertical">{{ evaluation.vm_id }}</td>
        <td class="uk-text-nowrap uk-padding-remove-vertical">{{
            evaluation.input_software_name
          }}
        </td>
        <td class="uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.run_id }}</td>
        <td class="uk-padding-remove-vertical uk-table-shrink uk-text-nowrap"
            v-for="measure in filterMeasures(evaluation.measures)">{{ measure }}
        </td>
      </tr>
      <tr>
        <td :id="'details_' + index"
            class="uk-table-shrink uk-text-nowrap uk-preserve-width hide-element"
        >
          <div>
            <p class="uk-text-bold">Task description: </p>
            <p>{{ taskDescription}}</p>
          </div>
          <div>
            <p class="uk-text-bold">Previous stage: </p>
            <p>{{ evaluation.previous_stage }}</p>
          </div>
          <p class="uk-text-bold">Run locally: </p>
          <ul uk-tab>
            <li><a href="#">TIRA (CLI)</a></li>
            <li><a href="#">TIRA (Python)</a></li>
            <li><a href="#">Docker</a></li>
          </ul>
          <ul class="uk-switcher uk-margin">
            <li><code>{{ evaluation.cli_command}}</code></li>
            <li><code>{{ evaluation.python_command}}</code></li>
            <li><code>{{ evaluation.docker_command}}</code></li>

          </ul>
        </td>
      </tr>
    </table>
  </div>
</template>
<script>
import SortIcon from "../elements/sort-icon";

export default {
  props: ['keys', 'evaluation', 'role', 'dataset_id', 'task_id', 'hide_private', 'taskDescription'],
  components: {
    SortIcon
  },
  data() {
    return {
      currentSort: 'vm',
      currentSortDir: 'desc',
    }
  },
  beforeMount() {
    this.currentSort = this.keys[0]
  },
  methods: {
    sort: function (s) {
      if (s === this.currentSort) {
        this.currentSortDir = this.currentSortDir === 'asc' ? 'desc' : 'asc';
      } else {
        this.currentSortDir = 'desc'
      }
      this.currentSort = s;
    },
    expandDetails: function (index) {
      document.getElementById('details_' + index).classList.toggle('hide-element');
      document.getElementById('chevron-down-' + index).classList.toggle('hide-element');
      document.getElementById('chevron-up-' + index).classList.toggle('hide-element');
    },
    filterMeasures: function (measures) {
      let result = []
      for (let i = 0; i < measures.length; i++) {
        if (measures[i] !== "") {
          result.push(measures[i])
        }
      }
      return result
    },
    filteredKeys: function (keys) {
      let result = {}
      for (const key in keys) {
        if (this.filteredEvaluations[0]["measures"][key] !== "") {
          result[key] = keys[key];
        }
      }
      return result
    }
  },
  computed: {
    filteredEvaluations: function () {
      let result = this.hide_private ? this.evaluation.filter(i => i.published === true) : this.evaluation
      result.map(i => {
        i.vm_id = i.vm_id.replace(/-default/, '')
      })

      result.sort((a, b) => {
        let modifier = 1;
        if (this.currentSortDir === 'desc') modifier = -1;
        if (this.keys.includes(this.currentSort)) {
          let key_index = this.keys.indexOf(this.currentSort)
          if (a["measures"][key_index] < b["measures"][key_index]) return -1 * modifier;
          if (a["measures"][key_index] > b["measures"][key_index]) return modifier;
        } else {
          if (a[this.currentSort].toLowerCase() < b[this.currentSort].toLowerCase()) return -1 * modifier;
          if (a[this.currentSort].toLowerCase() > b[this.currentSort].toLowerCase()) return modifier;
        }
        return 0;
      })
      return result
    }
  },

}
</script>