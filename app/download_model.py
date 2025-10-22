from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "databricks/dolly-v2-7b"
save_path = "./models/dollyv2"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print("✅ Модель успешно скачана и сохранена локально!")
