// APPLICATION URL
const URL = "https://localhost:8000"


const startBtn = document.querySelector("#analyzeBtn");
const inputEl = document.querySelector("#youtubeUrl");
const loadingDiv = document.querySelector("#loadingDiv");
const errorDiv = document.querySelector("#errorDiv");

startBtn.addEventListener('click', async () => {
    const url = inputEl.ariaValueMax.trim();
    if (!url){
        showError("Please enter a proper Youtube video link.");
        return;
    }
    hideError();
    loadingDiv.classList.remove("hidden");
    startBtn.ariaDisabled = true;
    try {
        // POST REQUEST ->>>>>>>
        const response = await fetch(`url/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ video_url: url})
        });
        const data = await response.json();
        if (!response.ok){
            throw new Error(data.detail || "An error occurred on server.");
        }
        displayResults(data);
    } catch (err){
        showError("Connection error: " + err.message);
    } finally {
        loadingDiv.classList.add("hidden");
        startBtn.disabled = false;
    }
});