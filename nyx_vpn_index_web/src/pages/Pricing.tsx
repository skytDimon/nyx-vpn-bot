import { motion } from 'framer-motion';
import { XpWindow } from '../components/XpWindow';
import { XpButton } from '../components/XpButton';
import { useTelegram } from '../hooks/useTelegram';
import { useCabinetData } from '../hooks/useCabinetData';

function botUrl(botUsername: string, payload: string): string {
  return `tg://resolve?domain=${botUsername}&start=${payload}`;
}

export function Pricing() {
  const { hapticFeedback } = useTelegram();
  const { data, loading, error } = useCabinetData();

  if (loading) {
    return (
      <XpWindow title="оплата.exe" icon="💰">
        <div className="flex items-center justify-center py-8">
          <span className="font-mono text-sm text-black animate-pulse">Загрузка...</span>
        </div>
      </XpWindow>
    );
  }

  if (error === 'NoToken') {
    return (
      <XpWindow title="ошибка.exe" icon="⚠️">
        <div className="bg-white border border-[#7E7E7E] p-3">
          <p className="font-mono text-xs text-black">Откройте кабинет через бота.</p>
        </div>
      </XpWindow>
    );
  }

  if (error || !data) {
    return (
      <XpWindow title="ошибка.exe" icon="❌">
        <div className="bg-white border border-[#7E7E7E] p-3">
          <p className="font-mono text-xs text-black">Не удалось загрузить данные.</p>
        </div>
      </XpWindow>
    );
  }

  const amount = data.payment_amount;
  const days = data.payment_days;
  const phone = data.sbp_phone ?? '—';

  return (
    <div className="flex flex-col gap-3">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 px-1">
        <span className="text-2xl">💰</span>
        <h1 className="font-mono text-white text-lg font-semibold">Оплата</h1>
      </motion.div>

      <XpWindow title="тариф.exe" icon="📦">
        <div className="flex flex-col gap-2">
          <div className="bg-white border border-[#7E7E7E] p-3">
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-3xl font-bold text-black">{amount}</span>
              <span className="font-mono text-lg text-[#7E7E7E]">₽</span>
            </div>
            <p className="font-mono text-xs text-[#7E7E7E] mt-0.5">за {days} дн. · безлимит трафика · Германия + Нидерланды</p>
            <p className="font-mono text-[10px] text-[#7E7E7E] mt-1">До 5 устройств · Поддержка 24/7</p>
          </div>
        </div>
      </XpWindow>

      <XpWindow title="инструкция.sbp" icon="💳">
        <div className="bg-white border border-[#7E7E7E] p-3">
          <p className="font-mono text-xs font-bold text-black mb-2">Оплата через СБП:</p>
          <ol className="font-mono text-xs text-black space-y-2">
            <li>
              1. Переведите <span className="font-bold">{amount} ₽</span> по СБП на номер
              <span className="font-bold"> {phone}</span>
            </li>
            <li>2. Сфотографируйте или сделайте скриншот чека</li>
            <li>3. Пришлите фото чека в бота — подписка продлится после проверки</li>
          </ol>
        </div>
        <div className="mt-2">
          <XpButton
            variant="accent"
            fullWidth
            onClick={() => {
              hapticFeedback('heavy');
              window.location.href = botUrl(data.bot_username, 'extend');
            }}
          >
            Перейти к оплате в боте
          </XpButton>
        </div>
      </XpWindow>
    </div>
  );
}
