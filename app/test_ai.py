from ai_assistant import load_local_model

tokenizer, model = load_local_model()

if model:
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
        max_new_tokens=60,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    text = tokenizer.decode(output[0], skip_special_tokens=True)

    if "Совет:" in text:
        text = text.split("Совет:")[-1].strip()

    text = text.replace("\n", " ").strip()
    if not text:
        text = "Попробуй разделить проект на этапы и начни с основной структуры сайта."

    print("💡 Совет ИИ:", text)
else:
    print("❌ Модель не загрузилась.")
