import { createApp } from 'vue'
import { MotionPlugin } from '@vueuse/motion'
import './style.css'
import axios from 'axios'
import App from './App.vue'

// Set base URL for axios
axios.defaults.baseURL = '/onto_hub'

const app = createApp(App)

app.use(MotionPlugin)

app.mount('#app')
