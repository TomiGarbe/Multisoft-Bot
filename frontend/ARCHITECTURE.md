# Frontend Architecture - Multisoft Bot Admin Panel

## Structure Overview

This frontend is built with Next.js 16 using the App Router and is organized with Route Groups for better code organization.

### Directory Structure

```
src/
├── app/
│   ├── (auth)/               # Authentication route group (public)
│   │   └── login/
│   │       └── page.tsx      # Login page
│   │
│   ├── (dashboard)/          # Protected dashboard route group
│   │   ├── layout.tsx        # Layout with auth protection, sidebar & header
│   │   ├── dashboard/
│   │   │   └── page.tsx      # Dashboard home page
│   │   ├── users/
│   │   │   └── page.tsx      # Users management (placeholder)
│   │   ├── roles/
│   │   │   └── page.tsx      # Roles management (placeholder)
│   │   └── permissions/
│   │       └── page.tsx      # Permissions management (placeholder)
│   │
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Root page (redirects to login or dashboard)
│   └── globals.css           # Global styles
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   └── Header.tsx        # Top header with user info and logout
│   ├── Layout.tsx            # Legacy - can be removed
│   └── ... (other components)
│
├── hooks/
│   ├── useAuth.ts            # Authentication state management
│   └── ... (other hooks)
│
├── services/
│   ├── api.ts                # Axios instance with interceptors
│   ├── auth.ts               # Authentication service functions
│   └── ... (other services)
│
├── lib/
│   ├── auth.ts               # Token management (localStorage)
│   └── utils.ts
│
└── types/
    └── ... (TypeScript types)
```

## Key Features

### 1. **Authentication Flow**
- Login page at `/login` (unprotected)
- Credentials saved to localStorage (access_token, refresh_token)
- API interceptors automatically add Bearer token to requests

### 2. **Protected Routes**
- All routes under `(dashboard)` are protected
- Layout checks for authentication on mount
- Redirects to `/login` if not authenticated

### 3. **API Configuration**
- Base URL from `NEXT_PUBLIC_API_URL` environment variable
- Automatic token injection in all requests
- Token refresh on 401 response
- Automatic redirect to login on token expiration

### 4. **Services**
- `services/auth.ts`: Authentication functions (login, logout, token management)
- `services/api.ts`: Axios instance with interceptors and API endpoints

### 5. **Hooks**
- `useAuth()`: Manages user state and authentication operations

### 6. **Components**
- `Sidebar`: Navigation menu with links to dashboard, users, roles, permissions
- `Header`: User info display and logout button
- `Layout`: Layout wrapper (legacy, can be removed)

## Setup Instructions

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Copy `.env.local.example` to `.env.local` and update if needed:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server
```bash
npm run dev
```

Visit `http://localhost:3000` - you'll be redirected to login or dashboard based on auth status.

### 4. Default Credentials
```
Email: admin@test.com
Password: 123456
```

## Authentication Flow Diagram

```
1. User visits http://localhost:3000
   └─> Redirects to /login or /dashboard based on auth status

2. At /login:
   ├─> If already authenticated → redirect to /dashboard
   └─> If not → show login form

3. User submits credentials:
   ├─> Call POST /auth/login with email & password
   ├─> Save tokens (access_token, refresh_token) to localStorage
   └─> Redirect to /dashboard

4. At /dashboard and all nested routes:
   ├─> Check localStorage for access_token
   ├─> If missing → redirect to /login
   └─> If present → render Sidebar + Header + page content

5. Token Refresh:
   ├─> If API returns 401 → use refresh_token
   ├─> Get new access_token from POST /auth/refresh
   ├─> Retry original request
   └─> If refresh fails → redirect to /login

6. Logout:
   ├─> Clear tokens from localStorage
   └─> Redirect to /login
```

## API Endpoints Used

Currently, the following endpoints are expected from the backend:

- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token
- `GET /auth/users` - List users (prepared, not yet implemented)
- `POST /auth/users` - Create user (prepared, not yet implemented)
- `PUT /auth/users/{id}` - Update user (prepared, not yet implemented)
- `DELETE /auth/users/{id}` - Delete user (prepared, not yet implemented)
- `GET /auth/roles` - List roles (prepared, not yet implemented)
- `POST /auth/roles` - Create role (prepared, not yet implemented)
- `GET /auth/permissions` - List permissions (prepared, not yet implemented)

## Next Steps

1. ✅ Basic authentication and route protection
2. ✅ Layout with sidebar and header
3. ⏳ Dashboard with statistics
4. ⏳ Users CRUD page
5. ⏳ Roles CRUD page
6. ⏳ Permissions management page
7. ⏳ Form validation and better error handling
8. ⏳ User profile page
9. ⏳ Settings page

## Notes

- Old route directories (dashboard/, login/, users/, roles/, permissions/ in src/app root) can be removed - they are replaced by the new route group structure
- All components are client-side ("use client") since they need state and interactivity
- Token expiration and refresh are handled automatically via axios interceptors
- The user object is currently a placeholder - implement `/auth/me` endpoint to fetch real user data
