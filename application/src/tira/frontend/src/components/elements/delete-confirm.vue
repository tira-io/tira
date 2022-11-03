<template>
<a :uk-tooltip="tooltip"
     class="uk-button uk-button-danger uk-button-small"
     uk-toggle="target: #delete-confirm-modal"
     @click="">
    {{ actionTitle }}
    &nbsp;
    <font-awesome-icon v-if="!inProgress && icon==='trash'" icon="fas fa-trash"/>
    <font-awesome-icon v-else-if="!inProgress && icon==='cancel'" icon="fas fa-ban"/>
    <font-awesome-icon v-else-if="inProgress" icon="fas fa-circle-notch" spin/>
</a>
<div id="delete-confirm-modal" uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-width-large">
        <p>
          <span class="uk-text-danger">Danger Zone!</span> Please confirm that you want to {{ actionTitle }}.
        </p>
        <div class="uk-position-bottom-center uk-position-medium uk-margin-small-bottom">
            <button class="uk-button uk-button-default uk-modal-close" type="button">Cancel</button>
            <button class="uk-button uk-button-danger" type="button"
                    @click="$emit('confirmation')">{{ actionTitle }}</button>
        </div>
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
  inProgress: Boolean
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
  tooltip() {
    return `title: ${this.tooltip}; delay: 1`
  }
}
}
</script>