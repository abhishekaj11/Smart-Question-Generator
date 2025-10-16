from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os

# === Step 1: Configuration ===
model_name = "tiiuae/falcon-rw-1b"  # Small and lightweight model
local_dir = "./falcon-rw-1b-local"  # Local save directory

# === Step 2: Load model/tokenizer (from local if available) ===
if os.path.exists(local_dir):
    print("[INFO] Loading model and tokenizer from local directory...")
    tokenizer = AutoTokenizer.from_pretrained(local_dir)
    model = AutoModelForCausalLM.from_pretrained(local_dir)
else:
    print("[INFO] Downloading model and tokenizer from Hugging Face...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # Save locally for future use
    print("[INFO] Saving model and tokenizer locally...")
    tokenizer.save_pretrained(local_dir)
    model.save_pretrained(local_dir)

# === Step 3: Prompt setup ===
topic = "Renewable Energy Systems"
prompt = f"""
Generate 8 engineering exam questions for the topic "{topic}".
Categorize them into Easy, Medium, and Hard.
"""

# === Step 4: Tokenize and run inference ===
inputs = tokenizer(prompt, return_tensors="pt")
inputs = {k: v.to(model.device) for k, v in inputs.items()}  # Move to model's device

# Generation settings
generation_config = {
    "max_new_tokens": 300,
    "temperature": 0.7,
    "top_k": 50,
    "top_p": 0.95,
    "do_sample": True,
}

with torch.no_grad():
    outputs = model.generate(**inputs, **generation_config)

# === Step 5: Decode and print ===
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n[Generated Exam Questions]:\n")
print(generated_text)
