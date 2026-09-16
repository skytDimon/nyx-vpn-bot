import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface XpWindowProps {
  title: string;
  icon?: string;
  children: ReactNode;
  className?: string;
}

export function XpWindow({ title, icon, children, className = '' }: XpWindowProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`w-full bg-[#C3C3C3] shadow-[inset_-2px_-2px_0px_0px_#262626,inset_2px_2px_0px_0px_#F0F0F0,inset_-4px_-4px_0px_0px_#7E7E7E] ${className}`}
    >
      {/* Title Bar */}
      <div className="bg-[#02007F] flex items-center w-[calc(100%-8px)] mx-1 mt-1 px-2 py-1.5 gap-2">
        {icon && <span className="text-lg leading-none">{icon}</span>}
        <span className="font-mono text-white text-sm font-medium truncate">{title}</span>
        <div className="ml-auto flex gap-0.5 shrink-0">
          <div className="w-4 h-3.5 bg-[#C3C3C3] shadow-[inset_-1px_-1px_0px_0px_#262626,inset_1px_1px_0px_0px_#F0F0F0] flex items-center justify-center">
            <span className="text-[8px] font-mono leading-none font-bold text-black">_</span>
          </div>
          <div className="w-4 h-3.5 bg-[#C3C3C3] shadow-[inset_-1px_-1px_0px_0px_#262626,inset_1px_1px_0px_0px_#F0F0F0] flex items-center justify-center">
            <span className="text-[8px] font-mono leading-none font-bold text-black">□</span>
          </div>
          <div className="w-4 h-3.5 bg-[#C3C3C3] shadow-[inset_-1px_-1px_0px_0px_#262626,inset_1px_1px_0px_0px_#F0F0F0] flex items-center justify-center">
            <span className="text-[8px] font-mono leading-none font-bold text-black">✕</span>
          </div>
        </div>
      </div>
      {/* Window Body */}
      <div className="p-3">
        {children}
      </div>
    </motion.div>
  );
}
