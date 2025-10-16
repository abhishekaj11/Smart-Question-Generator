from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

topic = "Renewable Energy Systems"
prompt = f"""
Generate 8 engineering exam questions for the topic "{topic}".
Categorize them into Easy, Medium, and Hard.
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
