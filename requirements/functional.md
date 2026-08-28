It's a mini Stack Overflow. People post questions, other people answer them, and the community sorts out which answers are actually good.

## The user flows

**1. Accounts.** Someone signs up (or you seed users manually in the shell/admin — signup itself isn't a required endpoint, login is). They log in with username/password, get a session, and stay logged in across requests via cookie — exactly like a normal website.

**2. Asking a question.** A logged-in user writes a question — title, body, and some tags (e.g., "django", "orm"). It shows up in the public question list for anyone to browse, logged in or not.

**3. Browsing questions.** Anyone (logged in or not) can hit the question list and see: the title, who asked it, what tags it has, and how many answers it has — without the page needing to open each question individually to know that.

**4. Answering.** A logged-in user (doesn't have to be the question's author — in fact, usually isn't) writes an answer to someone else's question.

**5. Voting.** Logged-in users can upvote or downvote individual answers — signaling "this answer is good" or "this answer is wrong/unhelpful." Each user gets exactly one vote per answer (they can't spam-vote the same answer repeatedly). Voting nudges the answerer's reputation score up or down.

**6. Accepting an answer.** This is the key "authority" mechanic — **only the person who asked the original question** can mark one specific answer as "the accepted answer." This is the Q&A equivalent of the question-asker saying "yep, this solved it." If they later change their mind and accept a different answer instead, the old accepted answer gets un-accepted automatically — a question can only have one accepted answer at a time.

**7. Commenting.** Logged-in users can leave small comments directly on a question (think: "can you clarify what version you're using?") — lighter-weight than a full answer.

**8. Deleting.** People can delete their own answers or comments. Staff/admins can delete anyone's.

## The one genuinely tricky modeling problem

`Question` needs to know which `Answer` is its accepted one, but `Answer` also needs to know which `Question` it belongs to. That's a two-way relationship, and if you're not careful, you end up trying to create a table that references a row that doesn't exist yet (you can't create a `Question` pointing to an `Answer` that requires that same `Question` to already exist first). This is a real, common modeling puzzle — think about whether `accepted_answer` truly needs to be its own field, or whether `Answer.is_accepted` is actually enough on its own (that's a legitimate hint, not a spoiler of the "right" answer — there isn't one single right answer).

## The reputation system

This one's intentionally underspecified — you invent the actual scoring rule (e.g., "+10 reputation when your answer gets accepted, +2 per upvote, -1 per downvote"). The point isn't the specific numbers, it's that the *update mechanism* has to be correct — atomic, race-condition-safe, and triggered consistently (via signals) no matter how the vote/acceptance happened.

## What's deliberately out of scope

No comment-on-answers (only comment-on-questions, to keep the model from ballooning), no editing questions/answers after posting (out of scope, add it yourself if you want extra practice), no notifications, no search UI beyond the optional stretch goal, no pagination requirement (though nothing stops you from adding it).

Let me know if any specific flow still feels ambiguous — happy to narrow it down further before you start building.