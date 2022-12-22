"use strict";

// Select the div containing message related buttons
const messageBtns = document.querySelectorAll('.message-btns');

// Handle Clicks on message buttons
messageBtns.addEventListener('click', async event => {
  const actions = ["like", "unlike","follow", "unfollow"]
  const action = event.target.getAttribute('data-message-action')
  if (actions.includes(action)) {
    const messageId = event.target.getAttribute('data-message-id');
    let resource = (action === "like" || action === "unlike") ? "messages" : "users"

    try {
      const response = await sendAjaxRequest(resource, messageId, action);
      console.log("Action Handler Response: ", response);
    } catch (error) {
      console.error(error);
    }
  }
});

async function sendAjaxRequest(resource,id,action) {
  // Use the fetch API to send an AJAX request
  const response = await fetch(`/${resource}/${id}/${action}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  return;
}