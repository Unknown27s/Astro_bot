/**
 * Utility to merge classnames
 * Handles conditional classes, arrays, objects
 * Similar to clsx library but lightweight
 */
export function cn(...classes) {
  return classes
    .flat()
    .filter(Boolean)
    .join(' ')
    .trim();
}

/**
 * Get button variant classes
 */
export const buttonVariants = {
  primary: 'bg-primary hover:bg-primary-700 text-white shadow-md hover:shadow-lg',
  secondary: 'bg-slate-200 hover:bg-slate-300 text-text-primary',
  ghost: 'bg-transparent hover:bg-slate-100 text-text-primary',
  danger: 'bg-error hover:bg-red-700 text-white',
  success: 'bg-success hover:bg-green-700 text-white',
  outline: 'border-2 border-primary text-primary hover:bg-primary hover:text-white',
};

/**
 * Get size classes for button
 */
export const buttonSizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
  xl: 'px-8 py-4 text-xl',
};

/**
 * Format date to readable string
 */
export function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format time
 */
export function formatTime(date) {
  if (!date) return '';
  const d = new Date(date);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Truncate text
 */
export function truncate(text, length = 100) {
  if (!text) return '';
  if (text.length <= length) return text;
  return text.slice(0, length) + '...';
}
