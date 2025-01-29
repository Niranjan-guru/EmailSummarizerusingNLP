// document.getElementById("scanEmails").addEventListener("click", () => {
//     chrome.runtime.sendMessage({ action: "summarizeEmails" }, (response) => {
//         const output = document.querySelector(".output");
//         if (response.summary) {
//             output.innerHTML = `<p>${response.summary}</p>`;
//         } else {
//             output.innerHTML = "<p>No summaries available.</p>";
//         }
//     });
// });

document.getElementById("scanEmails").addEventListener("click", () => {
    // Open the Flask page for Google OAuth & Email Summary
    chrome.tabs.create({ url: "https://127.0.0.1:5000/summarize_emails" });
});
