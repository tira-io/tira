<template>
<a class="uk-button uk-button-small uk-button-default uk-background-default" @click="toggleModal">
    <font-awesome-icon icon="fas fa-search" />
    REVIEW</a>
<div :id="modalId" class="uk-container uk-container-expand" data-uk-modal>
    <div class="uk-modal-dialog uk-modal-body uk-width-expand">
        <button class="uk-modal-close-default" type="button" data-uk-close></button>
        <review :task_id="task_id" :user_id="user_id" :dataset_id="dataset_id" :run_id="run_id" :csrf="csrf" v-if="show"
                @add-notification="(type, message) => this.$emit('addNotification', type, message)"
                @update-review="newReview => this.$emit('updateReview', newReview)"/>
    </div>
</div>
</template>

<script>
import Review from "../runs/review";
export default {
  name: "review-button",
  props: {
    task_id: String,
    user_id: String,
    dataset_id: String,
    run_id: String,
    csrf: String,
  },
  data() {
    return {
      show: false,
    }
  },
  methods: {
    toggleModal() {
      this.show = !this.show
      const reviewModal = document.getElementById(this.modalId)

      if (this.show){
        UIkit.modal(reviewModal).show();
      } else {
        UIkit.modal(reviewModal).hide();
      }

    },
  },
  emits: ['addNotification', 'updateReview'],
  components: {
    Review
  },
  computed: {
    modalId() {
      return `modal-${this.run_id}`
    },
    modalTarget() {
      return `target: #modal-${this.run_id}`
    },

  }
}
</script>
