<template>
  <v-alert v-model="alert" @click:close="messageClosed" closable :title="title" :text="text" :type="type" :class="alert && current_element ? 'tira-alert' : 'tira-alert hide-tira-alert'" transition="fade-transition"/>
</template>

<script lang="ts">
export default {
  name: "tira-alert",
  data() { return {messages: [{title: '', text: '', type: ''}], alert: false}},
  computed: {
    type() {
      if (this.current_element === null) return 'error'
      if (this.current_element['type'] !== 'error') return 'success'
      return 'error'
    },
    text() {return (this.current_element || {text: ''} ).text || ''},
    title() {return ((this.current_element || {title: ''} ).title || '') + (this.messages.length <= 1 ? '' : ' (+ ' + (this.messages.length -1) + ' more messages)')},
    current_element() {
        return this.messages.length > 0 ? this.messages[0]: null;
    }
  },
  methods: {
    push_message: function (title: string, text: string, type: string) {
      this.messages.push({title: title, text: text, type: type})
      this.alert = true
      setTimeout(() => {this.messageClosed()}, 5000);
    },
    messageClosed: function () {
        this.messages = this.messages.slice(1)
        setTimeout(() => {this.alert = this.messages.length > 0;}, 10);
    }
  },
  beforeMount() {  
    this.messages = []
    window.push_message = this.push_message
  },
}
</script>
<style>
.tira-alert {
  position: fixed;
  top: 0;
  z-index: 10;
  width: 100%;
  opacity: 0.9;
}
.hide-tira-alert {
  height: 0;
  visibility: hidden;
}
</style>