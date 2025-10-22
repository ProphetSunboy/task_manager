from ai_assistant import load_local_model

tokenizer, model = load_local_model()

if model:
    # Явный контекст + явный маркер конца инструкции
    prompt = (
        "Ты — ассистент по личной продуктивности.\n"
        "Задача: Разработка диплома.\n"
        "Описание: Разработать диплом по теме 'Сайт деревенских продуктов'.\n"
        "Дай короткий, практичный совет, как лучше выполнить задачу.\n"
        "Совет:"
    )

    inputs = tokenizer(prompt, return_tensors="pt")

    output = model.generate(
        **inputs,
        max_new_tokens=60,  # ограничиваем длину совета
        temperature=0.7,  # меньше случайности
        top_p=0.9,  # немного разнообразия
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    # Декодирование
    text = tokenizer.decode(output[0], skip_special_tokens=True)

    # Отделяем только часть после "Совет:"
    if "Совет:" in text:
        text = text.split("Совет:")[-1].strip()

    # Убираем возможный мусор
    text = text.replace("\n", " ").strip()
    if not text:
        text = "Попробуй разделить проект на этапы и начни с основной структуры сайта."

    print("💡 Совет ИИ:", text)
else:
    print("❌ Модель не загрузилась.")
