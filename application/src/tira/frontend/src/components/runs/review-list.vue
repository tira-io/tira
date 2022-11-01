<template>
<div class="scrollable-table">
<table class="uk-margin-small uk-table uk-table-divider uk-table-small uk-table-middle">
    <thead>
    <tr>
        <th></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="uk-table-shrink"></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Run</span></th>
        <th class="header uk-table-shrink uk-text-nowrap"><span>Input Run</span></th>
        <th class="header uk-table-expand">Dataset</th>
        <th class="header uk-table-shrink uk-text-nowrap" v-if="display==='participant'"></th> <!--  evaluate button -->
        <th class="header uk-table-shrink uk-text-nowrap"></th> <!--  review button -->
        <th class="header uk-table-shrink uk-text-nowrap" v-if="display==='review'"></th> <!--  download button -->
        <th class="header uk-table-shrink uk-text-nowrap" v-if="display==='participant'"></th> <!--  delete button -->
    </tr>
    </thead>
    <tbody>
    <tr v-for="run in getRuns()"  class="uk-padding-remove" :id="run.software + '-' + run.run_id + '-run'"
    :class="{ 'table-background-yellow': display==='review' && !(run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors),
              'table-background-green': display==='participant' && run.review.noErrors,
              'table-background-red': display==='participant' && (run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors)}">
<!--              'uk-background-default': (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors)}">-->
        <td class="uk-table-shrink uk-padding-remove uk-margin-remove" :id="'run-' + user_id + '-' + run.run_id"></td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run status Icon -->
            <div uk-tooltip="This run is OK" v-if="run.review.noErrors" class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-check"/>
            </div>
            <div uk-tooltip="This run has errors" v-else-if="run.review.hasErrors" class="dataset-detail-icon uk-text-danger">
                <font-awesome-icon icon="fas fa-times"/>
            </div>
            <div uk-tooltip="This run has not been reviewed yet. A task organizer will check each run and confirm it's validity." v-else class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-question" />
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- run visibility Icon -->
            <div uk-tooltip="This run is blinded" v-if="run.review.blinded" class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-eye-slash"/>
            </div>
            <div uk-tooltip="This run is visible to the participant" v-else class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-eye" />
            </div>
        </td>
        <td class="uk-table-shrink uk-padding-remove-vertical"> <!-- published run Icon -->
            <div uk-tooltip="This run is on the leaderboards" v-if="run.review.published" class="dataset-detail-icon uk-text-success">
                <font-awesome-icon icon="fas fa-sort-amount-up" />
            </div>
            <div uk-tooltip="This run is not published" v-else class="dataset-detail-icon">
                <font-awesome-icon icon="fas fa-sort-amount-up" />
            </div>
        </td>
        <td class="uk-table-shrink uk-text-nowrap"><span v-if="run.input_run_id !== ''">
                <font-awesome-icon icon="fas fa-level-up-alt" flip="horizontal"/>
            </span>&nbsp;{{ run.run_id }}</td>
        <td class="uk-table-shrink uk-text-nowrap" ><a :href="'#run-' + user_id + '-' + run.input_run_id" v-if="run.input_run_id !== 'none'">{{ run.input_run_id }}</a>
        </td>
        <td class="uk-padding-remove-vertical uk-text-truncate" :uk-tooltip="run.dataset">{{ run.dataset }}</td>

