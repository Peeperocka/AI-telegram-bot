from aiogram.fsm.state import StatesGroup, State


class SettingsState(StatesGroup):
    choosing_model = State()
    choosing_provider = State()
    choosing_mode = State()


class ChatState(StatesGroup):
    waiting_query = State()
