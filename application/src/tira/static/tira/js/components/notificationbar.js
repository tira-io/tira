export default {
  props: ['notification'],
  template: `
    <div :class="{ 
    'uk-alert-success': notification.type === 'success',
    'uk-alert-primary': notification.type === 'warning',
    'uk-alert-danger': notification.type === 'error',  
    }" uk-alert>
        <a class="uk-alert-close" uk-close></a>
        <p>[[ notification.message ]]</p>
    </div>
</div>`
}