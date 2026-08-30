from datetime import datetime
from decimal import Decimal

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Product, Order, OrderStatus, PaymentMethod, DiscountCode
from keyboards.inline import (
    back_to_menu_kb, products_list_kb, duration_kb,
    custom_plan_gb_kb, custom_plan_duration_kb,
    payment_choice_kb, confirm_buy_kb, discount_skip_kb,
)
from locales.fa import TEXTS
from states.states import BuyService
from config import get_card_info, get_admin_ids
from utils.pricing import calc_custom_price, calc_preset_price

router = Router()


# ─── Step 1: show plans ────────────────────────────────────────
@router.callback_query(F.data == "buy")
async def cb_buy(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True, Product.is_test == False)
        )
        products = result.scalars().all()

    if not products:
        await callback.message.edit_text(TEXTS["buy_empty"], reply_markup=back_to_menu_kb())
        await callback.answer()
        return

    await callback.message.edit_text(
        "🛒 خرید سرویس جدید\n━━━━━━━━━━━━━━━━━━━━━\nپلن مورد نظر را انتخاب کنید:",
        reply_markup=products_list_kb(products),
    )
    await callback.answer()


# ─── Step 2a: preset plan selected → duration ──────────────────
@router.callback_query(F.data.startswith("product_"))
async def cb_select_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        product = (await session.execute(
            select(Product).where(Product.id == product_id)
        )).scalar_one_or_none()

    if not product:
        await callback.answer("❌ پلن یافت نشد.", show_alert=True)
        return

    price_30 = product.price
    price_7 = await calc_preset_price(price_30, 7)

    await state.update_data(
        plan_type="preset", product_id=product_id,
        product_name=product.name, data_gb=product.data_gb,
        price_30=str(price_30), price_7=str(price_7),
    )

    await callback.message.edit_text(
        f"📦 {product.name}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 حجم: {product.data_gb} گیگ\n\n"
        f"💰 ۳۰ روزه: {price_30:,.0f} تومان\n"
        f"⚡ ۷ روزه: {price_7:,.0f} تومان (-۶,۰۰۰)\n\n"
        f"مدت اشتراک را انتخاب کنید:",
        reply_markup=duration_kb(product_id),
    )
    await callback.answer()


