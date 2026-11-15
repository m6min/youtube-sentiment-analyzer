// APPLICATION URL
const BACKEND = "https://yt-analyzer-p56w.onrender.com";

const COLORS = { clickbait: "#FF5A5F", neutral: "#F0B23D", relevant: "#2FD08A" };

function verdictFor(score) {
  if (score >= 55) return "clickbait";
  if (score >= 35) return "neutral";
  return "relevant";
}

document.addEventListener("DOMContentLoaded", async () => {
  let clientId = localStorage.getItem("clientId");
  if (!clientId) {
    clientId = crypto.randomUUID();
    localStorage.setItem("clientId", clientId);
  }

  const list = document.querySelector("#list");
  const errorEl = document.querySelector("#error");

  try {
    const response = await fetch(`${BACKEND}/rankings`, {
      method: "GET",
      headers: { "X-Client-ID": clientId }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Couldn't fetch rankings.");
    }

    if (!data.rankings || data.rankings.length === 0) {
      list.innerHTML = `<p id="no-data">${data.message || "No analyzed videos this week yet."}</p>`;
      return;
    }

    data.rankings.forEach((video, i) => {
      const verdict = verdictFor(video.clickbait_score);
      const color = COLORS[verdict];

      const card = document.createElement("article");
      card.className = "card";

      const rank = document.createElement("div");
      rank.className = "rank mono";
      rank.textContent = String(i + 1).padStart(2, "0");

      const thumb = document.createElement("div");
      thumb.className = "thumb";
      thumb.style.backgroundImage = `url("${video.thumbnail_url}")`;
      thumb.innerHTML = `
        <span class="play">
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M8 5v14l11-7z" fill="rgba(236,238,241,0.85)"/>
          </svg>
        </span>`;

      const body = document.createElement("div");
      body.className = "card-body";

      const title = document.createElement("h2");
      title.className = "card-title";
      title.textContent = `"${video.title}"`;

      const scoreBox = document.createElement("div");
      scoreBox.className = "card-score";

      const num = document.createElement("span");
      num.className = "score-num mono";
      num.textContent = `%${Math.round(video.clickbait_score)}`;
      num.style.color = color;

      const label = document.createElement("span");
      label.className = "score-label";
      label.textContent = verdict;

      scoreBox.append(num, label);
      body.append(title, scoreBox);
      card.append(rank, thumb, body);
      list.appendChild(card);
    });
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
});
