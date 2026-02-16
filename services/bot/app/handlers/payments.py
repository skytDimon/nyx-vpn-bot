from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data.startswith("plan:"))
async def choose_plan(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ Оплата по планам временно недоступна. Используйте оплату с баланса."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:balance:"))
async def pay_balance_plan(callback: CallbackQuery):
    if callback.data in {"pay:balance:fi", "pay:balance:nl"}:
        await callback.answer()
        return
    await callback.message.answer(
        "⚠️ Оплата по планам с баланса пока недоступна. Используйте тариф с оплатой с баланса."
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("pay:stars:") | F.data.startswith("pay:crypto:")
)
async def pay(callback: CallbackQuery):
    await callback.message.answer(
        "⚠️ Оплата Stars/Crypto временно недоступна. Доступна только оплата с баланса."
    )
    await callback.answer()
