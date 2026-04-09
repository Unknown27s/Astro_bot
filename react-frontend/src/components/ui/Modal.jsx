import { cn } from '../../utils/cn';
import { X } from 'lucide-react';

export default function Modal({
  isOpen = false,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  className,
  ...props
}) {
  if (!isOpen) return null;

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={(e) => e.target === e.currentTarget && onClose && onClose()}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50 animate-fade-in" />

      {/* Modal */}
      <div
        className={cn(
          'relative bg-white rounded-2xl shadow-xl',
          'w-full mx-4 animate-slide-in',
          'max-h-[90vh] overflow-y-auto',
          sizes[size] || sizes.md,
          className
        )}
        {...props}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white">
            <h2 className="text-2xl font-bold text-slate-800">{title}</h2>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-slate-600" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-6">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-slate-200 p-6 flex justify-end gap-3 bg-slate-50">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
