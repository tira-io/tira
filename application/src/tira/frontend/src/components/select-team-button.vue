<template>
    <span v-if="userVmsForTask && userVmsForTask.length > 1">
        <a :disabled="!selectTeam" v-bind:class="(rendering == 'long')?'uk-button uk-button-primary uk-text-large':''">
            <font-awesome-icon v-if="rendering == 'short'"  icon="fas fa-cog" />
            <span v-if="rendering == 'long'"><font-awesome-icon icon="fas fa-terminal" class="uk-margin-right" />Submit</span>
        </a>

        <div v-if="!selectTeam" class="uk-card uk-card-body uk-card-default"
             data-uk-drop="pos: right-top; mode: click">
            <p style="text-align: center" class="uk-margin-small uk-padding-small">
                Submit as:
                <ul>
                    <li v-for="vm in userVmsForTask"><a :href="'/task/' + this.taskId + '/user/' + vm">{{  vm  }}</a></li>
                </ul>
            </p>
        </div>
    </span>
</template>
<script>

export default {
  name: "select-team-button",
  props: {
    taskId: String,
    userVmsForTask: Array,
    rendering: String,
  },
}
</script>
