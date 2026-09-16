import type { ReactNode, ButtonHTMLAttributes } from 'react';

interface XpButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'default' | 'accent' | 'pressed';
  fullWidth?: boolean;
}

export function XpButton({
  children,
  variant = 'default',
  fullWidth = false,
  className = '',
  ...props
}: XpButtonProps) {
  const baseClasses =
    'relative inline-flex items-center justify-center whitespace-nowrap transition-all font-mono font-medium text-sm px-4 py-3 h-[46px] select-none active:pt-[13px] active:pb-[11px] active:pl-[17px] active:pr-[15px]';

  const variantClasses = {
    default:
      'text-black bg-[#C3C3C3] hover:bg-[#DBDBDB] shadow-[inset_-2px_-2px_0px_0px_#262626,inset_2px_2px_0px_0px_#F0F0F0,inset_-4px_-4px_0px_0px_#7E7E7E] active:shadow-[inset_2px_2px_0px_0px_#262626,inset_-2px_-2px_0px_0px_#F0F0F0,inset_4px_4px_0px_0px_#7E7E7E]',
    accent:
      'text-black bg-[#00FF00] hover:bg-[#7FFF7F] shadow-[inset_-2px_-2px_0px_0px_#262626,inset_2px_2px_0px_0px_#F0F0F0,inset_-4px_-4px_0px_0px_#7E7E7E] active:shadow-[inset_2px_2px_0px_0px_#262626,inset_-2px_-2px_0px_0px_#F0F0F0,inset_4px_4px_0px_0px_#7E7E7E] before:content-[""] before:absolute before:inset-[6px] before:border before:border-dashed before:border-black before:pointer-events-none active:before:top-[8px] active:before:left-[8px] active:before:right-[4px] active:before:bottom-[4px]',
    pressed:
      'text-black bg-[#C3C3C3] shadow-[inset_2px_2px_0px_0px_#262626,inset_-2px_-2px_0px_0px_#F0F0F0,inset_4px_4px_0px_0px_#7E7E7E] pt-[13px] pb-[11px] pl-[17px] pr-[15px]',
  };

  const widthClass = fullWidth ? 'w-full' : '';

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${widthClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
