import { cn } from '../../utils/cn';
import { AlertCircle, CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

export default function Alert({
  variant = 'info',
  title,
  message,
  onClose,
  className,
  ...props
}) {
  const variants = {
    error: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-800',
      icon: AlertCircle,
      color: 'text-red-600',
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      icon: CheckCircle,
      color: 'text-green-600',
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      text: 'text-yellow-800',
      icon: AlertTriangle,
      color: 'text-yellow-600',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      icon: Info,
      color: 'text-blue-600',
    },
  };

  const config = variants[variant] || variants.info;
  const IconComponent = config.icon;

  return (
    <div
      className={cn(
        'flex gap-3 rounded-lg border-2 p-4',
        config.bg,
        config.border,
        config.text,
        className
      )}
      {...props}
    >
      <IconComponent className={cn('h-5 w-5 flex-shrink-0 mt-0.5', config.color)} />
      <div className="flex-1">
        {title && <div className="font-semibold">{title}</div>}
        {message && <div className="text-sm">{message}</div>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-0 hover:opacity-70 transition-opacity flex-shrink-0"
        >
          <X className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}
