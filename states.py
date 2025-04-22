from aiogram.fsm.state import StatesGroup, State

MODE_SINGLE = "single"
MODE_ARENA = "arena"


class SettingsState(StatesGroup):
    choosing_model = State()
    choosing_provider = State()
    choosing_mode = State()
    choosing_arena_type = State()


class ChatState(StatesGroup):
    waiting_single_query = State()
    waiting_arena_query = State()
    waiting_arena_vote = State()
