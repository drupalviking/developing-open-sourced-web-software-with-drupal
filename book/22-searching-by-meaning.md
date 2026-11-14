# Search by Meaning

 Screenshot` note marks where one goes.  Author: tested 2026-11-14 on Drupal CMS 2.2.8 (11.4.11) with AI 1.5.2, ai_vdb_provider_pinecone 1.1.0-beta5, OpenAI embeddings and Anthropic Claude Haiku 5.5. The AI module's own AI Search submodule is marked deprecated: it's moving to a standalone project, AI Search (drupal/ai_search), which only had alpha releases (https://www.drupal.org/node/3570322). Check before publication which one to use, and rewrite the steps if the new project has different screens. amazee.ai's vector database not tried.  Author: Pinecone's labels are from our notes, not checked on its current screens (2026-11-14). No screenshots of Pinecone (the author, 2026-11-14).  Screenshot: the AI search server form.  Screenshot: the index form, with the Tracker choice.  Screenshot: /find-a-hike with "an easy walk by the water": Glencorse Reservoir winter loop, North Berwick Law and the harbour, Arthur's Seat by night, as teasers.  Screenshot: the agent form, with the RAG/Vector Search tool and its forced index.  Screenshot: the assistant form.  Author: the hike guide was tested 2026-11-14 (agent `hike_guide`, assistant `hike_guide`, tool `ai_search:rag_search` with index forced). Labels to check when taking screenshots: the agent and assistant pages, the tool's restriction table, and the chatbot block's settings. Issue drafts for the tracker default and for the chatbot block in Canvas are in the author's `issue-drafts` folder (PROJECT-LOG Backlog); if either is fixed, update the text, and place the chatbot in Mercury's footer.  Screenshot: the admin chatbot with the question and its answer. %%

Two more things to know before you put a chatbot in front of visitors. Drupal CMS's privacy settings (the *Klaro* consent manager) ask before the chatbot loads, because it sends what you type to an outside service: a visitor-facing chatbot needs that consent too, and a line in the privacy policy. And each question costs a few model calls, paid by the token: little for one question, real money for thousands. A chatbot on a busy public site needs a budget, and a limit.

## Summary

You can now:

- explain how a search by meaning differs from a search by words, and what embeddings and vector databases are;
- set up an embeddings provider and a vector database, and keep their keys in the Key module;
- build a Search API server and index on AI Search, with the right tracker and indexing options;
- build a search by meaning as a view, with one page per language, and explain why;
- explain what RAG is, and build an agent and an assistant that answer from the club's own content;
- name what a chatbot on a public site needs: consent, a privacy policy, and a budget.

## Exercises

1. Try *Find a hike* with searches of your own. Find one that the Chapter 22 search page answers better, and one that only *Find a hike* gets right. What do they tell you about when to use which?
2. Difficulty is a filterable attribute in the index. Add it to *Find a hike* as an exposed filter, so a visitor can ask for "a walk with views" among the easy hikes only. Remember both page displays.
3. Change the Hike guide's instructions so it always says where to meet and what to bring. Ask it the same question before and after. What else would you like it to say, or never say?
4. *(challenge)* The guide only knows the hikes. Make a second index, *Albums by meaning*, with the albums, and give the guide a second RAG/Vector Search tool for it, so it can answer "where can I see photos from the Pentlands?". What does that cost to index, compared with the hikes?
5. *(challenge)* Some questions shouldn't be answered from the club's pages at all: "Is it safe to go up Arthur's Seat in the dark?", "What will the weather be on Saturday?". Write instructions for the guide for questions like these, and test them.

## Want to know more?

- The [AI module](https://www.drupal.org/project/ai), the new [AI Search](https://www.drupal.org/project/ai_search) project, and the [Pinecone provider](https://www.drupal.org/project/ai_vdb_provider_pinecone).
- [Pinecone's own introduction to vector databases](https://www.pinecone.io/learn/vector-database/).
