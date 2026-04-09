import { cn } from '../../utils/cn';

export default function Avatar({
  src,
  initials,
  size = 'md',
  variant = 'circle',
  className,
  alt = 'Avatar',
  ...props
}) {
  const sizes = {
    xs: 'h-6 w-6 text-xs',
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg',
    xl: 'h-16 w-16 text-2xl',
    '2xl': 'h-20 w-20 text-3xl',
  };

  const shape = {
    circle: 'rounded-full',
    square: 'rounded-md',
    rounded: 'rounded-lg',
  };

  return (
    <div
      className={cn(
        'flex items-center justify-center bg-purple-600 text-white font-semibold',
        sizes[size] || sizes.md,
        shape[variant] || shape.circle,
        'overflow-hidden',
        className
      )}
      {...props}
    >
      {src ? (
        <img src={src} alt={alt} className="h-full w-full object-cover" />
      ) : (
        <span>{initials || '?'}</span>
      )}
    </div>
  );
}
