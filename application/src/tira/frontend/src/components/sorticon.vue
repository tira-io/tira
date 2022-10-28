<template>
<font-awesome-icon icon="fas fa-sort" class="uk-text-muted" v-if="row_key!==selected_key" />
<!-- ascending icons -->
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-up" v-else-if="direction==='asc' && icon_type==='arrow'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-amount-up" v-else-if="direction==='asc' && icon_type==='bar'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-alpha-up" v-else-if="direction==='asc' && icon_type==='letter'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-numeric-up" v-else-if="direction==='asc' && icon_type==='number'" />
<!-- descending icons -->
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-down" v-else-if="direction==='desc' && icon_type==='arrow'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-amount-down" v-else-if="direction==='desc' && icon_type==='bar'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-alpha-down" v-else-if="direction==='desc' && icon_type==='letter'" />
<font-awesome-icon class="uk-text-default" icon="fas fa-sort-numeric-down" v-else-if="direction==='desc' && icon_type==='number'" />
</template>

<script>
export default {
  name: "sorticon",
  props: {
    row_key: String,
    /**
     * The key of the row which the table should be sorted after
     */
    selected_key: String,
    /**
     * @values asc, desc
     */
    direction: {
      type: String,
      default: 'desc'
    },
    /**
     * which icons to use when sorted
     * @values: bar, arrow, letter, number
     */
    icon_type: {
      type: String,
      default: 'arrow'
    }
  },
}
</script>