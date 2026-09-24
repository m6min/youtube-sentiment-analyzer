const BACKEND = "http://localhost:8000"

document.addEventListener('DOMContentLoaded', async () => {
    let clientId = localStorage.getItem("clientId");
    if (!clientId) {
        clientId = crypto.randomUUID(); 
        localStorage.setItem("clientId", clientId);
    }
    const rankingsGrid = document.querySelector('.ranking-grid');
    const errorDiv = document.querySelector('#errorDiv');

    try {
        const response = await fetch(`${BACKEND}/rankings`, {
            method: 'GET',
            headers: {
                'X-Client-ID': clientId
            }
        });
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
            card.className = 'video-card';

            const img = document.createElement('img');
            img.className = 'thumbnail';
            img.src = video.thumbnail_url;
            img.alt = video.title;

            const content = document.createElement('div');
            content.className = 'card-content';

            const title = document.createElement('h3');
            title.textContent = '"' + video.title + '"';

            const scoreBox = document.createElement('div');
            scoreBox.className = 'score-container';

            const score = document.createElement('p');
            score.textContent = `Clickbait Score: %${video.clickbait_score}`;

            scoreBox.append(score);
            content.append(title, scoreBox);
            card.append(img, content);
            rankingsGrid.append(card);
        });
    } catch (err) {
        errorDiv.textContent = err.message;
        errorDiv.classList.remove("hidden");
    }
});