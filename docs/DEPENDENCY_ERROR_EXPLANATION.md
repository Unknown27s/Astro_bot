# Dependency Error Explanation & Resolution

## ❌ Problem: CSS Class Not Found at Build Time

**Error:** `The 'text-primary' class does not exist`

### Root Cause
When using `@apply` in CSS files (not components), Tailwind CSS tries to resolve the class **during the build process**.

Custom color extensions defined in `tailwind.config.js` work fine in **JSX components** (like `className="text-primary"`), but NOT in CSS files with `@apply` statements because:

1. CSS files are processed by PostCSS → Tailwind
2. At that moment, Tailwind hasn't extended the color utilities yet
3. It only sees standard Tailwind classes like `text-slate-500`

### ✅ Solution Implemented

**Changed FROM:**
```css
/* ❌ This fails - custom class in CSS @apply */
a {
  @apply text-primary font-medium hover:text-primary-dark transition-colors duration-200;
}
```

**Changed TO:**
```css
/* ✅ This works - CSS variables + standard CSS */
a {
  color: var(--color-primary);
  font-weight: 500;
  transition: color 0.2s ease-in-out;
}

a:hover {
  color: var(--color-primary-dark);
}
```

## 🔑 Key Takeaways

### Where to Use What:

| Context | What to Use | Example |
|---------|------------|---------|
| JSX Components | Tailwind classes | `className="text-primary text-lg"` |
| Component Attributes | Tailwind classes | `className="bg-bg-primary"` |
| CSS Files (@apply) | Standard Tailwind classes | `@apply text-slate-800 font-bold` |
| CSS Files (styling) | CSS Variables | `color: var(--color-primary)` |

### This Project's Approach:
1. **For components:** Use `className="text-primary"` (works because Tailwind extends colors in config)
2. **For globals.css:** Use CSS variables `var(--color-primary)` (works universally)
3. **For @apply in CSS:** Only use standard Tailwind classes `@apply text-slate-500`

## 📚 Why CSS Variables?

CSS variables (custom properties) are:
- ✅ Available at all layers (CSS + JS)
- ✅ Don't require build-time resolution
- ✅ Can be dynamically changed (theme switching)
- ✅ Work with dark mode media queries
- ✅ Backwards compatible

```css
:root {
  --color-primary: #7C3AED;
  --color-text-primary: #1E293B;
}

/* Works everywhere */
a { color: var(--color-primary); }
.card { background: var(--color-bg-primary); }
```

## 🎯 This Won't Happen Again

The project now follows this pattern:
1. **tailwind.config.js** - Define extended colors + custom utilities
2. **globals.css** - Use CSS variables + standard Tailwind @apply
3. **Components (JSX)** - Use extended Tailwind classes directly
4. **theme.css** - Define CSS variable fallbacks

## 🚀 Moving Forward

**Safe to use in components:**
```jsx
<div className="text-primary bg-bg-primary border-border">
  Content
</div>
```

**Safe to use in CSS:**
```css
body {
  @apply bg-slate-50 font-sans;
  color: var(--color-text-primary);
}
```

---

**Status:** ✅ Resolved | **Build:** Should now compile without CSS errors
