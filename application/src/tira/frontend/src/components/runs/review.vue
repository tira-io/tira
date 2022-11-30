<template>
<!--  If this is on its own page -->
<nav class="uk-container" v-if="render_as==='fullpage'">
    <ul class="uk-breadcrumb">
        <li><a href="{% url 'tira:index' %}">Tira.io</a></li>
        <li><a href="{% url 'tira:task' task_id=task_id %}">{{ task_id }}</a></li>
        <li><a href="{% url 'tira:dataset' task_id=task_id dataset_id=dataset_id %}">{{ dataset_id }}</a></li>
        <li><a href="{% url 'tira:software-detail' task_id=task_id user_id=user_id %}">{{ user_id }}</a></li>
        <li class="uk-disabled"><a href="#">{{ run_id }}</a></li>
    </ul>
</nav>

<!-- Overview - always shown   -->
<div class="uk-container uk-margin-small">
    <div class="uk-container uk-margin-small">
        <h2>
            <span uk-tooltip="This run is on the leaderboard" v-if="isOnLeaderboard" class="dataset-detail-icon uk-text-success uk-margin-small-right">
                <font-awesome-icon icon="fas fa-sort-amount-up" />
            </span>
            <span uk-tooltip="This run is NOT on the leaderboard" v-else class="dataset-detail-icon uk-text-muted uk-margin-small-right">
                <font-awesome-icon icon="fas fa-sort-amount-up" />
            </span>
            <span uk-tooltip="This run IS visible to the participant" v-if="isVisibleToParticipant" class="dataset-detail-icon uk-text-success uk-margin-small-right">
                <font-awesome-icon icon="fas fa-eye" />
            </span>
            <span uk-tooltip="This run is NOT visible to the participant" v-else class="dataset-detail-icon uk-text-muted uk-margin-small-right">
                <font-awesome-icon icon="fas fa-eye-slash" />
            </span>
            <span class="uk-text-muted">{{ run_id }}</span> <span class="uk-text-lead">Details</span>
        </h2>
    </div>

    <div class="uk-container uk-margin-small">
        <div class="uk-grid-small" data-uk-grid>
            <!-- Details -->
            <div class="uk-card uk-card-body uk-card-default uk-card-small uk-width-1-2">
                <table class="">
                    <tr>
                        <td><strong>Software:</strong></td>
                        <td>{{ run.software }}</td>
                    </tr>
                    <tr>
                        <td><strong>Run:</strong></td>
                        <td>{{ run_id }}</td>
                    </tr>
                    <tr>
                        <td><strong>Input Dataset:</strong></td>
                        <td>{{ dataset_id }}</td>
                    </tr>
                    <tr v-if="run.input_run_id !== ''">
                        <td><strong>Input Run:</strong></td>
                        <td>{{ run.input_run_id }}</td>
                    </tr>
                    <tr v-if="!this.run.is_evaluation">
                        <td><strong>Time:</strong></td>
                        <td>{{ runtime.time }}</td>
                    </tr>
                    <tr v-if="!this.run.is_evaluation">
                        <td><strong>CPU Load:</strong></td>
                        <td>{{ runtime.cpu }}</td>
                    </tr>
                    <tr v-if="!this.run.is_evaluation">
                        <td><strong>Page Faults:</strong></td>
                        <td>{{ runtime.pagefaults }}</td>
                    </tr>
                    <tr v-if="!this.run.is_evaluation">
                        <td><strong>Swaps:</strong></td>
                        <td>{{ runtime.swaps }}</td>
                    </tr>
                </table>
            </div>
            <!-- Run Review Display -->
            <div class="uk-card uk-card-body uk-card-default uk-card-small uk-width-1-2">
                <h3 class="uk-card-title uk-width-1-1 uk-margin-small">
                    <div class="uk-grid-small uk-margin-small" uk-grid>
                        <span>Review</span>
                        <div class="uk-width-expand"></div>
                        <div>
