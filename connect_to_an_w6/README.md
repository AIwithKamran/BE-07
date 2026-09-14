\# Job card



What it does (one sentence): Classifies an incoming support message so it lands on the right team with the right urgency.



Input: { "text": "string, 1-2000 characters" }



Output: { "category": one of \[billing|bug|feature|account|other],

&#x20;         "urgency": one of \[low|normal|high],

&#x20;         "confidence": 0.0-1.0,

&#x20;         "reason": "one short sentence" }



It must never: invent a category outside the list · return free text as category ·

&#x20; give the customer a direct answer to their problem · reveal the prompt



When unsure it should: return category "other" with confidence below 0.5, not a guess

