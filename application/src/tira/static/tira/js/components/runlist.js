export default {
    props: ['runs', 'vm_id', 'task_id', 'dataset_id', 'for_review', 'hide_reviewed'],
    computed: {
        getRuns() {
            if (this.hide_reviewed) {
                return this.runs.filter(run => (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) === false)
            }
            return this.runs
        }
    },
    template: `
<div class="scrollable-table">
<table class="uk-margin-small uk-table uk-table-divider uk-table-small uk-table-middle">
    <thead>
    <tr>
        <th></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Run</span></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Input Run</span></th>
        <th class="header uk-table-expand"><span v-if="for_review">Review</span><span v-else>Dataset</span></th>
        <th class="header uk-text-center uk-width-1-4">Actions</th>
    </tr>
    </thead>
    <tbody>
    <tr v-for="run in getRuns"  class="uk-padding-remove" :id="run.run.software.id + '-' + run.run.run_id + '-run'"
    :class="{ 'table-background-green': (run.review.noErrors) && !for_review,
              'table-background-red': (run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && !for_review,
              'uk-background-default': !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && !for_review,
              'table-background-yellow': !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && for_review,
              'uk-background-default': (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) && for_review}">
        <td :id="'run-' + vm_id + '-' + run.run.run_id"></td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run status Icon -->
            <div uk-tooltip="This run is OK" v-if="run.review.noErrors">
                <i class="fas fa-check dataset-detail-icon uk-text-success"></i>
            </div>
            <div uk-tooltip="This run has errors" v-else-if="run.review.hasErrors">
                <i class="fas fa-times dataset-detail-icon uk-text-danger"></i>
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run visibility Icon -->
            <div uk-tooltip="This run is blinded" v-if="run.review.blinded">
                <i class="fas fa-user-slash dataset-detail-icon"></i>
            </div>
            <div uk-tooltip="This run is visible to the participant" v-else>
                <i class="fas fa-user dataset-detail-icon uk-text-success"></i>
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- published run Icon -->
            <div uk-tooltip="This run is on the leaderboards" v-if="run.review.published">
                <i class="fas fa-users dataset-detail-icon uk-text-success"></i>
            </div>
            <div uk-tooltip="This run is not published" v-else>
                <i class="fas fa-users-slash dataset-detail-icon"></i>
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- is upload  -->
            <div uk-tooltip="This run is was uploaded" v-if="run.is_upload">
                <i class="fas fa-upload dataset-detail-icon"></i>
            </div>
            <div uk-tooltip="This run is is from a software" v-if="!run.is_upload">
                <i class="fas fa-cogs dataset-detail-icon"></i>
            </div>
        </td>
<!--        Note: the style attribute below is a hack, since disraptor ignores fa-flip-horizontal-->
        <td class="uk-table-shrink uk-text-nowrap"><span v-if="run.run.is_evaluation"><i class="fas fa-level-up-alt" style="transform: scaleX(-1);"></i></span>&nbsp;[[ run.run.run_id ]]</td>
        <td class="uk-table-shrink uk-text-nowrap" ><a :href="'#run-' + vm_id + '-' + run.run.input_run_id" v-if="run.run.input_run_id != ''">[[ run.run.input_run_id ]]</a>
        </td>
        <td class="uk-padding-remove-vertical uk-text-nowrap uk-text-truncate" v-if="for_review">
           <span v-if="run.review.reviewer" class="uk-text-bold">[[ run.review.reviewer ]]&nbsp;</span> 
           <span v-if="run.review.hasErrorOutput">Output Error -&nbsp;</span>
           <span v-else-if="run.review.otherErrors">Software Error -&nbsp;</span>
           <span v-if="run.review.comment != ''">[[ run.review.comment ]]</span>
           </td>
        <td class="uk-padding-remove-vertical uk-text-truncate" v-else>[[ dataset_id ]]</td>
        
        <td class="uk-align-right uk-table-expand uk-text-nowrap uk-margin-remove uk-padding-remove-vertical uk-padding-remove-right">
            <a class="uk-button uk-button-small uk-button-default run-evaluate-button uk-background-default"
               data-tira-dataset="{{ run.dataset }}" data-tira-vm-id="{{ vm_id }}"
               data-tira-run-id="{{ run.run_id }}"
               v-if="!(for_review) && !run.run.is_evaluation">
                <div id="run-evaluate-spinner-{{ run.run_id }}" class="run-evaluate-spinner" uk-spinner="ratio: 0.4"></div> evaluate</a>
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               :href="'/task/' + task_id + '/user/' + vm_id + '/dataset/' + dataset_id + '/run/' + run.run.run_id"><i class="fas fa-search"></i> inspect</a>
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               target="_blank"
               :href="'/task/' + task_id + '/user/' + vm_id + '/dataset/' + dataset_id + '/download/' + run.run.run_id + '.zip'"><i class="fas fa-download"></i> download</a>
            <a class="uk-button uk-button-small uk-button-danger run-delete-button"
               v-if="!(for_review)"
               data-tira-dataset="{{ run.dataset }}" data-tira-vm-id="{{ vm_id }}"
               data-tira-run-id="{{ run.run_id }}">delete</a>
          </td>         
    </tr>
    </tbody>
</table>
</div>
`
}

