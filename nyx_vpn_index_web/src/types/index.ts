export interface Subscription {
  start_at: string | null;
  end_at: string | null;
  days_left: number | null;
  subscription_link: string | null;
  instructions: string | null;
}

export interface CabinetData {
  username: string;
  tg_id: number;
  is_active: boolean;
  reason: string | null;
  subscription: Subscription | null;
  referral_balance: number;
  bot_username: string;
  sbp_phone: string | null;
  payment_amount: number;
  payment_days: number;
}
