<template>
  <div class="uk-margin-remove" :class="{ 
  'uk-alert-success': notification.type === 'success',
  'uk-alert-primary': notification.type === 'warning',
  'uk-alert-danger': notification.type === 'error',  
  }" uk-alert>
      <a class="uk-alert-close" uk-close></a>
      <p>{{ notification.message }}</p>
  </div>
</template>
<script>
export default {
  props: ['notification'],
}
</script>
