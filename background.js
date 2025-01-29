chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action == "summarizeEmails") {
        chrome.scripting.executeScript(
            {
                target: {tabId: sender.tab.id},
                files: ['content.js'],
            },
            () => {
                console.log("Content script injected.");
            }
        );
    }

    // Listen for the summarized email content from content script
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (message.action === "showSummary") {
            sendResponse({ summary: message.summary });
        }
    });

    return true;  // Keep the message channel open for async response
});
