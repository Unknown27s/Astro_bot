import { cn } from '../../utils/cn';

export default function Card({
  children,
  className,
  padding = 'md',
  shadow = 'md',
  hover = false,
  ...props
}) {
  const paddingClass = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
  }[padding] || 'p-4';

  const shadowClass = {
    none: 'shadow-none',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  }[shadow] || 'shadow-md';

  return (
    <div
      className={cn(
        'bg-white rounded-xl border border-slate-200',
        paddingClass,
        shadowClass,
        hover && 'hover:shadow-lg hover:border-purple-600 transition-all duration-200',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
