/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import * as components from 'vuetify/components'
import * as labsComponents from 'vuetify/labs/components'
import { md3 } from 'vuetify/blueprints'

// Composables
import { createApp } from 'vue'
import {createVuetify, ThemeDefinition} from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides

const myCustomLightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    background: '#f2f7f7',
    surface: '#f2f4f7',
    primary: '#6200EE',
    'primary-darken-1': '#3700B3',
    secondary: '#03DAC6',
    'secondary-darken-1': '#018786',
    error: '#B00020',
    info: '#2196F3',
    success: '#4CAF50',
    warning: '#FB8C00',
  },
}

export default createVuetify({
  blueprint: md3,
  components: {
    ...components,
    ...labsComponents,
  },
  theme: {
    defaultTheme: 'myCustomLightTheme',
    themes: {
      myCustomLightTheme,
      light: {
        colors: {
          primary: '#4F81E4'
        },
      },
      dark: {
        colors: {
          primary: '#4F81E4'
        },
      },
    },
  },
})
