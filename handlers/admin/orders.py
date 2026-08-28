from datetime import timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select, func as sql_func

from database.engine import async_session
from database.models import User, Product, Order, OrderStatus, PaymentMethod
from keyboards.inline import (
    admin_menu_kb, back_to_admin_kb,
    admin_orders_list_kb, admin_order_detail_kb,
)
from locales.fa import TEXTS
from states.states import AdminConfigSend
from config import is_admin

router = Router()


def _pay_method_str(order) -> str:
    val = order.payment_method.value if hasattr(order.payment_method, 'value') else str(order.payment_method)
    return {"wallet": "💳 کیف پول", "card_transfer": "⇜ کارت به کارت", "gateway": "🌐 درگاه پرداخت"}.get(val, "نامشخص")


def _status_str(order) -> str:
    val = order.status.value if hasattr(order.status, 'value') else str(order.status)
    return {"pending": "⏳ در انتظار", "approved": "✅ تایید شده", "rejected": "❌ رد شده", "expired": "⏰ منقضی"}.get(val, "نامشخص")


@router.callback_query(F.data == "admin_pending_orders")
async def cb_admin_pending_orders(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Order).where(Order.status == OrderStatus.pending).order_by(Order.created_at.asc())
        )
        orders = result.scalars().all()

        if not orders:
            await callback.message.edit_text(
                "✅ سفارش در انتظاری وجود ندارد.",
                reply_markup=admin_menu_kb(),
            )
            await callback.answer()
            return

        # Eagerly load product and user for each order
        items = []
        for order in orders:
            prod_result = await session.execute(select(Product).where(Product.id == order.product_id))
            product = prod_result.scalar_one_or_none()
            user_result = await session.execute(select(User).where(User.telegram_id == order.user_id))
            user = user_result.scalar_one_or_none()
            items.append({"order": order, "product": product, "user": user})

    lines = ["📋 سفارشات در انتظار تایید:\n━━━━━━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(items, 1):
        o = item["order"]
        p = item["product"]
        u = item["user"]
        user_name = (u.first_name or "نامشخص") if u else "نامشخص"
        prod_name = p.name if p else "نامشخص"
        price = f"{p.price:,.0f}" if p else "0"
        pay_method = _pay_method_str(o)
        lines.append(f"\n{i}. 🆔 #{o.id} | 👤 {user_name}\n   📦 {prod_name} | {price}t | {pay_method}")

    kb = admin_orders_list_kb(items)
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_order_"))
async def cb_view_order(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()

        if not order:
            await callback.answer("❌ سفارش یافت نشد.", show_alert=True)
            return

        prod_result = await session.execute(select(Product).where(Product.id == order.product_id))
        product = prod_result.scalar_one_or_none()

        user_result = await session.execute(select(User).where(User.telegram_id == order.user_id))
        user = user_result.scalar_one_or_none()

    user_name = (user.first_name or "نامشخص") if user else "نامشخص"
    user_uname = f"@{user.username}" if user and user.username else "ندارد"
    prod_name = product.name if product else "نامشخص"
    prod_desc = (product.description or "ندارد") if product else "ندارد"
    prod_price = f"{product.price:,.0f}" if product else "0"
    prod_dur = product.duration_days if product else 0
    pay_method = _pay_method_str(order)
    status_str = _status_str(order)

    text = (
        f"📋 جزئیات سفارش #{order.id}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: {user_name} ({user_uname})\n"
        f"🆔 آیدی: {order.user_id}\n\n"
        f"📦 پلن: {prod_name}\n"
        f"📝 توضیحات: {prod_desc}\n"
        f"💰 قیمت: {prod_price} تومان\n"
        f"⏰ مدت: {prod_dur} روز\n\n"
        f"💳 روش پرداخت: {pay_method}\n"
        f"📊 وضعیت: {status_str}\n"
        f"📅 تاریخ ثبت: {order.created_at.strftime('%Y/%m/%d %H:%M') if order.created_at else 'نامشخص'}"
    )

    await callback.message.edit_text(text, reply_markup=admin_order_detail_kb(order.id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_"))
async def cb_approve_order(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        f"✅ ارسال کانفیگ برای سفارش #{order_id}\n\n"
        f"📝 لینک کانفیگ را ارسال کنید:",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminConfigSend.waiting_config)
    await state.update_data(order_id=order_id)
    await callback.answer()


@router.message(AdminConfigSend.waiting_config)
async def process_send_config(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data["order_id"]

    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()

        if not order:
            await message.answer("❌ سفارش یافت نشد.", reply_markup=admin_menu_kb())
            await state.clear()
            return

        prod_result = await session.execute(select(Product).where(Product.id == order.product_id))
        product = prod_result.scalar_one_or_none()

        order.config_link = message.text.strip()
        order.status = OrderStatus.approved
        order.approved_at = sql_func.now()
        if product:
            order.expires_at = sql_func.now() + timedelta(days=product.duration_days)
        await session.commit()

    await message.answer(
        f"✅ کانفیگ برای سفارش #{order_id} ارسال شد.",
        reply_markup=admin_menu_kb(),
    )
    await state.clear()

    # Notify user
    try:
        await message.bot.send_message(
            order.user_id,
            f"✅ سفارش شما #{order_id} تایید شد!\n\n"
            f"🔑 کانفیگ:\n{order.config_link}\n\n"
            f"📖 برای آموزش استفاده از بخش آموزش استفاده کنید.",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_reject_"))
async def cb_reject_order(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])

    async with async_session() as session:
        order_result = await session.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()

        if not order:
            await callback.answer("❌ سفارش یافت نشد.", show_alert=True)
            return

        order.status = OrderStatus.rejected
        await session.commit()

        # Refund if paid by wallet
        pay_val = order.payment_method.value if hasattr(order.payment_method, 'value') else str(order.payment_method)
        if pay_val == "wallet":
            user_result = await session.execute(select(User).where(User.telegram_id == order.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                user.wallet_balance += order.final_price
                await session.commit()

    await callback.answer("❌ سفارش رد شد.", show_alert=True)

    # Notify user
    try:
        await callback.bot.send_message(
            order.user_id,
            f"❌ سفارش #{order_id} رد شد.\n"
            f"در صورت پرداخت از کیف پول، وجه به موجودی شما بازگشت داده شد.\n"
            f"📞 برای اطلاعات بیشتر با پشتیبانی تماس بگیرید.",
        )
    except Exception:
        pass

    # Go back to pending orders list
    await cb_admin_pending_orders(callback)
