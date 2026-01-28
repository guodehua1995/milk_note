# MilkNote 前端项目

这是一个现代化的Vue.js前端项目，为MilkNote应用提供用户认证和聊天功能。

## 项目结构

```
web/
├── public/                    # 静态资源
├── src/                       # 源代码目录
│   ├── api/                   # API服务层
│   ├── components/            # Vue组件
│   ├── config/                # 配置文件
│   ├── assets/                # 静态资源
│   ├── router.js              # 路由配置
│   ├── main.js                # 应用入口
│   └── App.vue                # 根组件
├── package.json              # 项目配置
└── vue.config.js             # Vue CLI配置
```

## 安装依赖

```bash
npm install
```

## 开发环境运行

```bash
npm run serve
```

应用将在 http://localhost:8081/ 启动

## 构建生产版本

```bash
npm run build
```

## 主要功能

- 用户注册/登录
- 实时聊天功能
- 响应式设计
- 现代化UI界面

## 技术栈

- Vue.js 3
- Vue Router 4
- Axios
- CSS3