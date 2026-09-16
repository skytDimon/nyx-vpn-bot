import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, Key } from 'lucide-react';
import { XpWindow } from '../components/XpWindow';
import { XpButton } from '../components/XpButton';
import { useTelegram } from '../hooks/useTelegram';
import { useCabinetData } from '../hooks/useCabinetData';

function formatEndDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('ru-RU');
}

function botUrl(botUsername: string, payload: string): string {
  return `tg://resolve?domain=${botUsername}&start=${payload}`;
}

export function Dashboard() {
  const { hapticFeedback } = useTelegram();
  const { data, loading, error } = useCabinetData();
  const [copied, setCopied] = useState(false);

  if (loading) {
    return (
      <XpWindow title="загрузка.exe" icon="⏳">
        <div className="flex items-center justify-center py-8">
          <span className="font-mono text-sm text-black animate-pulse">Загрузка данных...</span>
        </div>
      </XpWindow>
    );
  }

  if (error === 'NoToken') {
    return (
      <XpWindow title="ошибка.exe" icon="⚠️">
        <div className="bg-white border border-[#7E7E7E] p-3">
          <p className="font-mono text-xs text-black leading-relaxed">
            Ссылка недействительна. Откройте кабинет через бота: нажмите <b>Личный кабинет</b> в меню.
          </p>
        </div>
      </XpWindow>
    );
  }

  if (error) {
    const msg =
      error === 'TokenExpired'
        ? 'Срок действия ссылки истёк. Откройте кабинет заново через бота.'
        : error === 'UserNotFound'
          ? 'Пользователь не найден.'
          : 'Не удалось загрузить данные. Попробуйте позже.';
    return (
      <XpWindow title="ошибка.exe" icon="❌">
        <div className="bg-white border border-[#7E7E7E] p-3">
          <p className="font-mono text-xs text-black">{msg}</p>
        </div>
      </XpWindow>
    );
  }

  if (!data) return null;

  const link = data.subscription?.subscription_link ?? null;
  const isDeleted = data.reason === 'deleted_from_panel';
  const statusText = isDeleted
    ? '⛔ Доступ отключён'
    : data.is_active
      ? '✅ Подписка активна'
      : '❌ Подписка неактивна';
  const statusColor = isDeleted ? 'bg-red-500' : data.is_active ? 'bg-[#00FF00] animate-pulse' : 'bg-red-500';
  const endDate = data.subscription?.end_at ?? null;
  const daysLeft = data.subscription?.days_left;

  const handleCopy = async () => {
    if (!link) return;
    hapticFeedback('light');
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = link;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 px-1">
        <span className="text-2xl">👋</span>
        <h1 className="font-mono text-white text-lg font-semibold">Привет, {data.username}!</h1>
      </motion.div>

      <XpWindow title="nyx_panel.exe" icon="🔑">
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${statusColor}`} />
            <span className="font-mono text-sm font-bold text-black">{statusText}</span>
          </div>

          {isDeleted && (
            <div className="bg-red-50 border border-red-300 p-2">
              <p className="font-mono text-[11px] text-red-800 leading-relaxed">
                Профиль удалён из системы. Обратитесь в поддержку, чтобы восстановить доступ.
              </p>
            </div>
          )}

          {data.is_active && endDate && (
            <div className="bg-white border border-[#7E7E7E] p-2">
              <p className="font-mono text-[10px] text-[#7E7E7E]">Срок окончания</p>
              <p className="font-mono text-sm font-bold text-black">
                {formatEndDate(endDate)}
                {typeof daysLeft === 'number' && <span className="font-normal text-[#7E7E7E]"> · {daysLeft} дн. осталось</span>}
              </p>
            </div>
          )}

          {!data.is_active && !isDeleted && (
            <div className="bg-white border border-[#7E7E7E] p-2">
              <p className="font-mono text-xs text-black">
                Подписка неактивна. Продлите её, чтобы получить ссылку для подключения.
              </p>
            </div>
          )}

          {link && (
            <div className="bg-white border border-[#7E7E7E] p-2">
              <p className="font-mono text-[10px] text-[#7E7E7E] mb-1">Ссылка-подписка (нажмите для копирования):</p>
              <div className="bg-[#000020] p-2 break-all cursor-pointer" onClick={handleCopy}>
                <code className="font-mono text-[10px] text-[#00FF00]">{link.slice(0, 80)}...</code>
              </div>
              <XpButton variant="default" fullWidth onClick={handleCopy} className="mt-2">
                {copied ? (
                  <>
                    <Check size={14} className="mr-1" /> Скопировано!
                  </>
                ) : (
                  <>
                    <Copy size={14} className="mr-1" /> Копировать ссылку
                  </>
                )}
              </XpButton>
            </div>
          )}

          <XpButton variant="accent" fullWidth onClick={() => (window.location.href = botUrl(data.bot_username, 'extend'))}>
            <Key size={16} className="mr-2" />
            Продлить подписку
          </XpButton>
        </div>
      </XpWindow>

      <XpWindow title="referral.exe" icon="🎁">
        <div className="bg-white border border-[#7E7E7E] p-2 flex items-center justify-between">
          <div>
            <p className="font-mono text-[10px] text-[#7E7E7E]">Реферальный баланс</p>
            <p className="font-mono text-lg font-bold text-black">{data.referral_balance} ₽</p>
          </div>
          <XpButton
            variant="default"
            onClick={() => {
              hapticFeedback('light');
              window.location.href = botUrl(data.bot_username, `ref_${data.tg_id}`);
            }}
          >
            Пригласить
          </XpButton>
        </div>
      </XpWindow>

      <XpWindow title="warning.txt" icon="⚠️">
        <div className="bg-[#FFF8DC] border border-[#E6C200] p-2">
          <p className="font-mono text-[11px] text-black leading-relaxed">
            ⚠️ Не заходите на Госуслуги, ФНС, сайты банков и другие государственные/финансовые сервисы с включённым
            VPN — это может привести к блокировке аккаунта. Отключите VPN перед такими визитами.
          </p>
        </div>
      </XpWindow>

      <XpWindow title="быстрый старт.txt" icon="📄">
        <div className="bg-white border border-[#7E7E7E] p-2">
          <p className="font-mono text-xs text-black leading-relaxed">
            Для подключения к <span className="font-bold">NyxVPN</span>:
          </p>
          <ol className="font-mono text-xs text-black mt-2 space-y-1">
            <li>1. Установите VPN-клиент (v2rayTun / Streisand / Hiddify)</li>
            <li>2. Скопируйте ссылку-подписку выше</li>
            <li>3. Добавьте её как подписку в клиенте</li>
            <li>4. Выберите ноду и подключитесь</li>
          </ol>
        </div>
      </XpWindow>

      <AnimatePresence />
    </div>
  );
}
