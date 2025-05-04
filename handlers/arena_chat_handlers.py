import random
from io import BytesIO

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from database import get_model_rating, update_model_rating
from handlers.response_handler import handle_model_response
from keyboards.inline_keyboards import get_arena_vote_keyboard
from keyboards.reply_keyboards import get_settings_reply_keyboard
from registry import AIRegistry, TextToTextModel, TextToImgModel, ImgToTextModel, AudioToTextModel
from states import ChatState
from utils.transcription import transcribe_voice_message
from utils.utils import calculate_elo_update

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
            if arena_type == "text" and TextToImgModel in model.meta.capabilities:
                response = await model.execute(message.text, enforce_text_response=True)
            else:
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
    model_objects = data.get('arena_current_pair')

    if not model_objects or len(model_objects) != 2:
        print("Error: Invalid 'arena_current_pair' data in state.")
        await callback.answer("Произошла ошибка при обработке голоса. Попробуйте снова.", show_alert=True)
        await state.set_state(ChatState.waiting_arena_query)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Error editing reply markup: {e}")
            pass
        return

    try:
        model_id_1 = f"{model_objects[0].meta.provider.lower()}:{model_objects[0].meta.version}"
        model_id_2 = f"{model_objects[1].meta.provider.lower()}:{model_objects[1].meta.version}"
        print(f"ARENA Vote Handler: Got vote {callback.data} for pair IDs: [{model_id_1}, {model_id_2}]")
    except AttributeError as e:
        print(f"Error: Could not extract model ID from state objects: {e}. Objects: {model_objects}")
        await callback.answer("Произошла ошибка данных моделей. Попробуйте снова.", show_alert=True)
        await state.set_state(ChatState.waiting_arena_query)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            print(f"Error editing reply markup: {e}")
            pass
        return

    vote = callback.data.split("_")[1]
    winner_model_id = None
    is_tie = False

    if vote == "1":
        winner_model_id = model_id_1
        print(f"Voted for model 1 ID: {winner_model_id}")
    elif vote == "2":
        winner_model_id = model_id_2
        print(f"Voted for model 2 ID: {winner_model_id}")
    elif vote == "tie":
        is_tie = True
        print(f"Voted TIE for {model_id_1} vs {model_id_2}")
    else:
        print(f"Unexpected vote value: {vote}")
        await callback.answer("Некорректный голос, попробуйте еще раз", show_alert=True)
        return

    try:
        rating1 = get_model_rating(model_id_1)
        rating2 = get_model_rating(model_id_2)

        if rating1 is not None and rating2 is not None:
            if is_tie:
                new_rating1, new_rating2 = calculate_elo_update(rating1, rating2, score_a=0.5)
            elif winner_model_id:
                if winner_model_id == model_id_1:
                    new_rating1, new_rating2 = calculate_elo_update(rating1, rating2, score_a=1.0)
                else:
                    new_rating2, new_rating1 = calculate_elo_update(rating2, rating1, score_a=1.0)
            else:
                print("Error: Vote processed but no winner/loser/tie identified for rating calculation.")
                raise ValueError("Rating calculation logic error")

            update_model_rating(model_id_1, new_rating1)
            update_model_rating(model_id_2, new_rating2)
            print(f"Ratings updated: {model_id_1}={new_rating1}, {model_id_2}={new_rating2}")

        else:
            print(
                f"Error: Could not retrieve ratings for one or both models: {model_id_1} ({rating1}), {model_id_2} ({rating2})")

    except Exception as e:
        print(f"Error during rating update process: {e}")

    await callback.answer("Ваш голос принят!")

    await state.update_data(arena_current_pair=None)
    await state.set_state(ChatState.waiting_arena_query)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"Could not edit message reply markup: {e}")

    await callback.message.answer(
        "Ожидаю ваш следующий запрос для арены.",
        reply_markup=get_settings_reply_keyboard()
    )
