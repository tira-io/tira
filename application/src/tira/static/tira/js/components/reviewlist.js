import RunList from './runlist.js'

export default {
  props: ['vms', 'task_id', 'dataset_id', 'hide_reviewed'],
  components: {
      RunList
  },
  template: `
<ul id="tira-run-accordion" class="uk-list uk-list-collapse uk-list-striped" uk-accordion="multiple: true">
    <li v-for="vm in vms">
        <div class="uk-accordion-title">
            <table class="uk-text-small uk-width-5-6">
                <tr>
                  <td class="uk-width-1-5 uk-text-left"><b>[[ vm.vm_id ]]</b></td>
                  <td class="uk-width-1-5 uk-text-right">[[ vm.runs.length ]] Runs</td>
                  <td class="uk-width-1-5 uk-text-right">
                      <span  v-if="vm.unreviewed_count > 0" class="uk-text-warning">
                      [[ vm.unreviewed_count ]] Unreviewed</span></td>
                  <td class="uk-width-1-5 uk-text-right">[[ vm.blinded_count ]] Blinded</td>
                  <td class="uk-width-1-5 uk-text-right">
                      <span v-if="vm.published_count == 0" class="uk-text-warning">
                      [[ vm.published_count ]] Published</span></td>
                </tr>
            </table>
        </div>
        <div class="uk-accordion-content uk-margin-remove-top" v-if="vm">
            <a :href="'/task/' + task_id + '/user/' + vm.vm_id">[manage user]</a>
            <RunList :runs="vm.runs" :vm_id="vm.vm_id" :task_id="task_id" :dataset_id="dataset_id" :for_review="true" :hide_reviewed="hide_reviewed"/> 
        </div>
    </li>
</ul>
`
}