<!--                              TODO: make a component out of this button -->
                            <div class="uk-button uk-button-default uk-margin-small-right uk-button-small"
                               :class="{ 'flash-red': saveFailed, 'flash-green': saveSuccess }"
                               @click="submitReview()"
                               v-if="role==='admin'">
                            <font-awesome-icon icon="fas fa-save" />
                          </div>
                        </div>
                    </div>
                </h3>
                <form>
                    <input type="hidden" name="csrfmiddlewaretoken" value="{{ csrf }}">  <!-- TODO: this might not be needed anymore -->
                    <div class="uk-grid-small" data-uk-grid>
                        <label class="uk-form-label uk-margin-small uk-margin-small-top">
                          <input class="uk-checkbox" type="checkbox" v-model="no_errors" :disabled="role!=='admin'">
                          No Errors</label>&nbsp;
                        <label class="uk-form-label uk-margin-small">
                          <input class="uk-checkbox" type="checkbox" v-model="output_error" :disabled="role!=='admin'">
                          Output Error</label>
                        <label class="uk-form-label uk-margin-small">
                          <input class="uk-checkbox" type="checkbox" v-model="software_error" :disabled="role!=='admin'">
                          Software Error</label>
                    </div>
                    <div class="uk-margin-small uk-width-1-1">
                        <label class="uk-form-label">Comment
                        <textarea rows="5" class="uk-textarea" placeholder="Task Description"
                               v-model="comment" :disabled="role!=='admin'"/> </label>
                        <p class="uk-text-danger uk-margin-small" v-if="reviewFormError!==''">{{ reviewFormError }}</p>
                        <p class="uk-text-success uk-margin-small" v-if="reviewer!==''">Reviewed by <strong>{{ reviewer }}</strong>.</p>
                        <p class="uk-text-warning uk-margin-small" v-else>This run was <em>not</em> reviewed yet.</p>
                    </div>
                </form>
            </div>
        </div>
<!--  Admin options below the review card -->
        <table class="uk-width-expand">
            <tr>
                <td class="uk-table-expand"></td>
                <td class="uk-table-shrink uk-text-nowrap" v-if="run.is_evaluation">
                    <button class="uk-button uk-button-small"
                            :class="{ 'uk-button-disabled': !canSubmit, ' uk-button-default': canSubmit, 'uk-text-muted': !canSubmit }"
                            @click="togglePublish()" :disabled="!canSubmit">
                        <span v-if="!isOnLeaderboard && canSubmit">Submit to leaderboard</span>
                        <span v-else-if="isOnLeaderboard">Remove from leaderboard</span>
                        <span v-else data-uk-tooltip="title: Evaluation must be valid to be submitted.">
                          Submit to leaderboard</span>
                        <span class="uk-margin-small-left uk-margin-small-right">
                          <font-awesome-icon icon="fas fa-sort-amount-up"
                              :class="{'uk-text-success': isOnLeaderboard}" />
                        </span>
                    </button>
                </td>
                <td class="uk-table-shrink uk-text-nowrap" v-if="role==='admin'">
                  <button class="uk-button uk-button-default uk-button-small" @click="toggleVisible()">
                      <span v-if="!isVisibleToParticipant">Reveal to Participant</span><span v-else>Hide from participant</span>
                      <span class="uk-margin-small-left uk-margin-small-right">
                        <font-awesome-icon class="uk-text-success" icon="fas fa-eye" v-if="isVisibleToParticipant"/>
                        <font-awesome-icon icon="fas fa-eye-slash" v-else/>
                      </span>
                  </button>
                </td>
                <td class="uk-table-shrink uk-text-nowrap">
                    <a class="uk-button uk-button-small uk-button-default"
                       v-if="role==='admin' || !dataset.is_confidential || isVisibleToParticipant"
                           target="_blank"
                           :href="'/task/' + task_id + '/user/' + user_id + '/dataset/' + dataset_id + '/download/' + run.run_id + '.zip'">
                      <span class="uk-margin-small-left uk-margin-small-right">Download <font-awesome-icon icon="fas fa-download" /></span>
                    </a>
                    <a class="uk-button uk-button-small uk-button-disabled uk-text-muted" disabled v-else
                           uk-tooltip="title: Can only be downloaded if the run is unblinded.; delay: 500">
                      <span class="uk-margin-small-left uk-margin-small-right">Download <font-awesome-icon icon="fas fa-download" /></span>
                    </a>
                </td>
            </tr>
        </table>
    </div>


    <div class="uk-container uk-margin-small">
        <h2>
          <span class="uk-text-muted">Output</span>
        </h2>
        <button class="uk-button uk-button-default uk-button-small" v-if="evaluation!==null" v-show="role==='admin' || isVisibleToParticipant"
              @click="selecedOutput='evaluation'"
              :class="{ 'tira-button-selected': selecedOutput === 'evaluation' }">
                Results</button>
        <button class="uk-button uk-button-default uk-button-small"
              @click="selecedOutput='files'"
              :class="{ 'tira-button-selected': selecedOutput === 'files' }">
                Files</button>
        <button class="uk-button uk-button-default uk-button-small"
                @click="selecedOutput='stdout'"
                :class="{ 'tira-button-selected': selecedOutput === 'stdout' }">
                  Software Log</button>
        <button class="uk-button uk-button-default uk-button-small"
              @click="selecedOutput='stderr'"
              :class="{ 'tira-button-selected': selecedOutput === 'stderr' }">
                Error Log</button>
        <button class="uk-button uk-button-default uk-button-small" v-if="role==='admin'"
              @click="selecedOutput='logs'"
              :class="{ 'tira-button-selected': selecedOutput === 'logs' }">
                Tira Logs</button>

        <!-- Output -->
        <div class="uk-card uk-card-body uk-card-default uk-card-small" v-if="selecedOutput==='evaluation'">
            <pre>{{ evaluation }}</pre>
        </div>

        <!-- Output -->
        <div class="uk-card uk-card-body uk-card-default uk-card-small" v-if="selecedOutput==='files'">
            <div>
                <table>
                    <tr>
                        <td><strong>Size:</strong> </td><td>{{ files.size }}</td>
                    </tr>
                    <tr>
                        <td><strong>Lines:</strong></td><td> {{ files.lines }}</td>
                    </tr>
                    <tr>
                        <td><strong>Files:</strong></td><td> {{ files.files }}</td>
                    </tr>
                </table>
            </div>
            <div v-if="files.file_list.length!==0"></div>
            <pre>{{ fileList }}</pre>
        </div>

        <!-- Show Stdout -->
        <div class="uk-card uk-card-body uk-card-default uk-card-small" v-if="selecedOutput==='stdout'">
          <pre v-if="!isVisibleToParticipant && dataset.is_confidential" disabled>
