import os
import random
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import InferenceClient

BASE_DIR = Path(__file__).parent

# 🔹 Пути к локальным моделям
RU_LOCAL = (BASE_DIR / "models" / "rugpt3small").resolve()
EN_LOCAL = (BASE_DIR / "models" / "distilgpt2").resolve()

# 🔹 Модели Hugging Face
HF_MODELS = {
    "ru": "ai-forever/FRED-T5-1.7B",
    "en": "mistralai/Mistral-7B-Instruct-v0.2",
}

HF_TOKEN = os.getenv("HF_TOKEN", "HF_TOKEN_HERE")

# 🔹 Словарь для ленивой загрузки моделей
_models = {}


def _load_local_model(lang):
    """Загружает локальную модель при необходимости"""
    path = RU_LOCAL if lang == "ru" else EN_LOCAL
    if not os.path.isdir(path):
        return None, None
    try:
        print(f"✅ Загружаем локальную модель из {path}")
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True)
        _models[lang] = (tokenizer, model)
        return tokenizer, model
    except Exception as e:
        print(f"⚠️ Ошибка загрузки локальной модели: {e}")
        return None, None


def _generate_local(prompt, lang="ru"):
    """Генерация через локальную модель (fallback)"""
    tokenizer, model = _models.get(lang, (None, None))
    if tokenizer is None or model is None:
        tokenizer, model = _load_local_model(lang)
        if tokenizer is None:
            return None

    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(
        **inputs,
        max_length=200,
        temperature=0.8,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    text = tokenizer.decode(output[0], skip_special_tokens=True)
    return text.replace(prompt, "").strip()


def _generate_hf(prompt, lang="ru"):
    """Генерация текста через Hugging Face API"""
    model_name = HF_MODELS["ru"] if lang == "ru" else HF_MODELS["en"]
    print(f"🌐 Генерация через Hugging Face API ({model_name})...")

    client = InferenceClient(model=model_name, token=HF_TOKEN)

    try:
        # 🧠 Некоторые модели (например Mistral) работают только в режиме "conversational"
        if "mistral" in model_name.lower():
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful and concise time management assistant.",
                },
                {"role": "user", "content": prompt},
            ]
            response = client.chat_completion(messages, max_tokens=250, temperature=0.7)
            return response.choices[0].message["content"].strip()
        else:
            # 🔹 Обычный режим text-generation (для FRED-T5 и других)
            response = client.text_generation(
                prompt,
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
            )
            return response.strip()
    except Exception as e:
        print(f"⚠️ Ошибка Hugging Face API: {e}")
        return None


def get_task_advice(task, lang="ru"):
    """Генерация совета по тайм-менеджменту"""
    title = getattr(task, "title", "")
    desc = getattr(task, "description", "")
    allocated = getattr(task, "allocated_time", 0)
    deadline = getattr(task, "deadline", None)
    pomo_work = getattr(task, "pomodoro_work", 25)
    pomo_break = getattr(task, "pomodoro_break", 5)

    now = datetime.now()
    days_left = None
    if deadline:
        try:
            deadline_date = deadline.date() if hasattr(deadline, "date") else deadline
            days_left = (deadline_date - now.date()).days
        except Exception:
            days_left = None

    if lang == "ru":
        prompt = (
            "Ты — профессиональный ассистент по тайм-менеджменту. "
            "Проанализируй задачу и дай конкретный, краткий совет для повышения эффективности.\n\n"
            f"Задача: {title}\n"
            f"Описание: {desc}\n"
            f"Выделено времени: {allocated} мин.\n"
            f"Дедлайн: {days_left if days_left is not None else 'не задан'} дн.\n"
            f"Pomodoro: {pomo_work}/{pomo_break} мин.\n"
            "Совет:"
        )
    else:
        prompt = (
            "You are an expert time management assistant. "
            "Analyze the task and give a concise, practical productivity tip.\n\n"
            f"Task: {title}\n"
            f"Description: {desc}\n"
            f"Allocated time: {allocated} min.\n"
            f"Deadline: {days_left if days_left is not None else 'not set'} days.\n"
            f"Pomodoro: {pomo_work}/{pomo_break} min.\n"
            "Tip:"
        )

    # 1️⃣ Пытаемся через API
    try:
        text = _generate_hf(prompt, lang)
    except Exception as e:
        print(f"⚠️ Ошибка API Hugging Face: {e}")
        text = None

    # 2️⃣ Если не сработало — fallback на локальную модель
    if not text:
        text = _generate_local(prompt, lang)

    # 3️⃣ Если совсем ничего — статический совет
    if not text or len(text) < 10:
        backup_ru = [
            "Разбей задачу на конкретные шаги и начни с самого простого.",
            "Выдели приоритеты и работай в коротких фокус-сессиях.",
            "Поставь таймер и избегай отвлекающих факторов.",
        ]
        backup_en = [
            "Break the task into specific steps and start with the simplest one.",
            "Set clear priorities and work in focused short sessions.",
            "Use a timer and minimize distractions.",
        ]
        text = random.choice(backup_ru if lang == "ru" else backup_en)

    return text.strip()
