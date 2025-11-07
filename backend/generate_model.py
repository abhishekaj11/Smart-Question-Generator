from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os


def load_model(model_name: str):
	"""Load tokenizer and model with a safe fallback and clearer error reporting."""
	try:
		tokenizer = AutoTokenizer.from_pretrained(model_name)
		model = AutoModelForCausalLM.from_pretrained(
			model_name,
			device_map="auto",
			torch_dtype="auto",
			low_cpu_mem_usage=True,
		)
		return tokenizer, model
	except Exception as e:
		# Provide a helpful message and re-raise so callers can decide what to do
		raise RuntimeError(
			f"Failed to load model '{model_name}'.\nOriginal error: {e}\n"
			"If you're running on a machine without enough memory/GPU, consider using a smaller model "
			"or remove device_map='auto'."
		)


def generate_for_topic(topic: str, model_name: str = "tiiuae/falcon-7b-instruct") -> str:
	tokenizer, model = load_model(model_name)

	prompt = f"""
	Generate 8 engineering exam questions for the topic "{topic}".
	Categorize them into Easy, Medium, and Hard.
	"""

	# Prepare inputs on CPU by default. Move to CUDA if available.
	inputs = tokenizer(prompt, return_tensors="pt")
	if torch.cuda.is_available():
		inputs = {k: v.cuda() for k, v in inputs.items()}

	outputs = model.generate(**inputs, max_new_tokens=400, temperature=0.7)
	return tokenizer.decode(outputs[0], skip_special_tokens=True)


if __name__ == "__main__":
	# Allow overriding topic and model via environment variables for quick testing
	topic = os.environ.get("SQG_TOPIC", "Renewable Energy Systems")
	model_name = os.environ.get("SQG_MODEL", "tiiuae/falcon-7b-instruct")

	try:
		generated = generate_for_topic(topic, model_name=model_name)
		print(generated)
	except Exception as err:
		print("Error while generating questions:\n", err)
