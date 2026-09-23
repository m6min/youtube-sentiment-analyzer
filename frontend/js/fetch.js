const BACKEND = "http://localhost:8000"

document.addEventListener('DOMContentLoaded', async () => {
    const rankingsGrid = document.querySelector('.rankings-grid');
    const errorDiv = document.querySelector('#errorDiv');

    try {
        const response = await fetch(`${BACKEND}/rankings`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Couldn't fetched data.");
        }
        if (data.rankings.length === 0) {
            rankingsGrid.innerHTML = `<p>${data.message}</p>`;
            document.querySelector(".page-title").classList.add("hidden");
            return;
        }
        data.rankings.forEach(video => {
            const card = document.createElement('div');
            card.className = "video-card";
            card.innerHTML = `
                <img src="${video.thumbnail_url}" alt="Video Thumbnail" class="thumbnail">
                <div class="card-content">
                    <h3>${video.title}</h3>
                    <div class="score-container">
                        <p>Clickbait Score: %${video.clickbait_score}</p>
                    </div>
                </div>
            `;
            rankingsGrid.appendChild(card);
        });
    } catch (err) {
        errorDiv.textContent = err.message;
        errorDiv.classList.remove("hidden");
    }
});