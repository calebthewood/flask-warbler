"use strict";

console.log("Icons by Font Awesome Pro 6.2.1 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc.");
// Select the div containing message related buttons
const messages = document?.getElementById('messages');
const userProfileBtns = document?.getElementById('user-profile-btns');
const followingBtn = document?.getElementById('following-btns');

// Handle Clicks on (un)like/(un)follow buttons
if (messages) messages.addEventListener('click', handleBtns);
if (userProfileBtns) userProfileBtns.addEventListener('click', handleBtns);
if (followingBtn) followingBtn.addEventListener('click', handleBtns);


async function handleBtns(event) {
  console.log("Handle Buttons");
  if (event.target.tagName === 'BUTTON') {
    const endpoint = event.target?.getAttribute('data-endpoint');
    const { classList } = event.target;
    // Update Button's classlist
    if (classList.contains("like")) {
      event.target.classList.replace("like", "unlike");
    } else if (classList.contains("unlike")) {
      event.target.classList.replace("unlike", "like");
    } else if (classList.contains("follow")) {
      event.target.classList.replace("follow", "unfollow");
      event.target.innerHTML = icons.unfollow;
    } else if (classList.contains("unfollow")) {
      event.target.classList.replace("unfollow", "follow");
      event.target.innerHTML = icons.follow;
    } else if (classList.contains("delete")) {
      event.target.closest('li').remove()
    }
    event.target.setAttribute('data-endpoint', toggleEndpoint(endpoint));

    try {
      await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
    } catch (error) {
      console.error(error);
    }
  }
}


/** Accepts a given endpoint and returns the complementary endpoint.
 *  Works for likes and follows.
 *
 *    Likes: "/messages/42/unlike" >> "/messages/42/like"
 *
 *    Follows: "/users/stop-following/13" >> "/users/follow/13"
 */
function toggleEndpoint(endpoint) {
  const params = endpoint.split("/");
  console.log("PARAMS: ", params);
  if (params[1] === "users") {
    params[2] = params[2] == "follow" ? "stop-following" : "follow";
  } else {
    params[3] = params[3] == "like" ? "unlike" : "like";
  }
  return params.join("/");
}