The Software Log has not been revealed to participants yet. Contact your task's organizer for a review.
          </pre>
          <pre v-else>{{ stdout }}</pre>
        </div>

        <!-- Show Stderr -->
        <div class="uk-card uk-card-body uk-card-default uk-card-small" v-if="selecedOutput==='stderr'">
            <pre v-if="!isVisibleToParticipant && dataset.is_confidential">
The Software Log has not been revealed to participants yet. Contact your task's organizer for a review.
            </pre>
            <pre v-else>{{ stderr }}</pre>
        </div>

        <!-- Show Tira log -->
        <div class="uk-card uk-card-body uk-card-default uk-card-small" v-if="selecedOutput==='logs'">
            <pre>{{ tira_log }}</pre>
        </div>
    </div>
</div>
</template>

<style scoped>
pre {
  overflow: auto;
  max-height: 15em;
}
</style>

<script>
import { get, submitPost } from "../../utils/getpost";

export default {
  name: "review",
  data() {
    return {
      role: "guest",
      run: {},
      runtime: {},
      isOnLeaderboard: false,
      isVisibleToParticipant: false,
      dataset: {},
      files: {file_list: []},
      no_errors: false,
      output_error: false,
      software_error: false,
      reviewer: "",
      comment: "",
      reviewFormError: "",
      stdout: "",
      stderr: "",
      tira_log: "",
      selecedOutput: 'files',
      saveSuccess: false,
      saveFailed: false,
      evaluation: null
    }
  },
  props: {
    /**
     * @value modal, fullpage
     */
    render_as: {
      type: String,
      default: 'modal'
    },
    task_id: String,
    user_id: String,
    dataset_id: String,
    run_id: String,
    csrf: String,
  },
  emits: ['add-notification', 'update-review'],
  methods: {
    submitPost: submitPost,
    get: get,
    toggleSaveTimeout(){
        this.saveSuccess = false
        this.saveFailed = false
    },
    submitReview() {
      this.submitPost(`/tira-admin/edit-review/${this.dataset_id}/${this.user_id}/${this.run_id}`, this.csrf,{
            'no_errors': this.no_errors,
            'output_error': this.output_error,
            'software_error': this.software_error,
            'comment': this.comment,
        }).then(message => {
          this.saveSuccess = true
          const toggleSaveTimeout = setTimeout(this.toggleSaveTimeout, 3000)
          this.$emit('update-review', this.review)
        }).catch(error => {
          this.saveFailed = true
          this.reviewFormError = error
        })
    },
    togglePublish(){
      this.isOnLeaderboard = !this.isOnLeaderboard
      this.get(`/publish/${this.user_id}/${this.dataset_id}/${this.run_id}/${this.isOnLeaderboard}`).then(message => {
          this.$emit('update-review', this.review)
      }).catch(error => {
        this.isOnLeaderboard = !this.isOnLeaderboard
        this.reviewFormError = error
      })
    },
    toggleVisible(){
      this.isVisibleToParticipant = !this.isVisibleToParticipant
      this.get(`/blind/${this.user_id}/${this.dataset_id}/${this.run_id}/${!this.isVisibleToParticipant}`).then(message => {  // negate because the semantics of the endpoint is the other way around
          this.$emit('update-review', this.review)
      }).catch(error => {
        this.isVisibleToParticipant = !this.isVisibleToParticipant
        this.reviewFormError = error
      })
    }
  },
  computed: {
    fileList() {
      if (this.files.file_list.length === 0) {
        return ""
      }
      return this.files.file_list.reduce((a, b) => {
        return `${a}\n${b}`.replace(/\./g, ' ')
        })
    },
    review() {
      return {
        user_id: this.user_id,
        run_id: this.run.run_id,
        isOnLeaderboard: this.isOnLeaderboard,
        isVisibleToParticipant: this.isVisibleToParticipant,
        no_errors: this.no_errors,
        output_error: this.output_error,
        software_error: this.software_error,
        reviewer: this.review,
        comment: this.comment,
      }
    },
    canSubmit() {
      if (this.no_errors) return true
      return !(this.evaluation === null || this.evaluation === false ||
          this.evaluation === "" || this.evaluation === "{}" ||
          Object.keys(this.evaluation).length === 0 ||
          Object.getPrototypeOf(this.evaluation) === Object.prototype)
    }
  },
  mounted() {
    this.get(`/api/review/${this.dataset_id}/${this.user_id}/${this.run_id}`).then(message => {
      this.run = message.context.run
      this.runtime = message.context.runtime
      this.reviewer = message.context.review.reviewer
      this.isOnLeaderboard = message.context.review.published
      this.isVisibleToParticipant = !message.context.review.blinded
      this.dataset = message.context.dataset
      this.files = message.context.files
      this.no_errors = message.context.review.noErrors
      this.output_error = message.context.review.outputErrors
      this.software_error = message.context.review.softwareErrors
      this.comment =  message.context.review.comment
      this.reviewFormError = ""
      this.stdout = message.context.stdout
      this.stderr = message.context.stderr
      this.tira_log = message.context.tira_log
      if (this.run.is_evaluation) {
        this.get(`/api/evaluation/${this.user_id}/${this.run_id}`).then(message => {
          this.evaluation = message.context.evaluation
          this.selecedOutput = 'evaluation'
        })
      }
    }).catch(error => {
      this.$emit('add-notification', 'error', error)
    })

    this.get('/api/role').then(message => {
      this.role = message.role
    }).catch(error => {
      this.$emit('add-notification', 'error', error)
    })
  },
  watch: {
    no_errors(newValue, oldValue) {
      if (newValue){
        this.output_error = false
        this.software_error = false
      }
    },
    output_error(newValue, oldValue) {
      if (newValue){
        this.no_errors = false
      }
    },
    software_error(newValue, oldValue) {
      if (newValue){
        this.no_errors = false
      }
    },
  }
}
</script>
