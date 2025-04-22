import random
from io import BytesIO

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from handlers.response_handler import handle_model_response
from keyboards.inline_keyboards import get_arena_vote_keyboard
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry, TextToTextModel, TextToImgModel, ImgToTextModel, AudioToTextModel
from states import ChatState
from utils.transcription import transcribe_voice_message

router = Router()


@router.message(F.text, ChatState.waiting_arena_query)
async def arena_text_query_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    print(f"ARENA Handler (Text): Mode is {data.get('mode')}")
    await message.answer("Обработка вашего текстового запроса в режиме арены...")

    registry = AIRegistry()
    arena_type = data.get('arena_type')
    if not arena_type:
        await message.answer("Тип арены не выбран. Пожалуйста, выберите тип арены.",
                             reply_markup=get_settings_reply_keyboard())
        return
    models = None
    match arena_type:
        case "text":
            models = registry.get_models_by_type(TextToTextModel)
        case "image":
            models = registry.get_models_by_type(TextToImgModel)
    if not models or len(models) < 2:
        await message.answer("Нет моделей для выбранного типа арены.",
                             reply_markup=get_settings_reply_keyboard())
        return

    models = random.sample(models, 2)
    print(models)
    for index, model in enumerate(models):
        try:
            response = await model.execute(message.text)
        except Exception as e:
            print(e)
            response = None
        await message.answer(f"Ответ {index + 1} модели:")
        await handle_model_response(message, response)

    await state.update_data(arena_current_pair=(models[0], models[1]))
    await state.set_state(ChatState.waiting_arena_vote)
    await message.answer("Выберите лучший ответ:", reply_markup=get_arena_vote_keyboard())


@router.message(F.photo, ChatState.waiting_arena_query)
async def arena_photo_query_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    print(f"ARENA Handler (Photo): Mode is {data.get('mode')}")
    await message.answer("Обработка вашего фото в режиме арены...")
    registry = AIRegistry()
    arena_type = data.get('arena_type')
    if not arena_type:
        await message.answer("Тип арены не выбран. Пожалуйста, выберите тип арены.",
                             reply_markup=get_settings_reply_keyboard())
        return

    models = None
    match arena_type:
        case "text":
            models = registry.get_models_by_type(ImgToTextModel)

    if not models or len(models) < 2:
        await message.answer("Нет моделей для выбранного типа арены.",
                             reply_markup=get_settings_reply_keyboard())
        return
    models = random.sample(models, 2)
    print(models)

    photo = message.photo[-1]
    photo_bytes = await message.bot.download(photo)
    image_data = BytesIO(photo_bytes.read())
    prompt = message.caption or ""

    for index, model in enumerate(models):
        try:
            response = await model.execute(image_data, prompt)
        except Exception as e:
            print(e)
            response = None
        await message.answer(f"Ответ {index + 1} модели:")
        await handle_model_response(message, response)

    await state.update_data(arena_current_pair=(models[0], models[1]))
    await state.set_state(ChatState.waiting_arena_vote)
    await message.answer("Выберите лучший ответ:", reply_markup=get_arena_vote_keyboard())


@router.message(F.voice, ChatState.waiting_arena_query)
async def arena_voice_query_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    print(f"ARENA Handler (Voice): Mode is {data.get('mode')}")
    await message.answer("Обработка вашего голоса в режиме арены...")
    # TODO: Логика обработки голоса для арены
    registry = AIRegistry()
    arena_type = data.get('arena_type')

    if not arena_type:
        await message.answer("Тип арены не выбран. Пожалуйста, выберите тип арены.",
                             reply_markup=get_settings_reply_keyboard())
        return

    models = None
    match arena_type:
        case "text":
            models = registry.get_models_by_type(TextToTextModel)
        case "image":
            models = registry.get_models_by_type(TextToImgModel)

    if not models or len(models) < 2:
        await message.answer("Нет моделей для выбранного типа арены.",
                             reply_markup=get_settings_reply_keyboard())
        return

    models = random.sample(models, 2)
    print(models)

    for index, model in enumerate(models):
        try:
            if AudioToTextModel in model.meta.capabilities:
                voice = message.voice
                voice_bytes = await message.bot.download(voice)
                voice_data = BytesIO(voice_bytes.read())
                response = await model.execute(voice_data)
            else:
                text = await transcribe_voice_message(message, registry)
                response = await model.execute(text)
        except Exception as e:
            print(e)
            response = None
        await message.answer(f"Ответ {index + 1} модели:")
        await handle_model_response(message, response)
    await state.update_data(arena_current_pair=(models[0], models[1]))
    await state.set_state(ChatState.waiting_arena_vote)
    await message.answer("Выберите лучший ответ:", reply_markup=get_arena_vote_keyboard())


@router.callback_query(F.data.startswith("vote_"), ChatState.waiting_arena_vote)
async def arena_vote_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    models = data.get('arena_current_pair')
    print(f"ARENA Vote Handler: Got vote {callback.data} for {models}")

    vote = callback.data.split("_")[1]
    if vote == "1":
        print(f"Voted for {models[0]}")
    elif vote == "2":
        print(f"Voted for {models[1]}")
    else:
        print(f"voted against everyone")

    # TODO: обновить рейтинг, ну и че-нить там еще, не знаю
    await callback.answer("Ваш голос принят!")
    await state.update_data(arena_current_pair=None)
    await state.set_state(ChatState.waiting_arena_query)
    await callback.message.answer(
        "Ожидаю ваш следующий запрос для арены.",
        reply_markup=get_settings_reply_keyboard())
