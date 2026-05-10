# RainClaw

永远使用中文回复。

## 项目概述
RainClaw 是一个 AI Agent 平台，全栈架构：FastAPI + MongoDB 后端，Vue 3 + TypeScript 前端。

## 技术栈
- **后端**: FastAPI, MongoDB (motor), Pydantic, LangChain
- **前端**: Vue 3, TypeScript, Vite, Tailwind CSS, vue-i18n, vue-router, axios
- **图标**: lucide-vue-next
- **Toast**: showSuccessToast / showErrorToast from @/utils/toast

## 代码约定
- Vue 组件用 `<script setup lang="ts">` 组合式 API
- API 模块: `apiClient.get<ApiResponse<T>>()` → `.data.data`
- i18n: 扁平 key-value, key=英文, zh.ts=中文, en.ts=英文
- 所有页面路由是 `/chat` 的子路由, `meta: { requiresAuth: true }`
- 后端路由前缀 `/api/v1/`, ApiResponse 统一格式 `{ code, msg, data }`
- 管理员权限: 前端 `v-if="isAdmin"` + 后端 `_require_admin()`

## 完整项目上下文
参阅 `docs/project-context.md` 获取详细的项目结构、代码模式和注意事项。

## Epic 1 已完成
数据源配置管理（CRUD + 菜单 + i18n），详情见 `_bmad-output/implementation-artifacts/`
