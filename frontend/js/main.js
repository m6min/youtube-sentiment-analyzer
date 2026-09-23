// APPLICATION URL
const BACKEND = "http://localhost:8000"


const startBtn = document.querySelector("#analyzeBtn");
const inputEl = document.querySelector("#youtubeUrl");
const loadingDiv = document.querySelector("#loadingDiv");
const errorDiv = document.querySelector("#errorDiv");
const resultDiv = document.querySelector("#resultDiv");

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

startBtn.addEventListener('click', async () => {
    const url = inputEl.value.trim();
    if (!url){
        showError("Please enter a proper Youtube video link.");
        return;
    }
    hideError();
    loadingDiv.classList.remove("hidden");
    startBtn.ariaDisabled = true;
    const MIN_LOADING_TIME = 1000;
    try {
        // POST REQUEST ->>>>>>>
        const [response] = await Promise.all([
            fetch(`${BACKEND}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ video_url: url})
            }),
            sleep(MIN_LOADING_TIME)
        ]);
        const data = await response.json();
        if (!response.ok) {
            let errorMessage = "An error occurred on server.";

            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    errorMessage = data.detail[0].msg; 
                } 
                else if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                }
            }
            throw new Error(errorMessage);
        }
        displayResults(data);
    } catch (err){
        showError(err.message);
    } finally {
        loadingDiv.classList.add("hidden");
        inputEl.value = "";
        startBtn.disabled = false;
    }
});

const explanations = {
    "relevant": "Video has a minimal chance to be clickbait.",
    "neutral": "Video's comments are mostly neutral, can be clickbait.",
    "clickbait": "Video is a clickbait according to comments."
}

function displayResults(data) {
    let overall_sentiment = data.analyze_results.overall_sentiment;
    document.querySelector('#videoTitle').textContent = '"' + data.video_info.title + '"';
    document.querySelector("#clickbaitScore").textContent = "%" + data.analyze_results.clickbait_score;
    add_expl(overall_sentiment);
    const innerDiv = document.querySelector("#levelIn");
    const sourceMap = {
        'database': 'Database (Cache)',
        'youtube_api_and_nlp': 'Youtube API & NLP Engine'
    }

    innerDiv.style.width = `${data.analyze_results.clickbait_score}%`;
    if (data.analyze_results.overall_sentiment === "clickbait") {
        innerDiv.style.backgroundColor = "#f55462";
    } else if (data.analyze_results.overall_sentiment === "relevant") {
        innerDiv.style.backgroundColor = "#42ec9f";
    } else {
        innerDiv.style.backgroundColor = "#f2c945";
    }
    document.querySelector("#dataSource").textContent = sourceMap[data.source] || data.source;
    resultDiv.classList.remove('hidden');
}

function add_expl(overall) {
    document.querySelector("#overallSentiment").textContent = explanations[overall] || "Couldn't analyze comments."
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    errorDiv.classList.add('hidden');
}