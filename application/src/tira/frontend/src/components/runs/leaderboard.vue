<template>
<div class="scrollable-table">
<table class="uk-margin-small uk-table uk-table-small uk-table-striped uk-table-middle">
  <thead>
  <tr>
      <th></th>
      <th class="uk-table-shrink" v-if="role == 'admin'">&nbsp;</th>
      <th class="uk-table-shrink" v-if="role == 'admin'">&nbsp;</th>
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
          <sort-icon :row_key="key" :selected_key="currentSort" :direction="currentSortDir" />
      </th>
      <th class="header uk-table-expand"></th>
      <th class="header uk-table-shrink uk-text-nowrap"></th>
      <th class="header uk-table-shrink uk-text-nowrap"></th>
  </tr>
  </thead>
  <tbody>
  <!-- naming the loop variable "eval" will lead to an error within webpack (keyword) -->
  <tr class="uk-padding-remove"
      v-for="evaluation in filteredEvaluations">
      <td class="uk-table-shrink uk-padding-remove uk-margin-remove" :id="dataset_id + '-' + evaluation.vm_id + '-' + evaluation.run_id"></td>
      <td class="uk-table-shrink uk-padding-remove-vertical" v-if="role === 'admin'">
          <div uk-tooltip="This run is blinded" v-if="evaluation.blinded" class="dataset-detail-icon">
              <font-awesome-icon icon="fas fa-eye-slash"/>
          </div>
          <div uk-tooltip="This run is visible to the participant" v-else class="dataset-detail-icon uk-text-success">
              <font-awesome-icon icon="fas fa-eye" />
          </div>
      </td>
      <td class="uk-table-shrink uk-padding-remove-vertical" v-if="role === 'admin'"> <!-- Icons -->
          <div uk-tooltip="This run is on the leaderboards" v-if="evaluation.published" class="dataset-detail-icon uk-text-success">
              <font-awesome-icon icon="fas fa-sort-amount-up" />
          </div>
          <div uk-tooltip="This run is not published" v-else class="dataset-detail-icon">
              <font-awesome-icon icon="fas fa-sort-amount-up" />
          </div>
      </td>
<!--    TODO show group name if not none, else show vm_id-->
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.vm_id }}</td>
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.input_software_name }}</td>
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove-vertical">{{ evaluation.run_id }}</td>
      <td class="uk-padding-remove-vertical uk-table-shrink uk-text-nowrap" v-for="measure in evaluation.measures">{{ measure }}</td>
      <td class="uk-padding-remove-vertical uk-text-truncate"></td>
      <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
        <a class="uk-button uk-button-small uk-button-default uk-background-default"
           target="_blank"
           :href="'/serp/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/' + evaluation.input_run_id"><i class="fas fa-download"></i> SERP</a>
        <a class="uk-button uk-button-small uk-button-default uk-background-default"
           target="_blank"
           :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.input_run_id + '.zip'"><i class="fas fa-download"></i> run</a>
        <a class="uk-button uk-button-small uk-button-default uk-background-default"
           target="_blank"
           :href="'/task/' + task_id + '/user/' + evaluation.vm_id + '/dataset/' + dataset_id + '/download/' + evaluation.run_id + '.zip'"><i class="fas fa-download"></i> result</a>
      </td>
  </tr>
  </tbody>
</table>
</div>
</template>
<script>
import SortIcon from "../elements/sort-icon";

export default {
  props: ['keys', 'evaluation', 'role', 'dataset_id', 'task_id', 'hide_private'],
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
  },
  computed: {
    filteredEvaluations: function () {
      let result = this.hide_private ? this.evaluation.filter(i => i.published === true || i.published === 1) : this.evaluation
      result.map(i => {
        i.vm_id = i.vm_id.replace(/-default/, '')
      })

      result.sort((a, b) => {
        let modifier = 1;
        if(this.currentSortDir === 'desc') modifier = -1;
        if (this.keys.includes(this.currentSort)) {
          let key_index = this.keys.indexOf(this.currentSort)
          if(a["measures"][key_index] < b["measures"][key_index]) return -1 * modifier;
          if(a["measures"][key_index] > b["measures"][key_index]) return modifier;
        } else {
          if (a[this.currentSort].toLowerCase() < b[this.currentSort].toLowerCase()) return -1 * modifier;
          if (a[this.currentSort].toLowerCase() > b[this.currentSort].toLowerCase()) return modifier;
        }
        return 0;
      })
      return result
    }
  }
}
</script>

