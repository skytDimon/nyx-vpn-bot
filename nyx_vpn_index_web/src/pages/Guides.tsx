import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { XpWindow } from '../components/XpWindow';
import { XpButton } from '../components/XpButton';
import { useTelegram } from '../hooks/useTelegram';

interface GuidePlatform {
  id: string;
  name: string;
  icon: string;
  steps: Array<{ step: number; title: string; description: string }>;
}

const GUIDES: GuidePlatform[] = [
  {
    id: 'android',
    name: 'Android — v2rayTun',
    icon: '📱',
    steps: [
      { step: 1, title: 'Установите v2rayTun', description: 'Скачайте приложение из Google Play или GitHub.' },
      { step: 2, title: 'Скопируйте ссылку', description: 'На главной странице скопируйте ссылку-подписку.' },
      { step: 3, title: 'Добавьте подписку', description: 'В приложении: Добавить → Из подписки → вставьте ссылку.' },
      { step: 4, title: 'Подключитесь', description: 'Нажмите кнопку подключения и выберите ноду.' },
    ],
  },
  {
    id: 'ios',
    name: 'iOS — Streisand',
    icon: '🍎',
    steps: [
      { step: 1, title: 'Скачайте Streisand', description: 'Установите Streisand из App Store (бесплатно).' },
      { step: 2, title: 'Скопируйте ссылку', description: 'Скопируйте ссылку-подписку на главной.' },
      { step: 3, title: 'Добавьте сервер', description: 'В Streisand: + → Импорт из буфера — ссылка добавится автоматически.' },
      { step: 4, title: 'Подключитесь', description: 'Включите переключатель VPN в приложении.' },
    ],
  },
  {
    id: 'desktop',
    name: 'Windows / macOS — Hiddify',
    icon: '💻',
    steps: [
      { step: 1, title: 'Скачайте Hiddify', description: 'Загрузите Hiddify с официального сайта или GitHub.' },
      { step: 2, title: 'Скопируйте ссылку', description: 'Скопируйте ссылку-подписку на главной странице.' },
      { step: 3, title: 'Добавьте профиль', description: 'В Hiddify: Новая подписка → вставьте ссылку.' },
      { step: 4, title: 'Подключитесь', description: 'Выберите ноду и нажмите Старт.' },
    ],
  },
];

export function Guides() {
  const { hapticFeedback } = useTelegram();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    hapticFeedback('light');
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="flex flex-col gap-3">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 px-1">
        <span className="text-2xl">📖</span>
        <h1 className="font-mono text-white text-lg font-semibold">Инструкции</h1>
      </motion.div>

      <XpWindow title="readme.txt" icon="📄">
        <div className="bg-white border border-[#7E7E7E] p-2">
          <p className="font-mono text-xs text-black leading-relaxed">
            Для подключения к <span className="font-bold">NyxVPN</span> вам нужно:
          </p>
          <ol className="font-mono text-xs text-black mt-2 space-y-1">
            <li>1. Установить VPN-клиент на ваше устройство</li>
            <li>2. Получить ссылку-подписку на главной странице</li>
            <li>3. Импортировать ссылку в клиент</li>
            <li>4. Подключиться</li>
          </ol>
          <div className="mt-2 pt-2 border-t border-[#C3C3C3]">
            <p className="font-mono text-[10px] text-[#7E7E7E]">Протокол: VLESS + Reality · Обход блокировок</p>
          </div>
        </div>
      </XpWindow>

      <XpWindow title="помощь.exe" icon="❓">
        <div className="flex flex-col gap-1">
          {GUIDES.map((platform, index) => (
            <motion.div
              key={platform.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <XpButton
                fullWidth
                variant={expandedId === platform.id ? 'pressed' : 'default'}
                onClick={() => toggleExpand(platform.id)}
                className="justify-start text-left"
              >
                <span className="text-base mr-2">{platform.icon}</span>
                <span className="flex-1">{platform.name}</span>
                {expandedId === platform.id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </XpButton>

              <AnimatePresence>
                {expandedId === platform.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="bg-white border border-[#7E7E7E] border-t-0 p-2">
                      <div className="flex flex-col gap-2">
                        {platform.steps.map((step) => (
                          <div key={step.step} className="flex gap-2 items-start">
                            <div className="w-5 h-5 shrink-0 bg-[#02007F] flex items-center justify-center">
                              <span className="font-mono text-[10px] text-white font-bold">{step.step}</span>
                            </div>
                            <div className="min-w-0">
                              <p className="font-mono text-xs font-bold text-black">{step.title}</p>
                              <p className="font-mono text-[10px] text-[#7E7E7E] mt-0.5">{step.description}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </XpWindow>

      <XpWindow title="white_list.txt" icon="🌐">
        <div className="bg-white border border-[#7E7E7E] p-2">
          <p className="font-mono text-xs font-bold text-black">Белый список</p>
          <p className="font-mono text-[11px] text-black mt-1 leading-relaxed">
            Для доменов gosuslugi.ru, nalog.ru, сайтов банков добавьте их в обход (Bypass / Исключения) в настройках
            клиента — эти сайты будут идти напрямую.
          </p>
        </div>
      </XpWindow>
    </div>
  );
}
