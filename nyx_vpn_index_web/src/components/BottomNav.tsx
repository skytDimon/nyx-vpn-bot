import { NavLink } from 'react-router-dom';
import { Home, CreditCard, HelpCircle } from 'lucide-react';
import { useTelegram } from '../hooks/useTelegram';

const navItems = [
  { to: '/', icon: Home, label: 'Главная' },
  { to: '/pricing', icon: CreditCard, label: 'Оплата' },
  { to: '/guides', icon: HelpCircle, label: 'Помощь' },
];

export function BottomNav() {
  const { hapticFeedback } = useTelegram();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-[#C3C3C3] shadow-[inset_0_2px_0px_0px_#F0F0F0,inset_0_-2px_0px_0px_#262626] border-t-2 border-[#F0F0F0]">
      <div className="flex items-stretch h-14">
        <div className="flex items-center pl-1 pr-1 border-r border-[#7E7E7E]">
          <div className="flex items-center gap-1 px-2 py-1 bg-[#C3C3C3] shadow-[inset_-1px_-1px_0px_0px_#262626,inset_1px_1px_0px_0px_#F0F0F0,inset_-2px_-2px_0px_0px_#7E7E7E] select-none">
            <span className="text-xs">⚡</span>
            <span className="font-mono text-[10px] font-bold text-black">NyxVPN</span>
          </div>
        </div>

        <div className="flex flex-1 items-stretch gap-0.5 px-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => hapticFeedback('light')}
              className={({ isActive }) =>
                `flex-1 flex items-center justify-center gap-1 px-1 py-1 font-mono text-[10px] text-black transition-all select-none ${
                  isActive
                    ? 'bg-[#C3C3C3] shadow-[inset_2px_2px_0px_0px_#262626,inset_-2px_-2px_0px_0px_#F0F0F0,inset_4px_4px_0px_0px_#7E7E7E]'
                    : 'bg-[#C3C3C3] shadow-[inset_-2px_-2px_0px_0px_#262626,inset_2px_2px_0px_0px_#F0F0F0,inset_-4px_-4px_0px_0px_#7E7E7E] hover:bg-[#DBDBDB] active:shadow-[inset_2px_2px_0px_0px_#262626,inset_-2px_-2px_0px_0px_#F0F0F0,inset_4px_4px_0px_0px_#7E7E7E]'
                }`
              }
            >
              <Icon size={14} strokeWidth={2.5} />
              <span className="hidden min-[340px]:inline">{label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
