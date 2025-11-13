I want to add a NeedMemoryDetector Class before prompting to LLM, if the intent is product_search, need memory = false. If the query contains ANY of the following keywords or patterns, the message is a follow-up and MUST retrieve previous context:

["what about", "how about", "and for", "and the", "the second one", 
 "the previous one", "show me again", "same as before", 
 "continue", "continue writing", "as mentioned", "as I said",
 "based on earlier", "based on above", "cheaper one", 
 "something else", "other options", "more options"]


If matched:

need_memory = true,
Product-Search Specific Follow-Up Rules

If the previous intent = product_search and the current query does NOT mention any new product name,
AND the query matches a follow-up pattern (e.g., “what about for sleep”),
then treat the message as dependent on the previous product.

Examples:

“what about for sleep”

“and for travel?”

“a cheaper one?”

“any option for kids?”

“what else?”

In this case:

need_memory = true 
and also change the intent to product_search.


The system should reconstruct a full query using the previously extracted product, e.g.:

full_query = previous_product + " " + current_query

Embedding Similarity Fallback (optional but recommended)

If none of the above rules matched, compute embedding similarity between the current query and the last 3–5 user messages.
If:

cosine_similarity(query, past_message) > 0.70


then:

need_memory = true

Otherwise:

need_memory = false


Embedding model:

text-embedding-3-small

Final Output Format

Always return:

{
  "need_memory": true/false,
  "intent": "product_search | general"
  "reason": "keyword_match | intent_override | embedding_similarity | none"
}

Examples:
what about for sleep?
Previous intent: product_search
need memory = true

If need_memory = true, return the last 2–6 messages from chat history. 
Exclude system messages. Include alternating user–assistant turns.

This sliding window provides enough context for follow-up queries such 
as: "what about for sleep?", "a cheaper one?", "and for kids?", etc.

Do NOT return the entire history. Only return the most recent coherent 
topic block (2–6 messages). This prevents token waste and maintains 
high relevance.

If need_memory = false, return no history (empty list).