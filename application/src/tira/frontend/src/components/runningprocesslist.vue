<template>
<div class="uk-card uk-card-body uk-card-default uk-card-small">
    <ul data-uk-accordion>
        <li v-for="process in running_software">
            <a class="uk-accordion-title" href="#">
                <span class="uk-lead">{{ process.run_id }}&nbsp;</span>
                <span class="uk-text-small uk-text-muted uk-margin-medium-right">{{ process.started_at }}</span>
                <span class="uk-margin-medium-right" v-for="(state, label) in process.execution">
                    <span class="uk-margin-small-right"
                          :class="{ 'uk-text-muted': state === 'pending', 'uk-text-small': state === 'pending'}">{{ label }}
                        <span v-if="state==='pending'" class="uk-text-small uk-text-muted">&nbsp;pending</span>
                    </span>
                    <font-awesome-icon v-if="state === 'done'" class="uk-text-success" icon="fas fa-check"/>
                    <font-awesome-icon v-else-if="state === 'running'" icon="fas fa-circle-notch" spin/>
                    <font-awesome-icon v-else-if="state === 'fail'" class="uk-text-danger" icon="fas fa-cross"/>
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
  name: "runningprocesslist",
  props: ["running_evaluations", "running_software"],
  emits: ['addnotification'],
  data() {
    return {
      executionIndicator(key, label) {
        console.log(key, label)
        if (key === 'done') {
             return `${label} <font-awesome-icon class="uk-text-success" icon="fas fa-check"/>`
        } else if (key === 'running') {
             return `${label} <font-awesome-icon icon="far fa-circle-notch" spin/>`
        } else if (key === 'pending') {
             return ''
        } else if (key === 'fail') {
             return `${label} <font-awesome-icon class="uk-text-danger" icon="fas fa-cross"/>`
        }
        return ''
      }
    }
  },
  methods: {
  }
}
</script>