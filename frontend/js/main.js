// APPLICATION URL
const BACKEND = "https://yt-analyzer-p56w.onrender.com";

const form = document.querySelector("#form");
const urlInput = document.querySelector("#url");
const runBtn = document.querySelector("#run");
const loadingEl = document.querySelector("#loading");
const errorEl = document.querySelector("#error");
const resultEl = document.querySelector("#result");

let clientId = localStorage.getItem("clientId");
if (!clientId) {
  clientId = crypto.randomUUID();
  localStorage.setItem("clientId", clientId);
}

const VERDICT = {
  clickbait: { color: "#FF5A5F", explain: "High risk — the title promises more than the content delivers." },
  neutral:   { color: "#F0B23D", explain: "Mixed signals — not enough to call it either way." },
  relevant:  { color: "#2FD08A", explain: "Low risk — title and comments look consistent." }
};

const SOURCE = {
  database: "Database (cache)",
  youtube_api_and_nlp: "YouTube API & NLP"
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) {
    showError("Please enter a proper YouTube video link.");
    return;
  }

  hideError();
  resultEl.classList.add("hidden");
  loadingEl.classList.add("visible");
  runBtn.disabled = true;

  const MIN_LOADING_TIME = 600;
  try {
    const [response] = await Promise.all([
      fetch(`${BACKEND}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Client-ID": clientId
        },
        body: JSON.stringify({ video_url: url })
      }),
      sleep(MIN_LOADING_TIME)
    ]);

    const data = await response.json();

    if (!response.ok) {
      let errorMessage = "An error occurred on the server.";
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          errorMessage = data.detail[0].msg;
        } else if (typeof data.detail === "string") {
          errorMessage = data.detail;
        }
      }
      throw new Error(errorMessage);
    }

    displayResults(data);
    urlInput.value = "";
  } catch (err) {
    showError(err.message);
  } finally {
    loadingEl.classList.remove("visible");
    runBtn.disabled = false;
  }
});

function displayResults(data) {
  const verdict = data.analyze_results.overall_sentiment;
  const score = Math.round(data.analyze_results.clickbait_score);
  const meta = VERDICT[verdict] || { color: "#F0B23D", explain: "Couldn't analyze comments." };
  const color = meta.color;

  document.querySelector("#pill").className = "pill " + verdict;
  document.querySelector("#pillText").textContent = verdict ? verdict.charAt(0).toUpperCase() + verdict.slice(1) : "";

  const scoreEl = document.querySelector("#score");
  scoreEl.textContent = score;
  scoreEl.style.color = color;

  document.querySelector("#videoTitle").textContent = data.video_info.title;
  document.querySelector("#explain").textContent = meta.explain;

  // gauge
  document.querySelector("#fill").style.stroke = color;
  document.querySelector("#fill").style.strokeDasharray = score + " 100";

  // meta
  document.querySelector("#source").textContent = SOURCE[data.source] || data.source;

  const commentsMeta = document.querySelector("#commentsMeta");
  if (typeof data.comments_count_retrieved === "number") {
    document.querySelector("#comments").textContent = data.comments_count_retrieved.toLocaleString("en-US");
    commentsMeta.classList.remove("hidden");
  } else {
    commentsMeta.classList.add("hidden");
  }

  resultEl.classList.remove("hidden");
}

// Preview mode: open index.html?demo (or ?demo=neutral / ?demo=relevant) to see a sample result.
const demo = new URLSearchParams(location.search).get("demo");
if (demo !== null) {
  const v = VERDICT[demo] ? demo : "clickbait";
  displayResults({
    analyze_results: { overall_sentiment: v, clickbait_score: { clickbait: 78, neutral: 52, relevant: 21 }[v] },
    video_info: { title: "I Tried Living on $1 for 30 Days (You Won't Believe What Happened)" },
    source: "youtube_api_and_nlp",
    comments_count_retrieved: 412
  });
}
