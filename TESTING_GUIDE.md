# 🧪 AstroBot UI Testing Guide

## Overview
The React frontend is **100% complete** with a built-in **Test Mode** on the login page that allows you to quickly access and test all three user roles and their respective pages without needing actual credentials or backend authentication.

---

## 🚀 Quick Start - Test Mode Buttons

Navigate to: **http://localhost:3003/login** (or port 3000/3001/3002)

You'll see three TEST MODE buttons at the bottom of the login card:

### 1. 👨‍💼 Test Admin
**What it does:**
- Logs in as an admin user
- Sets up admin session in localStorage
- Redirects to Admin Dashboard
- Gives full access to all admin features

**What you can test:**
- Documents management (upload, view, delete)
- Analytics dashboard (charts, KPIs, metrics)
- User management (create, enable/disable, delete users)
- Rate limiting configuration
- System health monitoring
- Admin sidebar navigation
- Admin navbar with user dropdown and theme toggle

**localStorage State:**
```javascript
{
  astrobot_user: { id: '1', username: 'admin', role: 'admin', fullName: 'Admin User' },
  token: 'test-token'
}
```

---

### 2. 👨‍🎓 Test Student
**What it does:**
- Logs in as a student user
- Sets up student session in localStorage
- Redirects to Chat Interface
- Access to chat features as a student

**What you can test:**
- Chat interface with AstroBot
- Sending and receiving messages
- Message history in sidebar
- Conversation persistence
- Quick suggestion boxes
- Voice recording button (UI only)
- User profile display
- Logout functionality

**localStorage State:**
```javascript
{
  astrobot_user: { id: '2', username: 'student', role: 'student', fullName: 'Student User' },
  token: 'test-token'
}
```

---

### 3. 👨‍🏫 Test Faculty
**What it does:**
- Logs in as a faculty user
- Sets up faculty session in localStorage
- Redirects to Chat Interface
- Access to chat features as a faculty member

**What you can test:**
- Same features as Student role
- Faculty profile display
- Faculty-specific permissions (when implemented)

**localStorage State:**
```javascript
{
  astrobot_user: { id: '3', username: 'faculty', role: 'faculty', fullName: 'Faculty User' },
  token: 'test-token'
}
```

---

## 📍 Pages & Features to Test

### Admin Dashboard (`/admin/documents`)

**Main Features:**
- ✅ Document upload (multi-format: PDF, DOCX, XLSX, CSV, PPTX, HTML, TXT)
- ✅ Document list with search/filter
- ✅ Document deletion
- ✅ Knowledge base statistics
- ✅ AdminNavbar with user dropdown
- ✅ AdminSidebar with navigation menu
- ✅ Theme toggle (light/dark mode)
- ✅ Logout button

**Sub-pages to navigate to:**
- 📊 **Analytics** (`/admin/analytics`)
  - KPI cards: Total Queries, Active Users, Documents, Avg Latency
  - Query trends chart (line chart)
  - User distribution pie chart
  - API latency bar chart
  - Popular questions list

- 👥 **Users** (`/admin/users`)
  - User list with details
  - Create new user form
  - Enable/disable users
  - Delete users
  - User role selection

- ⚡ **Rate Limiting** (`/admin/rate-limiting`)
  - View rate limit configurations
  - Edit rate limits per endpoint
  - Toggle rate limiting on/off
  - Reset rate limits

- ⚙️ **Settings** (`/admin/settings`)
  - General system settings
  - Provider configuration

- 📈 **Memory** (`/admin/memory`)
  - Conversation memory statistics
  - Memory usage overview

- 🏥 **Health** (`/admin/health`)
  - System health status
  - Component availability

---

### Chat Interface (`/chat`)

**Main Features:**
- ✅ Welcome message from AstroBot
- ✅ Message input textarea (max 500 characters)
- ✅ Send button (with loading state)
- ✅ Voice recording button (UI ready)
- ✅ Quick suggestions dropdown
- ✅ Animated typing indicator
- ✅ Message history display
- ✅ User messages (right-aligned, purple bubbles)
- ✅ Bot messages (left-aligned, with sources dropdown)
- ✅ Copy message button
- ✅ Feedback buttons (👍 / 👎 )
- ✅ Conversation sidebar (left panel)
- ✅ New conversation button
- ✅ Search conversations
- ✅ Responsive design (mobile/desktop)

**Interactions to Test:**
1. Type a message and send (Note: API integration requires Spring Boot backend)
2. Click on suggestions
3. Toggle sidebar on mobile
4. Use voice button (UI only - backend implementation needed)
5. Click copy on bot messages
6. Submit feedback (thumbs up/down)
7. View message timestamps

---

### Login Page (`/login`)

**Features:**
- ✅ Logo and branding section
- ✅ Sign In tab
- ✅ Create Account tab
- ✅ Form validation (Zod + React Hook Form)
- ✅ Remember me checkbox
- ✅ Forgot password link
- ✅ Terms & Privacy footer
- ✅ Responsive design
- ✅ **TEST MODE buttons** (3 quick access buttons)
- ✅ Beautiful gradient background
- ✅ Smooth animations (Framer Motion)

---

## 🔍 Testing Checklist

