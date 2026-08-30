from decimal import Decimal

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database.engine import async_session
from database.models import Product
from keyboards.inline import (
    admin_products_kb, admin_menu_kb, back_to_admin_kb, admin_product_edit_kb,
    admin_product_type_kb,
)
from locales.fa import TEXTS
from states.states import AdminAddProduct, AdminEditProduct
from config import get_admin_ids, is_admin

router = Router()


@router.callback_query(F.data == "admin_products")
async def cb_admin_products(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.created_at.desc())
        )
        products = result.scalars().all()

    await callback.message.edit_text(
        "📦 مدیریت پلن‌ها\n\n روی پلن کلیک کنید برای ویرایش:",
        reply_markup=admin_products_kb(products),
    )
    await callback.answer()


# Toggle active status
@router.callback_query(F.data.startswith("admin_toggle_prod_"))
async def cb_toggle_product(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == prod_id)
        )
        product = result.scalar_one_or_none()
        if product:
            product.is_active = not product.is_active
            await session.commit()

    await callback.answer("✅ وضعیت تغییر کرد.")

    # Show product details again
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == prod_id)
        )
        product = result.scalar_one_or_none()

    if product:
        status = "✅ فعال" if product.is_active else "❌ غیرفعال"
        test = "🧪 تست" if product.is_test else "🛒 فروش"
        text = (
            f"📦 اطلاعات پلن\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 نام: {product.name}\n"
            f"💰 قیمت: {product.price:,.0f} تومان\n"
            f"⏰ مدت: {product.duration_days} روز\n"
            f"📝 توضیحات: {product.description or 'ندارد'}\n"
            f"🔄 وضعیت: {status}\n"
            f"🏷️ نوع: {test}"
        )
        await callback.message.edit_text(text, reply_markup=admin_product_edit_kb(prod_id))


# Delete product
@router.callback_query(F.data.startswith("admin_delete_prod_"))
async def cb_delete_product(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == prod_id)
        )
        product = result.scalar_one_or_none()
        if product:
            await session.delete(product)
            await session.commit()

    await callback.answer("✅ پلن حذف شد.")

    async with async_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.created_at.desc())
        )
        products = result.scalars().all()

    await callback.message.edit_text(
        "📦 مدیریت پلن‌ها\n\n روی پلن کلیک کنید برای ویرایش:",
        reply_markup=admin_products_kb(products),
    )


# View product details
@router.callback_query(F.data.startswith("admin_view_prod_"))
async def cb_view_product(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == prod_id)
        )
        product = result.scalar_one_or_none()

    if not product:
        await callback.answer("❌ پلن یافت نشد.", show_alert=True)
        return

    status = "✅ فعال" if product.is_active else "❌ غیرفعال"
    test = "🧪 تست" if product.is_test else "🛒 فروش"

    text = (
        f"📦 اطلاعات پلن\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 نام: {product.name}\n"
        f"💰 قیمت: {product.price:,.0f} تومان\n"
        f"⏰ مدت: {product.duration_days} روز\n"
        f"📝 توضیحات: {product.description or 'ندارد'}\n"
        f"🔄 وضعیت: {status}\n"
        f"🏷️ نوع: {test}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=admin_product_edit_kb(prod_id),
    )
    await callback.answer()


