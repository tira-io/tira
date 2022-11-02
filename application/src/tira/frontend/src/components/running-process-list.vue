<template>
<div class="uk-card uk-card-body uk-card-default uk-card-small">
    <h3>Running Processes</h3>
    <ul data-uk-accordion>
        <li v-for="process in running_software" class="uk-margin-remove">
            <a class="uk-accordion-title" href="#">
                <table>
                    <tr>
                        <td class="uk-table-shrink uk-text-nowrap">
                            <span class="uk-lead">{{ get_field(process, "software_name") }}&nbsp;</span>
                            <span class="uk-text-small uk-text-muted uk-margin-medium-right">{{ process.run_id }}</span>
                        </td>
                        <td class="uk-table-expand"></td>
                        <td class="uk-table-shrink uk-text-nowrap uk-preserve-width" v-for="(state, label) in process.execution">
                            <span class="uk-margin-small-right"
                                  :class="{ 'uk-text-muted': state === 'pending', 'uk-text-small': state === 'pending'}">{{ label }}
                                <span v-if="state==='pending'" class="uk-text-small uk-text-muted">&nbsp;pending</span>
                            </span>
                            <span class="uk-margin-medium-right">
                                <font-awesome-icon v-if="state === 'done'" class="uk-text-success" icon="fas fa-check"/>
                                <font-awesome-icon v-else-if="state === 'running'" icon="fas fa-circle-notch" spin/>
                                <font-awesome-icon v-else-if="state === 'failed'" class="uk-text-danger" icon="fas fa-times"/>
                            </span>
                        </td>
                        <td class="uk-width-1-5"></td>
                    </tr>
                </table>


            </a>
            <div class="uk-accordion-content uk-background-muted">
                <div class="uk-container uk-margin-medium uk-padding-medium">
                    <div class="uk-grid-small uk-padding-small" data-uk-grid>
                        <div>
                            <label class="uk-form-label">Pipeline Name
                            <input class="uk-input" type="text"
                                   :value="process.pipeline_name" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-auto">
                            <label class="uk-form-label">Started
                            <input class="uk-input" type="text"
                                   :value="process.started_at" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-expand"></div>
                        <div class="uk-width-auto">
                            <label class="uk-form-label">&nbsp;
                            <a uk-tooltip="Abort run"
                                 class="uk-button uk-button-default uk-margin-small-right uk-button-small"
                                 @click="stopRun(process.run_id)"><!--                             onclick="event.stopPropagation()"-->
                                <font-awesome-icon v-if="!(this.aborted_processes.includes(process.run_id))" class="uk-text-danger" icon="fas fa-ban"/>
                                <font-awesome-icon v-else-if="this.aborted_processes.includes(process.run_id)" icon="fas fa-ban" spin/>
                            </a></label>
                        </div>
                    </div>

                    <div class="uk-grid-small uk-padding-small uk-margin-remove-top" data-uk-grid>
                        <div class="uk-width-expand">
                            <label class="uk-form-label">Dataset
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'dataset')" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-1-5">
                            <label class="uk-form-label">Dataset Type
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'dataset_type')" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-auto">
                            <label class="uk-form-label">CPU
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'cores')" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-auto">
                            <label class="uk-form-label">Memory
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'ram')" readonly disabled>
                            </label>
                        </div>
                    </div>

                    <div class="uk-grid-small uk-padding-small uk-margin-remove-top" data-uk-grid>
                        <div class="uk-width-1-2">
                            <label class="uk-form-label">Image
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'image')" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-1-2">
                            <label class="uk-form-label">Command
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'command')" readonly disabled>
                            </label>
                        </div>
                    </div>

                    <div class="uk-padding-small">
                        <label class="uk-form-label">Software Output
                        <pre>{{ process.stdOutput }}</pre>
                        </label>
                    </div>
                </div>
            </div>
          <hr class="uk-margin-small">
        </li>
    </ul>
</div>
</template>

<style scoped>
pre {
  overflow: auto;
  max-height: 15em;
}
</style>

<script>
export default {
  name: "running-process-list",
  props: ["running_evaluations", "running_software"],
  emits: ['stopRun', 'addNotification'],
  data() {
    return {
      aborted_processes: [],
      executionIndicator(key, label) {
        console.log(key, label)
        if (key === 'done') {
             return `${label} <font-awesome-icon class="uk-text-success" icon="fas fa-check"/>`
        } else if (key === 'running') {
             return `${label} <font-awesome-icon icon="far fa-circle-notch" spin/>`
        } else if (key === 'pending') {
             return ''
        } else if (key === 'failed') {
             return `${label} <font-awesome-icon class="uk-text-danger" icon="fas fa-times"/>`
        }
        return ''
      }
    }
  },
  methods: {
    stopRun(run_id) {
      if(!(this.aborted_processes.includes(run_id))) {
        this.aborted_processes.push(run_id)
        this.$emit('stopRun', run_id)
      }
    },
    /**
     * Helper function, because the job config is sometimes not there
     */
    get_field(process, field) {
        if (typeof(process.job_config) != 'undefined') {
          return process.job_config[field]
        }
        return ""
    },
  },
  beforeMount() {
    console.log(this.running_software)
  }
}
</script>
