from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from database.engine import async_session
from database.models import User, Order, OrderStatus, Product
from keyboards.inline import back_to_menu_kb
from locales.fa import TEXTS

router = Router()


@router.callback_query(F.data == "my_services")
async def cb_my_services(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(Order)
            .where(
                Order.user_id == callback.from_user.id,
                Order.status == OrderStatus.approved,
            )
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        # Eagerly load product for each order
        orders_data = []
        for order in orders:
            prod_result = await session.execute(
                select(Product).where(Product.id == order.product_id)
            )
            product = prod_result.scalar_one_or_none()
            orders_data.append({"order": order, "product": product})

    if not orders_data:
        await callback.message.edit_text(
            TEXTS["my_services_empty"],
            reply_markup=back_to_menu_kb(),
        )
        await callback.answer()
        return

    lines = [TEXTS["my_services"]]
    for item in orders_data:
        order = item["order"]
        product = item["product"]
        expires = order.expires_at.strftime("%Y/%m/%d") if order.expires_at else "نامشخص"
        status = "✅ فعال" if order.config_link else "⏳ در انتظار کانفیگ"
        product_text = TEXTS["service_item"].format(
            order_id=order.id,
            product_name=product.name if product else "نامشخص",
            expires=expires,
            status=status,
        )
        lines.append(product_text)
        if order.config_link:
            lines.append(TEXTS["service_config"].format(config=order.config_link))

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()