# ─── Step 2b: custom plan → choose GB ──────────────────────────
@router.callback_query(F.data == "custom_plan")
async def cb_custom_plan(callback: CallbackQuery, state: FSMContext):
    await state.update_data(plan_type="custom")
    await callback.message.edit_text(
        "✏️ سفارشی - حجم دلخواه\n━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 حجم مورد نظر (گیگ) را انتخاب کنید:\n💡 حداقل: ۷ گیگ",
        reply_markup=custom_plan_gb_kb(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cgb_"))
async def cb_custom_gb(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    if data[1] == "custom":
        await state.set_state(BuyService.waiting_custom_gb)
        await callback.message.edit_text(
            "⌨️ حجم دلخواه را به گیگ وارد کنید:\n💡 حداقل ۷، حداکثر ۱۰۰",
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    gb = int(data[1])
    await state.update_data(data_gb=gb)
    await callback.message.edit_text(
        f"📊 حجم: {gb} گیگ\n\n⏰ مدت اشتراک را انتخاب کنید:",
        reply_markup=custom_plan_duration_kb(gb),
    )
    await callback.answer()


@router.message(BuyService.waiting_custom_gb)
async def process_custom_gb(message: Message, state: FSMContext):
    try:
        gb = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً عدد وارد کنید:")
        return
    if gb < 7 or gb > 100:
        await message.answer("❌ حجم باید بین ۷ تا ۱۰۰ گیگ باشد:")
        return

    await state.update_data(data_gb=gb)
    await state.clear()
    await message.answer(
        f"📊 حجم: {gb} گیگ\n\n⏰ مدت اشتراک را انتخاب کنید:",
        reply_markup=custom_plan_duration_kb(gb),
    )


# ─── Step 3: duration selected → calculate price → discount ────
@router.callback_query(F.data.startswith("dur_"))
async def cb_preset_duration(callback: CallbackQuery, state: FSMContext):
    """Preset plan: dur_{product_id}_{days}"""
    parts = callback.data.split("_")
    product_id = int(parts[1])
    days = int(parts[2])
    data = await state.get_data()

    price = Decimal(data["price_30"]) if days == 30 else Decimal(data["price_7"])

    await state.update_data(duration_days=days, base_price=str(price))
    await _show_discount_step(callback, state, data["product_name"], data.get("data_gb", 0), days, price)


@router.callback_query(F.data.startswith("cdur_"))
async def cb_custom_duration(callback: CallbackQuery, state: FSMContext):
    """Custom plan: cdur_{gb}_{days}"""
    parts = callback.data.split("_")
    gb = int(parts[1])
    days = int(parts[2])

    price = await calc_custom_price(gb, days)

    await state.update_data(
        duration_days=days, base_price=str(price),
        data_gb=gb, product_name=f"{gb} گیگ",
    )
    await _show_discount_step(callback, state, f"{gb} گیگ", gb, days, price)


async def _show_discount_step(callback, state, name, gb, days, price):
    await callback.message.edit_text(
        f"📦 {name} | {days} روزه\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 قیمت: {price:,.0f} تومان\n\n"
        f"🏷️ کد تخفیف دارید؟\nکد را بفرستید یا ادامه دهید:",
        reply_markup=discount_skip_kb(),
    )
    await state.set_state(BuyService.apply_discount)
    await callback.answer()


# ─── Step 4: discount code ─────────────────────────────────────
@router.message(BuyService.apply_discount)
async def process_discount_code(message: Message, state: FSMContext):
    code_text = message.text.strip().upper()
    data = await state.get_data()
    price = Decimal(data["base_price"])

    async with async_session() as session:
        disc = (await session.execute(
            select(DiscountCode).where(
                DiscountCode.code == code_text,
                DiscountCode.is_active == True,
            )
        )).scalar_one_or_none()

    now = datetime.utcnow()
    expired = disc.expires_at and disc.expires_at < now if disc else False

    if not disc or expired or (disc.max_uses > 0 and disc.used_count >= disc.max_uses):
        await message.answer(
            "❌ کد تخفیف نامعتبر یا منقضی شده.\n💡 مجدداً تلاش کنید یا ادامه دهید.",
            reply_markup=discount_skip_kb(),
        )
        return

    discount_amount = price * Decimal(str(disc.percent)) / Decimal("100")
    final_price = price - discount_amount

    await state.update_data(
        discount_code=code_text, discount_percent=disc.percent,
        final_price=str(final_price),
    )

    name = data.get("product_name", "?")
    days = data.get("duration_days", 30)

    await message.answer(
        f"✅ کد {code_text} اعمال شد ({disc.percent}%)\n\n"
        f"📦 {name} | {days} روزه\n"
        f"💰 قیمت: {price:,.0f} → {final_price:,.0f} تومان\n\n"
        f"روش پرداخت:",
        reply_markup=payment_choice_kb(),
    )
    await state.set_state(BuyService.confirm_payment)


@router.callback_query(F.data == "skip_discount", BuyService.apply_discount)
async def cb_skip_discount(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    price = Decimal(data["base_price"])
    await state.update_data(final_price=str(price), discount_code=None, discount_percent=0)

    name = data.get("product_name", "?")
    days = data.get("duration_days", 30)

    await callback.message.edit_text(
        f"📦 {name} | {days} روزه\n"
        f"💰 قیمت: {price:,.0f} تومان\n\n"
        f"روش پرداخت:",
        reply_markup=payment_choice_kb(),
    )
    await state.set_state(BuyService.confirm_payment)
    await callback.answer()


# ─── Step 5: payment ───────────────────────────────────────────
@router.callback_query(F.data == "pay_wallet", BuyService.confirm_payment)
async def cb_pay_wallet(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_price = Decimal(data["final_price"])

    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )).scalar_one_or_none()

    if not user or user.wallet_balance < final_price:
        await callback.message.edit_text(
            TEXTS["insufficient_balance"].format(
                balance=f"{user.wallet_balance:,.0f}" if user else "0",
                price=f"{final_price:,.0f}",
            ),
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        await state.clear()
        return

    name = data.get("product_name", "?")
    days = data.get("duration_days", 30)
    disc_code = data.get("discount_code")

    await callback.message.edit_text(
        f"🛒 تایید خرید\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 {name} | {days} روزه\n"
        f"💰 قیمت نهایی: {final_price:,.0f} تومان\n"
        f"💳 روش: کیف پول"
        + (f"\n🏷️ تخفیف: {disc_code}" if disc_code else "")
        + f"\n\nآیا مطمئن هستید؟",
        reply_markup=confirm_buy_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_buy", BuyService.confirm_payment)
async def cb_confirm_wallet(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_price = Decimal(data["final_price"])
    product_id = data.get("product_id")
    product_name = data.get("product_name", "?")
    data_gb = data.get("data_gb", 0)
    duration = data.get("duration_days", 30)
    plan_type = data.get("plan_type", "preset")
    discount_code = data.get("discount_code")
    discount_percent = int(data.get("discount_percent", 0))

    # Single session: check + deduct with row lock to prevent double-spend
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id).with_for_update()
        )).scalar_one_or_none()

        if not user or user.wallet_balance < final_price:
            await callback.message.edit_text(
                TEXTS["insufficient_balance"].format(
                    balance=f"{user.wallet_balance:,.0f}" if user else "0",
                    price=f"{final_price:,.0f}",
                ),
                reply_markup=back_to_menu_kb(),
            )
            await callback.answer()
            await state.clear()
            return

        user.wallet_balance -= final_price

        order = Order(
            user_id=callback.from_user.id,
            product_id=product_id or 0,
            plan_type=plan_type,
            data_gb=data_gb,
            duration_days=duration,
            final_price=final_price,
            discount_code=discount_code,
            discount_percent=discount_percent,
            status=OrderStatus.pending,
            payment_method=PaymentMethod.wallet,
        )
        session.add(order)

        if discount_code:
            disc = (await session.execute(
                select(DiscountCode).where(DiscountCode.code == discount_code)
            )).scalar_one_or_none()
            if disc:
                disc.used_count += 1

        await session.commit()

    await callback.message.edit_text(
        TEXTS["buy_success"].format(order_id=order.id),
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()
    await state.clear()

    disc_info = f"\n🏷️ {discount_code} ({discount_percent}%)" if discount_code else ""
    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        try:
            await callback.bot.send_message(
                admin_id,
                f"🛒 سفارش جدید #{order.id}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 {callback.from_user.first_name} (ID: {callback.from_user.id})\n"
                f"📦 {product_name} | {duration} روزه\n"
                f"💰 {final_price:,.0f} تومان | 💳 کیف پول{disc_info}",
            )
        except Exception:
            pass


# ─── Card transfer ─────────────────────────────────────────────
@router.callback_query(F.data == "pay_card", BuyService.confirm_payment)
async def cb_pay_card(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_price = Decimal(data["final_price"])

    card_number, card_holder = await get_card_info()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ انصراف", callback_data="menu")
    kb.adjust(1)

    await callback.message.edit_text(
        f"🏦 کارت به کارت\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 مبلغ: {final_price:,.0f} تومان\n\n"
        f"💳 شماره کارت:\n`{card_number}`\n"
        f"👤 به نام: {card_holder}\n\n"
        f"📸 تصویر رسید پرداخت را ارسال کنید.",
        reply_markup=kb.as_markup(), parse_mode="Markdown",
    )
    await state.set_state(BuyService.waiting_receipt)
    await callback.answer()


@router.message(BuyService.waiting_receipt, F.photo)
async def process_card_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    final_price = Decimal(data["final_price"])
    product_id = data.get("product_id")
    product_name = data.get("product_name", "?")
    data_gb = data.get("data_gb", 0)
    duration = data.get("duration_days", 30)
    plan_type = data.get("plan_type", "preset")
    discount_code = data.get("discount_code")
    discount_percent = int(data.get("discount_percent", 0))
    receipt_file_id = message.photo[-1].file_id

    async with async_session() as session:
        order = Order(
            user_id=message.from_user.id,
            product_id=product_id or 0,
            plan_type=plan_type,
            data_gb=data_gb,
            duration_days=duration,
            final_price=final_price,
            discount_code=discount_code,
            discount_percent=discount_percent,
            status=OrderStatus.pending,
            payment_method=PaymentMethod.card_transfer,
        )
        session.add(order)

        if discount_code:
            disc = (await session.execute(
                select(DiscountCode).where(DiscountCode.code == discount_code)
            )).scalar_one_or_none()
            if disc:
                disc.used_count += 1

        await session.commit()

    await message.answer(TEXTS["buy_success"].format(order_id=order.id), reply_markup=back_to_menu_kb())
    await state.clear()

    disc_info = f"\n🏷️ {discount_code} ({discount_percent}%)" if discount_code else ""
    admin_ids = await get_admin_ids()
    for admin_id in admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"🛒 سفارش جدید #{order.id}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 {message.from_user.first_name} (ID: {message.from_user.id})\n"
                f"📦 {product_name} | {duration} روزه\n"
                f"💰 {final_price:,.0f} تومان | 💳 کارت به کارت{disc_info}",
            )
            await message.bot.send_photo(
                admin_id, photo=receipt_file_id,
                caption=f"📸 رسید سفارش #{order.id} | {final_price:,.0f} تومان",
            )
        except Exception:
            pass


@router.message(BuyService.waiting_receipt)
async def process_card_invalid(message: Message):
    await message.answer("❌ لطفاً تصویر رسید را ارسال کنید.")


@router.callback_query(F.data == "cancel_pay")
async def cb_cancel_pay(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(TEXTS["buy_cancelled"], reply_markup=back_to_menu_kb())
    await callback.answer()
    await state.clear()
