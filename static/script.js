const textInput = document.getElementById("text-input");
const counter = document.getElementById("counter");
const analyzeBtn = document.getElementById("analyze-btn");
const btnLabel = document.getElementById("btn-label");
const spinner = document.getElementById("spinner");
const errorBox = document.getElementById("error");
const resultCard = document.getElementById("result-card");
const resultLabel = document.getElementById("result-label");
const resultConfidence = document.getElementById("result-confidence");
const barFill = document.getElementById("bar-fill");
const truncatedNote = document.getElementById("truncated-note");

const maxChars = parseInt(textInput.dataset.maxChars, 10);

function updateCounter() {
  const text = textInput.value;
  const trimmed = text.trim();
  const words = trimmed ? trimmed.split(/\s+/).length : 0;
  counter.textContent =
    words + (words === 1 ? " word" : " words") +
    " \u00B7 " + text.length.toLocaleString() + " / " + maxChars.toLocaleString() + " characters";
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.textContent = "";
  errorBox.hidden = true;
}

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  spinner.hidden = !isLoading;
  btnLabel.textContent = isLoading ? "Analyzing..." : "Analyze";
}

function showResult(data) {
  const isHuman = data.label === "HUMAN";
  const percent = (data.confidence * 100).toFixed(2);

  resultCard.classList.remove("human", "ai");
  resultCard.classList.add(isHuman ? "human" : "ai");

  resultLabel.textContent = data.label;
  resultConfidence.textContent = percent + "%";
  barFill.style.width = percent + "%";
  truncatedNote.hidden = !data.truncated;

  resultCard.hidden = false;
}

async function analyze() {
  clearError();

  const text = textInput.value.trim();
  if (!text) {
    resultCard.hidden = true;
    showError("Please enter some text to analyze.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    });

    const data = await response.json();

    if (!response.ok) {
      resultCard.hidden = true;
      showError(data.error || "Something went wrong. Please try again.");
      return;
    }

    showResult(data);
  } catch (err) {
    resultCard.hidden = true;
    showError("Could not reach the server. Make sure Flask is running.");
  } finally {
    setLoading(false);
  }
}

textInput.addEventListener("input", updateCounter);
analyzeBtn.addEventListener("click", analyze);
updateCounter();