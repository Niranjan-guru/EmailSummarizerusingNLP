(async function () {
  // Grab email content from Gmail's interface
  const emails = Array.from(document.querySelectorAll(".zA")); // Gmail-specific selectors
  const emailContents = emails.map((email) => email.innerText);

  try {
      // Send a request to the Flask backend for email summarization
      const response = await fetch("https://127.0.0.1:5000", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({ emails: emailContents }),
      });

      const { summary } = await response.json();
      
      // Send the summary to background.js for handling
      chrome.runtime.sendMessage({ action: "showSummary", summary });
  } catch (error) {
      console.error("Error while summarizing emails:", error);
      chrome.runtime.sendMessage({ action: "showSummary", summary: "Error occurred while summarizing emails." });
  }
})();
