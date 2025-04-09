from aiogram.fsm.state import StatesGroup, State


class SettingsState(StatesGroup):
    choosing_mode = State()
    choosing_network_single = State()


class ChatState(StatesGroup):
    waiting_query = State()
