import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'

// 样式顺序：先加载 Element Plus 基础样式，再用项目自有像素风主题覆盖
import 'element-plus/dist/index.css'
import './styles/pixel.css'

/**
 * Element Plus 必须在此全局注册。
 * 此前只有部分页面 import 了 ElMessage 等 API，组件本身从未注册，
 * 导致 Social / Writing / Distribution / Monitoring 等使用 <el-table> 的页面
 * 渲染时报 "Cannot destructure property 'row' of 'undefined'"，整页白屏。
 */
const app = createApp(App)
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