# Edit product name
@router.callback_query(F.data.startswith("edit_prod_name_"))
async def cb_edit_prod_name(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("📝 نام جدید پلن را وارد کنید:", reply_markup=back_to_admin_kb())
    await state.set_state(AdminEditProduct.value)
    await state.update_data(field="name", product_id=prod_id)
    await callback.answer()


# Edit product price
@router.callback_query(F.data.startswith("edit_prod_price_"))
async def cb_edit_prod_price(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("💰 قیمت جدید (تومان) را وارد کنید:", reply_markup=back_to_admin_kb())
    await state.set_state(AdminEditProduct.value)
    await state.update_data(field="price", product_id=prod_id)
    await callback.answer()


# Edit product duration
@router.callback_query(F.data.startswith("edit_prod_duration_"))
async def cb_edit_prod_duration(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("⏰ مدت جدید (روز) را وارد کنید:", reply_markup=back_to_admin_kb())
    await state.set_state(AdminEditProduct.value)
    await state.update_data(field="duration_days", product_id=prod_id)
    await callback.answer()


# Edit product description
@router.callback_query(F.data.startswith("edit_prod_desc_"))
async def cb_edit_prod_desc(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("📝 توضیحات جدید را وارد کنید:", reply_markup=back_to_admin_kb())
    await state.set_state(AdminEditProduct.value)
    await state.update_data(field="description", product_id=prod_id)
    await callback.answer()


# Edit product data/volume
@router.callback_query(F.data.startswith("edit_prod_data_"))
async def cb_edit_prod_data(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    prod_id = int(callback.data.split("_")[3])
    await callback.message.edit_text("📊 حجم جدید (GB) را وارد کنید:", reply_markup=back_to_admin_kb())
    await state.set_state(AdminEditProduct.value)
    await state.update_data(field="data_gb", product_id=prod_id)
    await callback.answer()


@router.message(AdminEditProduct.value)
async def process_edit_product(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    data = await state.get_data()
    field = data["field"]
    product_id = data["product_id"]

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            await message.answer("❌ پلن یافت نشد.", reply_markup=admin_menu_kb())
            await state.clear()
            return

        if field == "name":
            product.name = message.text.strip()
        elif field == "price":
            try:
                product.price = Decimal(message.text.replace(",", "").strip())
            except ValueError:
                await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
                return
        elif field == "duration_days":
            try:
                product.duration_days = int(message.text.strip())
            except ValueError:
                await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
                return
        elif field == "data_gb":
            try:
                product.data_gb = int(message.text.strip())
            except ValueError:
                await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
                return
        elif field == "description":
            product.description = message.text.strip()

        await session.commit()

    await message.answer("✅ پلن با موفقیت ویرایش شد.", reply_markup=admin_menu_kb())
    await state.clear()


# Add new product
@router.callback_query(F.data == "admin_add_product")
async def cb_add_product(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    await callback.message.edit_text(
        "➕ افزودن پلن جدید\n\n📝 نام پلن را وارد کنید:",
        reply_markup=back_to_admin_kb(),
    )
    await state.set_state(AdminAddProduct.name)
    await callback.answer()


# Product type selected (sell/test)
@router.callback_query(F.data.startswith("prodtype_"), AdminAddProduct.type)
async def cb_product_type(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ دسترسی غیرمجاز", show_alert=True)
        return

    ptype = "test" if callback.data == "prodtype_test" else "sell"
    data = await state.get_data()

    if ptype == "test":
        # Test plan: create directly with zero price
        async with async_session() as session:
            product = Product(
                name=data["name"],
                description=data["description"],
                duration_days=data["duration"],
                data_gb=0,
                price=Decimal("0"),
                is_active=True,
                is_test=True,
            )
            session.add(product)
            await session.commit()

        await callback.message.answer(
            "✅ پلن تست ساخته شد!\n\n"
            f"📝 نام: {data['name']}\n"
            f"⏰ مدت: {data['duration']} روز\n"
            "💡 کاربران فقط یک بار می‌توانند از آن استفاده کنند.",
            reply_markup=admin_menu_kb(),
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(is_test=False)
    await callback.message.answer("💰 قیمت پلن به تومان را وارد کنید:")
    await state.set_state(AdminAddProduct.price)
    await callback.answer()


@router.message(AdminAddProduct.name)
async def process_product_name(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await message.answer("📝 توضیحات پلن را وارد کنید:")
    await state.set_state(AdminAddProduct.description)


@router.message(AdminAddProduct.description)
async def process_product_desc(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text.strip())
    await message.answer("⏰ مدت پلن به روز را وارد کنید (مثال: 30):")
    await state.set_state(AdminAddProduct.duration)


@router.message(AdminAddProduct.duration)
async def process_product_duration(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        duration = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
        return
    await state.update_data(duration=duration)
    await message.answer(
        "🏷️ نوع پلن را انتخاب کنید:",
        reply_markup=admin_product_type_kb(),
    )
    await state.set_state(AdminAddProduct.type)


@router.message(AdminAddProduct.price)
async def process_product_price(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        price = Decimal(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد صحیح وارد کنید:")
        return

    data = await state.get_data()

    async with async_session() as session:
        product = Product(
            name=data["name"],
            description=data["description"],
            duration_days=data["duration"],
            price=price,
            is_active=True,
            is_test=False,
        )
        session.add(product)
        await session.commit()

    await message.answer(TEXTS["admin_added"], reply_markup=admin_menu_kb())
    await state.clear()
