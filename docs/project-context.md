# RainClaw Project Context

## Project Overview

RainClaw is an AI Agent platform with full-stack architecture using FastAPI backend and Vue 3 frontend.

## Tech Stack

### Backend
- **Framework:** FastAPI 0.135.3
- **Database:** MongoDB (motor 3.7.1 async driver)
- **Auth:** JWT with bcrypt password hashing
- **Validation:** Pydantic 2.13.0
- **AI/LLM:** LangChain 1.2.15, LangGraph 1.1.6
- **Server:** Uvicorn 0.44.0
- **Cache:** Redis 7.4.0
- **Logging:** Loguru 0.7.3

### Frontend
- **Framework:** Vue 3.3.4 + TypeScript 5.6
- **Build:** Vite 4.3
- **Styling:** Tailwind CSS 3.3
- **Icons:** lucide-vue-next 0.511
- **i18n:** vue-i18n 9.14
- **Router:** vue-router 4.5
- **State:** Local component state (ref/reactive), no Pinia/Vuex
- **HTTP:** axios 1.8
- **Utils:** @vueuse/core 10.11

## Project Structure

```
rainclaw/
├── backend/
│   ├── main.py              # FastAPI app entry + route registration
│   ├── models/              # Pydantic data models (package)
│   │   ├── __init__.py      # Re-exports all models
│   │   └── datasource.py    # Datasource model
│   ├── route/               # API route modules
│   │   ├── datasources.py   # Datasource CRUD routes
│   │   └── ...              # Other route modules
│   ├── mongodb/
│   │   └── db.py            # MongoDB connection + index setup
│   ├── user/
│   │   └── dependencies.py  # Auth middleware (require_user)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.ts          # Vue app entry + router definition
│   │   ├── api/             # API client modules
│   │   │   ├── client.ts    # Axios instance + interceptors
│   │   │   ├── datasources.ts
│   │   │   └── ...
│   │   ├── components/      # Vue components
│   │   │   ├── LeftPanel.vue
│   │   │   └── ...
│   │   ├── pages/           # Page components (/chat sub-routes)
│   │   │   ├── DatasourcesPage.vue
│   │   │   └── ...
│   │   ├── locales/         # i18n translations
│   │   │   ├── zh.ts
│   │   │   └── en.ts
│   │   ├── composables/     # Vue composables
│   │   │   └── useAuth.ts   # Auth state (isAdmin, etc.)
│   │   ├── utils/
│   │   │   └── toast.ts     # Toast notification helpers
│   │   └── types/
│   └── package.json
└── _bmad-output/
    ├── planning-artifacts/   # PRD, Architecture, UX, Epics
    └── implementation-artifacts/  # Story files, sprint-status, deferred-work
```

## Code Conventions

### API Module Pattern
```typescript
import { apiClient, ApiResponse } from './client';

export async function listItems(): Promise<Item[]> {
  const response = await apiClient.get<ApiResponse<Item[]>>('/items');
  return response.data.data;
}
```
- Always extract `.data.data` from the response
- Response format: `{ code: 0, msg: "success", data: ... }`
- Business errors: `{ code: 400, msg: "...", data: null }`
- The axios response interceptor converts non-zero code to `Promise.reject(ApiError)`
- Error object: `{ code, message, details }`

### Vue Component Pattern
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconName } from 'lucide-vue-next'
import { showSuccessToast, showErrorToast } from '../utils/toast'

const { t } = useI18n()
</script>
```
- Always use Composition API with `<script setup lang="ts">`
- Use `ref()`, `computed()`, `onMounted()` from Vue 3
- Icons from lucide-vue-next (PascalCase component names)
- Tailwind CSS for styling (no scoped CSS unless necessary)
- Toast: `showSuccessToast(msg)` / `showErrorToast(msg)`

### Route Pattern (main.ts)
```typescript
{
  path: 'datasources',
  component: DatasourcesPage,
  meta: { requiresAuth: true }
}
```
- All feature pages are children of `/chat`
- Route guard `requiresAuth: true` for authenticated pages
- Admin-only access enforced at component level (v-if="isAdmin")

### i18n Pattern
- Flat key-value structure (no nesting)
- Keys are English phrases
- zh.ts: `'Key': '中文翻译'`
- en.ts: `'Key': 'English translation'` (or same as key)

### Backend Route Pattern
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/items", tags=["items"])

class ApiResponse(BaseModel):
    code: int = 0
    msg: str = "success"
    data: Any = None

@router.get("", response_model=ApiResponse)
async def list_items(current_user: User = Depends(require_user)):
    _require_admin(current_user)
    # ... logic
    return ApiResponse(data=results)
```
- Prefix all routes under `/api/v1/` (configured in main.py)
- Admin check via `_require_admin()` wrapper
- MongoDB `_id` → `id` mapping: `doc["id"] = str(doc.pop("_id"))`
- Timestamps: Unix int timestamps via `int(time.time())`

## Key Features Implemented

### Epic 1: 数据源配置管理 (Done)
- Datasource CRUD with 5 DB types (MySQL, PostgreSQL, Oracle, MongoDB, SQL Server)
- Admin-only access (v-if="isAdmin" + backend role check)
- Password toggle (eye icon) in list and form
- Name search with fuzzy query
- Code uniqueness validation (frontend + backend)
- Left menu navigation with active state
- Full i18n (zh/en) support

## Technical Debt

See `_bmad-output/implementation-artifacts/deferred-work.md` for full list.
Key items:
- TOCTOU race condition on code uniqueness (low probability)
- NoSQL injection risk in regex search (admin-only mitigated)
- loadList race condition (admin low-concurrency)
- Hardcoded CSS color values (pre-existing pattern)
- toSnakeCase consecutive uppercase edge cases

## Common Gotchas

1. **Password field**: Backend returns passwords in plaintext (NFR3 requirement). Frontend controls visual masking.
2. **v-model.number**: Can produce NaN when field is empty — always validate with `isNaN()` before use.
3. **Form submission**: Form must be wrapped in `<form @submit.prevent>` for Enter key support — HTML `required` attribute alone doesn't work outside `<form>`.
4. **Route conflicts**: `isChatActive` in LeftPanel must explicitly exclude specialized routes (skills, tools, tasks, datasources) to avoid highlight conflicts.
