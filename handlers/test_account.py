from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Product, Order, OrderStatus, PaymentMethod
from keyboards.inline import back_to_menu_kb
from locales.fa import TEXTS
from config import get_admin_ids, get_free_test_days

router = Router()


@router.callback_query(F.data == "test_account")
async def cb_test_account(callback: CallbackQuery):
    free_days = await get_free_test_days()

    async with async_session() as session:
        user_result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ خطای سیستم.", show_alert=True)
            return

        if user.used_test:
            await callback.message.edit_text(
                TEXTS["test_used"],
                reply_markup=back_to_menu_kb(),
            )
            await callback.answer()
            return

        # Find test product
        prod_result = await session.execute(
            select(Product).where(Product.is_test == True, Product.is_active == True)
        )
        test_product = prod_result.scalars().first()

        if not test_product:
            await callback.message.edit_text(
                TEXTS["test_unavailable"],
                reply_markup=back_to_menu_kb(),
            )
            await callback.answer()
            return

        # Create test order — duration from test product if set, else from free_test_days setting
        duration = test_product.duration_days if test_product.duration_days > 0 else free_days
        order = Order(
            user_id=callback.from_user.id,
            product_id=test_product.id,
            plan_type="test",
            data_gb=test_product.data_gb,
            duration_days=duration,
            final_price=0,
            status=OrderStatus.pending,
            payment_method=PaymentMethod.wallet,
        )
        session.add(order)
        user.used_test = True
        await session.commit()
        order_id = order.id

    await callback.message.edit_text(
        TEXTS["test_success"],
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()

    # Notify all admins
    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        try:
            await callback.bot.send_message(
                admin_id,
                f"🧪 اکانت تست درخواست شده\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 کاربر: {callback.from_user.first_name} (@{callback.from_user.username or 'ندارد'})\n"
                f"🆔 آیدی: {callback.from_user.id}\n"
                f"📋 سفارش: #{order_id} | {duration} روزه\n\n"
                f"💡 لینک کانفیگ را از بخش «سفارشات در انتظار» ارسال کنید.",
            )
        except Exception:
            pass
