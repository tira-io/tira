<template>
    <a :uk-tooltip="tip"
         class="uk-button uk-button-small uk-padding-small-right"
        :class="{ 'uk-button-danger': !disable,
                   'uk-button-default': disable,
                   'uk-text-muted': disable,}"
        type="button"
        :disabled="disable">
        {{ actionTitle }}
        &nbsp;
        <font-awesome-icon v-if="!inProgress && icon==='trash'" icon="fas fa-trash"/>
        <font-awesome-icon v-else-if="!inProgress && icon==='cancel'" icon="fas fa-ban"/>
        <font-awesome-icon v-else-if="inProgress" icon="fas fa-circle-notch" spin/>
        &nbsp;
    </a>
    <div v-if="!disable" class="uk-card uk-card-body uk-card-default"
                data-uk-drop="pos: right-top; mode: click">
      <p style="text-align: center" class="uk-margin-small uk-padding-small">
        <span class="uk-text-danger">Danger Zone!</span> Please confirm that you want to {{ actionTitle }}.
      </p>
      <div class="uk-margin-small" style="text-align: center">
          <button class="uk-button uk-button-danger" type="button"
                  @click="$emit('confirmation')">{{ actionTitle }}</button>
      </div>
  </div>
</template>



<script>
export default {
name: "delete-confirm",
props: {
  /**
   * @value trash, cancel
   */
  icon: {
    type: String,
    default: 'trash'
  },
  tooltip: String,
  inProgress: Boolean,
  disable: {
    type: Boolean,
    default: false
  }
},
emits: ["confirmation"],
computed: {
  actionTitle() {
      if (this.icon === 'trash') {
        return "delete"
      } else if (this.icon === 'cancel') {
        return 'cancel'
      }
  },
  tip() {
    return `title: ${this.tooltip}; delay: 1`
  },
}
}
</script>