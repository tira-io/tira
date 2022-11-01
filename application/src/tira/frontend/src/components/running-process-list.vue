<template>
<div class="uk-card uk-card-body uk-card-default uk-card-small">
    <ul data-uk-accordion>
        <li v-for="process in running_software" class="uk-margin-small-top">
            <a class="uk-accordion-title" href="#">
                <a 
                    uk-tooltip="Abort run"
                    class="uk-margin-medium-right"
                    onclick="event.stopPropagation()"
                    @click="stopRun(process.run_id)">
                    <font-awesome-icon v-if="!aborting" class="uk-text-danger" icon="fas fa-ban"/>
                    <font-awesome-icon v-else-if="aborting" icon="fas fa-ban" spin/>
                </a>
                <span class="uk-lead">{{ process.run_id }}&nbsp;</span>
                <span class="uk-text-small uk-text-muted uk-margin-medium-right">{{ process.started_at }}</span>
                <span class="uk-margin-medium-right" v-for="(state, label) in process.execution">
                    <span class="uk-margin-small-right"
                          :class="{ 'uk-text-muted': state === 'pending', 'uk-text-small': state === 'pending'}">{{ label }}
                        <span v-if="state==='pending'" class="uk-text-small uk-text-muted">&nbsp;pending</span>
                    </span>
                    <font-awesome-icon v-if="state === 'done'" class="uk-text-success" icon="fas fa-check"/>
                    <font-awesome-icon v-else-if="state === 'running'" icon="fas fa-circle-notch" spin/>
                    <font-awesome-icon v-else-if="state === 'failed'" class="uk-text-danger" icon="fas fa-times"/>
                </span>
            </a>
            <div class="uk-accordion-content">
                <textarea class="uk-textarea" rows="10" placeholder="No Output recorded." disabled>
                    {{ process.stdOutput }}
                </textarea>
            </div>
        </li>
    </ul>
</div>
</template>

<script>
export default {
  name: "running-process-list",
  props: ["running_evaluations", "running_software"],
  emits: ['stoprun', 'addnotification'],
  data() {
    return {
      aborting: false,
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
        this.aborting = true
        this.$emit('stoprun', run_id)
    },
  }
}
</script>