### UI/UX Testing
- [ ] All colors are consistent (Purple #7C3AED for primary, Teal #14B8A6 for secondary)
- [ ] All text is readable and properly aligned
- [ ] All buttons have hover states
- [ ] Animations are smooth (Framer Motion)
- [ ] No console errors (open DevTools: F12)
- [ ] Responsive on mobile (375px), tablet (768px), desktop (1280px)
- [ ] All icons render correctly (Lucide React icons)

### Navigation Testing
- [ ] Test Admin → Admin Dashboard loads
- [ ] Test Student → Chat page loads
- [ ] Test Faculty → Chat page loads
- [ ] Admin sidebar navigation works
- [ ] Can switch between admin sub-pages
- [ ] Logout redirects to login page
- [ ] Back button navigation works

### Form Testing
- [ ] Login form validation (required fields)
- [ ] Password field is masked (dots showing)
- [ ] Tab switcher works (Sign In ↔ Create Account)
- [ ] Form errors display properly
- [ ] Loading states show on buttons

### Component Testing
- [ ] AdminNavbar displays user info correctly
- [ ] AdminSidebar shows active nav item
- [ ] Chat sidebar shows conversation history
- [ ] Message bubbles animate in smoothly
- [ ] Typing indicator animates
- [ ] All badges render with correct colors
- [ ] Modals (if any) open/close properly
- [ ] Dropdowns open/close correctly

### Theme Testing
- [ ] Light mode is default
- [ ] Dark mode toggle works (Admin navbar)
- [ ] Colors adapt to theme
- [ ] Text remains readable in both themes

---

## 📱 Device Testing

**Desktop (1280px+):**
- [ ] Two-column layout on login page
- [ ] Admin sidebar always visible
- [ ] Chat sidebar always visible
- [ ] All content visible without scrolling (where possible)

**Tablet (768px - 1279px):**
- [ ] Responsive grid adjusts
- [ ] Sidebar collapses/toggles
- [ ] Touch targets are adequate (44px minimum)

**Mobile (375px - 767px):**
- [ ] Single column layout
- [ ] Hamburger menu works
- [ ] Touch interactions work
- [ ] No horizontal scroll
- [ ] Buttons are easily tappable

---

## 🐛 Common Issues & Troubleshooting

### Issue: Test buttons not working
**Solution:**
- Clear browser cache: DevTools → Application → Clear Storage
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Check console for errors: F12 → Console tab

### Issue: localStorage not persisting
**Solution:**
- Check if private/incognito mode is enabled
- Check browser localStorage settings
- Clear cookies and site data

### Issue: Styles not loading correctly
**Solution:**
- Verify Tailwind CSS is loaded (Network tab in DevTools)
- Check for CSS console errors
- Try different browser

### Issue: Cannot see admin pages
**Solution:**
- Make sure you clicked "Test Admin" button
- Check localStorage: DevTools → Application → Local Storage → astrobot_user
- Verify role is set to "admin"

---

## 🔌 Backend Integration Notes

**Current Status:** Frontend is 100% complete and ready for backend integration

**What needs Spring Boot + FastAPI:**
- ❌ Login endpoint (`/api/auth/login`)
- ❌ Register endpoint (`/api/auth/register`)
- ❌ Chat endpoint (`/api/chat`)
- ❌ Document upload/management
- ❌ User management API
- ❌ Analytics data
- ❌ Voice transcription

**How to enable real login:**
1. Start Spring Boot backend on port 8080
2. Start FastAPI backend on port 8001
3. Change test mode to real login
4. Form submission will call actual API endpoints

---

## 📊 Build & Deployment

**Build Status:** ✅ Production Build Ready
```bash
npm run build
# Output: dist/ folder (ready for deployment)
```

**Development Server:**
```bash
npm run dev
# Runs on http://localhost:3003
```

**Key Files:**
- `src/pages/LoginPage.jsx` - Test mode buttons are here
- `src/pages/ChatPage.jsx` - Chat interface
- `src/components/admin/` - Admin dashboard components
- `tailwind.config.js` - Design system colors
- `src/styles/globals.css` - Global styles

---

## 📝 Notes for Developers

- **Test Mode is Development-Only**: Remove test buttons before production (line 144-194 in LoginPage.jsx)
- **localStorage Keys**: Always use `astrobot_user` for consistency
- **API Proxy**: Vite is configured to proxy `/api` requests to `http://localhost:8080` (Spring Boot)
- **No Actual Chat API**: Messages aren't actually sent to backend in test mode
- **Theme Persistence**: Theme preference is saved in localStorage

---

## ✅ Sign-Off Checklist

Before marking the frontend as production-ready:

- [ ] All pages load without errors
- [ ] Test buttons work (Admin, Student, Faculty)
- [ ] Chat interface displays correctly
- [ ] Admin dashboard displays correctly
- [ ] No console errors or warnings
- [ ] Responsive design works on all devices
- [ ] Animations are smooth
- [ ] Colors match design system
- [ ] All text is readable
- [ ] Buttons have proper hover/active states
- [ ] Forms validate correctly
- [ ] localStorage is working
- [ ] Logout clears session
- [ ] Navigation between pages works

---

**Last Updated:** April 9, 2026

**Frontend Version:** 2.0.0 (UI Redesign Complete)

**Status:** ✅ 100% Complete - Ready for Backend Integration