<!--        <td class="uk-padding-remove-vertical uk-text-nowrap uk-text-truncate">-->
<!--           <span v-if="run.review.reviewer" class="uk-text-bold">{{ run.review.reviewer }}&nbsp;</span>-->
<!--           <span v-if="run.review.hasErrorOutput">Output Error -&nbsp;</span>-->
<!--           <span v-else-if="run.review.otherErrors">Software Error -&nbsp;</span>-->
<!--           <span v-if="run.review.comment !== ''">{{ run.review.comment }}</span>-->
<!--        </td>-->
        <!--      Buttons -->
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width"
            v-if="display==='participant'">
            <a class="uk-button uk-button-small run-evaluate-button uk-background-default"
               :class="{ 'uk-button-disabled': runningEvaluationIds.includes(run.run_id), 'uk-button-default': !runningEvaluationIds.includes(run.run_id)}"
               :disabled="runningEvaluationIds.includes(run.run_id)"
               @click="evaluateRun(run.dataset, run.run_id)"
               v-if="run.input_run_id === ''">
  <!--                <div v-show="runningEvaluationIds.includes(run.run_id)" class="run-evaluate-spinner" uk-spinner="ratio: 0.4"></div>-->
                <font-awesome-icon v-show="runningEvaluationIds.includes(run.run_id)" icon="fas fa-cog" spin />
                <font-awesome-icon v-show="!runningEvaluationIds.includes(run.run_id)" icon="fas fa-cog" />
                evaluate</a>
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width">
            <review-button :task_id="task_id" :user_id="user_id" :dataset_id="run.dataset"
                           :run_id="run.run_id" :csrf="csrf"
                @add-notification="(type, message) => this.$emit('add-notification', type, message)"
                @update-review="newReview => updateReview(newReview)"
            />
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width"
            v-if="display==='review'">
            <a class="uk-button uk-button-small uk-button-default uk-background-default"
               target="_blank"
               :href="'/task/' + task_id + '/user/' + user_id + '/dataset/' + run.dataset + '/download/' + run.run_id + '.zip'">
                <font-awesome-icon icon="fas fa-download" />

                </a>
        </td>
        <td class="uk-table-shrink uk-text-nowrap uk-padding-remove uk-margin-remove uk-preserve-width"
         v-if="display==='participant'">
            <a class="uk-button uk-button-small uk-button-danger"
               @click="deleteRun(run.dataset, run.run_id)">
              <font-awesome-icon icon="fas fa-trash-alt" /></a>
        </td>
    </tr>
    </tbody>
</table>
</div>
</template>
<script>
import ReviewButton from "../elements/review-button";
import { get } from "../../utils/getpost"

export default {
  data() {
    return {
      runningEvaluationIds: []
    }
  },
  props: {
    runs: Array,
    user_id: String,
    task_id: String,
    hide_reviewed: {
      type: Boolean,
      default: false
    },
    /**
     * @values review, participant
     */
    display: {
      type: String,
      default: 'review'
    },
    running_evaluations: {
      type: Array,
      default: []
    },
    csrf: String},
  emits: ['add-notification', 'poll-evaluations', 'remove-run'],
  components: {
      ReviewButton
  },
  methods: {
    getRuns() {
      if (this.hide_reviewed) {
          return this.runs.filter(run => (run.review.noErrors || run.review.hasErrors || run.review.hasErrorOutput || run.review.otherErrors) === false)
      }
      return this.runs
    },
    get: get,
    updateReview(newReview) {
      if (this.user_id === newReview.user_id){
        for (const run of this.runs){
          if (run.run_id === newReview.run_id) {
            run.review.blinded = !newReview.isVisibleToParticipant
            run.review.published = newReview.isOnLeaderboard
            run.review.noErrors =newReview.no_errors
            run.review.hasErrors = !newReview.no_errors
            run.review.comment =newReview. comment
            run.review.hasErrorOutput = newReview.output_error
            run.review.otherErrors = newReview.software_error
            run.review.reviewer = newReview.reviewer
            run.reviewed = newReview.no_errors || newReview.output_error || newReview.software_error
          }
        }
      }
    },
    deleteRun(datasetId, runId) {
      if (this.display === 'review') {
        this.$emit('remove-run', runId)
        return
      }
      if(datasetId === ""){
        datasetId=null
      }
      this.get(`/grpc/${this.user_id}/run_delete/${datasetId}/${runId}`).then(message => {
        this.$emit('remove-run', runId)
      }).catch(error => {
        this.$emit('add-notification', 'error', error.message)
      })
    },
    evaluateRun(datasetId, runId) {
      if(datasetId === ""){
        datasetId=null
      }
      this.get(`/grpc/${this.user_id}/run_eval/${datasetId}/${runId}`).then(message => {
        this.$emit('poll-evaluations')
      }).catch(error => {
        this.$emit('add-notification', 'error', error.message)
      })
    }
  },
  mounted() {
  },
  beforeMount() {
    this.runningEvaluationIds = this.running_evaluations.map(e => {return e.run_id})
  }
}
</script>