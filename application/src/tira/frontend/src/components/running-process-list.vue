<template>
<div class="uk-card uk-card-body uk-card-default uk-card-small">
    <div class="uk-grid-medium" uk-grid>
      <div class="uk-text-lead uk-width-1-2">Running Processes &nbsp;</div>
      <div class="uk-text-light uk-width-1-4">| Last Cache Refresh: {{ last_software_refresh }}&nbsp;</div>
      <div class="uk-text-light uk-width-1-4">| Next Cache Refresh: {{ next_software_refresh }}</div>
    </div>
    <hr class="uk-margin-small">
    <ul class="uk-margin-remove-top" data-uk-accordion>
        <li v-for="process in running_software" class="uk-margin-remove">
            <a class="uk-accordion-title" href="#">
                <table>
                    <tr>
                        <td class="uk-table-shrink uk-text-nowrap">
                            <span class="uk-lead">{{ get_field(process, "software_name") }}&nbsp;</span>
                            <span class="uk-text-small uk-text-muted uk-margin-medium-right">{{ process.run_id }}</span>
                        </td>
                        <td class="uk-table-expand"></td>
                        <td class="uk-table-shrink uk-text-nowrap uk-width-1-6" v-for="(state, label) in process.execution">
                            <span class="uk-margin-small-right uk-text-small"
                                  :class="{ 'uk-text-muted': state === 'pending'}">{{ label }}
                                <span v-if="state==='pending'" class="uk-text-small uk-text-muted">&nbsp;pending</span>
                            </span>
                            <span class="uk-margin-medium-right">
                                <font-awesome-icon v-if="state === 'done'" class="uk-text-success" icon="fas fa-check"/>
                                <font-awesome-icon v-else-if="state === 'running'" icon="fas fa-circle-notch" spin/>
                                <font-awesome-icon v-else-if="state === 'failed'" class="uk-text-danger" icon="fas fa-times"/>
                            </span>
                        </td>
                        <td class="uk-width-1-6"></td>
                    </tr>
                </table>
            </a>
            <div class="uk-accordion-content uk-background-muted">
                <div class="uk-container uk-margin-medium uk-padding-medium">
                    <div class="uk-width-1-1 uk-margin-remove" data-uk-grid>
                        <div class="uk-width-expand"></div>
                        <div class="uk-width-auto">
                            <delete-confirm
                                tooltip="Abort run"
                                icon="cancel"
                                :in-progress="(aborted_processes.includes(process.run_id))"
                                @confirmation="() => stopRun(process.run_id)"
                            />
                        </div>
                    </div>
                    <div class="uk-grid-small uk-padding-small uk-margin-remove-top" data-uk-grid>
                        <div class="uk-width-1-2">
                            <label class="uk-form-label">Image
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'image')" readonly disabled>
                            </label>
                            <label class="uk-form-label">Command
                            <input class="uk-input" type="text"
                                   :value="get_field(process, 'command')" readonly disabled>
                            </label>
                        </div>
                        <div class="uk-width-1-2">
                            <table class="uk-width-expand">
                                <tr><td><strong>Started</strong></td><td>{{ process.started_at }}</td></tr>
                                <tr><td><strong>Dataset</strong></td><td>{{ get_field(process, 'dataset') }}</td></tr>
                                <tr><td><strong>Dataset Type</strong></td><td>{{ get_field(process, 'dataset_type') }}</td></tr>
                                <tr><td><strong>CPU</strong></td><td>{{ get_field(process, 'cores') }}</td></tr>
                                <tr><td><strong>Memory</strong></td><td>{{ get_field(process, 'ram') }}</td></tr>
                                <tr><td><strong>GPU</strong></td><td>{{ get_field(process, 'gpu') }}</td></tr>
                            </table>
                        </div>
                    </div>

                    <div class="uk-padding-small uk-padding-remove-top">
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
import DeleteConfirm from "./elements/delete-confirm";
export default {
  name: "running-process-list",
  components: {DeleteConfirm},
  props: ["running_evaluations", "running_software", "last_software_refresh", "next_software_refresh"],
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
        if ("job_config" in process) {
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
