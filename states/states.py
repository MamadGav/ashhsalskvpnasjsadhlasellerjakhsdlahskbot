from aiogram.fsm.state import State, StatesGroup


class WalletCharge(StatesGroup):
    enter_amount = State()
    upload_receipt = State()


class BuyService(StatesGroup):
    waiting_receipt = State()
    apply_discount = State()
    confirm_payment = State()
    waiting_custom_gb = State()


class SupportState(StatesGroup):
    waiting_message = State()
    admin_reply = State()


class AdminAddProduct(StatesGroup):
    name = State()
    description = State()
    duration = State()
    type = State()
    price = State()


class AdminEditProduct(StatesGroup):
    value = State()


class AdminEditSetting(StatesGroup):
    value = State()


class AdminChargeWallet(StatesGroup):
    amount = State()


class AdminConfigSend(StatesGroup):
    waiting_config = State()


class AdminDiscountCode(StatesGroup):
    code = State()
    percent = State()
    max_uses = State()
    expires = State()


class AdminManageAdmin(StatesGroup):
    waiting_user_id = State()


class AdminEditCard(StatesGroup):
    waiting_number = State()
    waiting_holder = State()
