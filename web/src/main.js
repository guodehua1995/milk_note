import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 引入全局样式
import './styles/variables.css'
import './styles/buttons.css'
import './styles/form-elements.css'
import './styles/responsive.css'

createApp(App).use(router).mount('#app')
