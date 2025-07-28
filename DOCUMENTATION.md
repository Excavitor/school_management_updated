# School Management System - Project Documentation

## Overview
Django-based school management system with granular role-based access control, notice management, and admission applications. Non-authenticate users can view notice, apply for admission, and can register to get access to dashboard pannel. New user will get Null role and can view only dashboard but authenticate user with proper role can do task according to their role. Only Superadmin can assign role to a user and can CRUD in role. Default permissions for a role are set in `/accounts/management/commands/setup_default_roles.py`

Default system roles are `Superadmin, Admin, Teacher, Guest/Null`

To run the project see `README.md` file.

## Apps & Models

### 1. Accounts App
**Models:**
- `CustomUser` - Extended user with phone, role (foreign key)
- `Role` - JSON-based permissions system (granular control)

### 2. Public App  
**Models:**
- `Notice` - School announcements (title, content, published status)
- `AdmissionApplication` - Student admission forms

**Tasks**
- This app is for non-authenticate users
- Can view published notices
- Can submit Admission application
- User registration for dashboard access

### 3. Dashboard App
**Models:** None (uses models from Public and Accounts)

**Tasks**
- This app is for authenticated users (login required after registration)
- New user get null role and can view dashboard only
- User can do task according to their role given by superadmin
- Superadmin can only do CRUD in role

## URL Structure & Flow

### Public URLs (/)
- `/` → HomeView → displays recent notices
- `/notices/` → NoticeListView → paginated notice list with search
- `/admission/` → AdmissionApplicationCreateView → admission form
- `/register/` → UserRegistrationView → user registration
- `/login/` → LoginView → session-based login
- `/logout/` → LogoutView → logout

### Dashboard URLs (/dashboard/)
- `/dashboard/` → DashboardHomeView → stats dashboard
- `/dashboard/notices/` → NoticeListView → notice management
- `/dashboard/applications/` → ApplicationListView → application management  
- `/dashboard/users/` → UserListView → user management (SuperAdmin)
- `/dashboard/roles/` → RoleListView → role management (SuperAdmin)

### API URLs
- `/api/auth/` → Djoser authentication endpoints
- `/api/accounts/` → User profile, registration, logout
- `/api/public/` → Public notice list, admission API
- `/dashboard/api/` → Dashboard CRUD operations

## Permissions System

### Roles
- **SuperAdmin**: All permissions
- **Admin**: Notice/application management, no user/role management  
- **Teacher**: Read-only access to notices/applications
- **Guest/Null**: Dashboard view only

## Key Features
- **Pages**: 15+ template pages (home, notices, admission, dashboard, management)
- **APIs**: 10+ REST endpoints for CRUD operations
- **Authentication**: Session + JWT dual support
- **Security**: reCAPTCHA, rate limiting, input validation
- **Export**: CSV export for applications
- **Search**: Full-text search on notices and applications
- **Pagination**: All list views paginated

## Database Tables
- CustomUser, Role (accounts app)
- Notice, AdmissionApplication (public app)

## Management Commands
- `setup_default_roles` - Creates default role structure
- `assign_superadmin_role` - Assigns SuperAdmin role to superusers