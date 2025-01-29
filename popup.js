document.getElementById("scanEmails").addEventListener("click", () => {
    chrome.runtime.sendMessage({ action: "summarizeEmails" }, (response) => {
        const output = document.querySelector(".output");
        if (response.summary) {
            output.innerHTML = `<p>${response.summary}</p>`;
        } else {
            output.innerHTML = "<p>No summaries available.</p>";
        }
    });
});