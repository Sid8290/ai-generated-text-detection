from flask import Flask, render_template, request, jsonify
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = "./model"
MAX_TOKENS = 256          # model's processing limit
MAX_CHARS = 20000         # reject excessively large input

app = Flask(__name__)

# Load the tokenizer and model once, when the app starts.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Loading model '{MODEL_PATH}' on {device} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.to(device)
model.eval()
print("Model ready.")


def display_label(pred_id):
    """Turn the model's configured label (HUMAN / AI) into a display name."""
    name = str(model.config.id2label.get(pred_id, "")).upper()
    if name == "HUMAN":
        return "HUMAN"
    if name == "AI":
        return "AI GENERATED"
    # Fallback if the config only has generic names: 0 = HUMAN, 1 = AI
    return "HUMAN" if pred_id == 0 else "AI GENERATED"


def predict_text(text):
    """Run the model on one text and return probabilities and the prediction."""
    truncated = len(tokenizer.tokenize(text)) + 2 > MAX_TOKENS  # +2 for [CLS] and [SEP]

    inputs = tokenizer(
        text,
        truncation=True,
        max_length=MAX_TOKENS,
        return_tensors="pt",
    ).to(device)

    with torch.inference_mode():
        logits = model(**inputs).logits

    probs = torch.softmax(logits, dim=-1)[0].cpu().tolist()
    pred_id = int(torch.tensor(probs).argmax())

    return {
        "label": display_label(pred_id),
        "confidence": round(probs[pred_id], 6),
        "prob_human": round(probs[0], 6),
        "prob_ai": round(probs[1], 6),
        "truncated": truncated,
    }


@app.route("/")
def index():
    return render_template("index.html", max_chars=MAX_CHARS)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Invalid request. Send JSON with a 'text' field."}), 400

    text = data["text"]
    if not isinstance(text, str):
        return jsonify({"error": "'text' must be a string."}), 400

    text = text.strip()
    if not text:
        return jsonify({"error": "Please enter some text to analyze."}), 400
    if len(text) > MAX_CHARS:
        return jsonify({"error": f"Text is too long. The maximum is {MAX_CHARS:,} characters."}), 400

    try:
        result = predict_text(text)
    except Exception as exc:
        print("Prediction error:", exc)
        return jsonify({"error": "Something went wrong while analyzing the text."}), 500

    return jsonify(result)


if __name__ == "__main__":
    # debug is off so the model is not loaded twice by the auto-reloader
    app.run(host="127.0.0.1", port=5000, debug=False)