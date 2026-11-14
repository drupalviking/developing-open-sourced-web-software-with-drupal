# Search

%% Author: this chapter comes before *Where Next?*, which becomes Chapter 23, and the patching appendix becomes Appendix C (the answers move to D). The renumbering waits until the chapter list is final (Backlog), so for now the chapter calls itself 22 and the appendix calls itself C, next to the old numbers. Screenshots aren't taken yet: each `%% Screenshot` note marks where one goes. %%

A visitor lands on the club's site with one thing in mind: "that walk by the reservoir". She doesn't know it's called *Glencorse Reservoir winter loop*, and she doesn't know whether it's under Hikes, the hike archive, or an album. She looks for a search box. Lens & Trail doesn't have one.

This chapter gives it one, and a good one. We start with what a search actually does, and why it doesn't look through every page each time someone types a word. We try Drupal's old Search module, which used to come with Drupal core, and see where it falls short. Then we build the search the club deserves with **Search API**: an index of the club's content in a database, a search page as a view, in English and Spanish, a search box on every page, and suggestions while you type. On Drupal CMS, a recipe does most of this for you, and we add *facets*, the lists of choices next to the results that let a visitor narrow them down. We look at the bigger search engines that large sites use. And last, we try something new: a search that understands what you *mean*, built with the AI tools from Chapter 19.

We start where Chapter 21 left the club's site: two languages, hikes, albums, news and pages, the views from Chapters 12 and 13, and the roles from Chapter 15.

## What a search does

Imagine finding every page about reservoirs in a printed book. You could read it from the first page to the last, which works for a leaflet and not for a book. Or you could turn to the index at the back, where someone has listed every important word, in alphabetical order, with the pages it appears on. Search engines do the second. Before anyone searches, they read every page once and write an *index*: a list of words, and for each word, the pages it's on. A search looks the words up in the index, which is fast however big the site is.

Writing a useful index takes more than listing words. A visitor who types "reservoirs" wants the page that says "reservoir". "Photo" should find "photos", "Glencorse" should find "glencorse", and "como" should find "Cómo unirse", the Spanish *How to join* page, accent or no accent. So when a search engine indexes a page, it first *processes* the text:

- It splits the text into words (*tokenizing*).
- It turns every word into lowercase, so the case doesn't matter.
- It turns letters such as "ó" or "ñ" into plain "o" and "n" (*transliteration*).
- It cuts words down to their stem: "reservoirs" and "reservoir" both become "reservoir", "walking" and "walked" become "walk" (*stemming*).

It does the same to whatever the visitor types, so both sides meet in the middle. Then it *ranks* the results: a page with the word in its title, or with the word five times, comes before a page that mentions it once in passing. The word for how well a page matches is *relevance*.

Keep those steps in mind. Every setting in this chapter is one of them.

> **Drupalism: index.** In Drupal, "index" mostly means this kind of search index, the list of words and where they are. To *index* content is to read it into such a list. You'll also see the word used for database indexes, which speed up looking things up in database tables; that's the same idea, at a lower level, and nothing you need to set up.

## Drupal's old Search module

Until Drupal 11, Drupal core came with a **Search** module. It indexes the site's content in the database during cron, and gives every site a page at `/search/node` and a search block. If you've seen a Drupal 7 or Drupal 8 site with a search box, it was probably this.

It was also old, and few people used it beyond small sites. Its index is simple, it searches all languages at once, and it can't be changed much. So the Drupal core team took it out: Drupal 11 marked it as *deprecated*, a warning that it would go, and Drupal 12 doesn't have it. It lives on as a contributed project, also called **Search**, for the sites that still use it.

We tried it on the club's site, so you don't have to. With the contributed Search project downloaded with Composer (`ddev composer require drupal/search`), the Search module and its submodule for content installed, the content indexed, and the permission **Use search** given to visitors (without it, the search page says "Access denied"), it worked. But:

- **English searches also found the Spanish pages.** The module searches every language at once, and has no setting to change that.
- **"Reservoirs" found nothing.** The module only looks up whole words as they are written. There's no stemming, unless you add a contributed module for it.
- **"Photo" missed "photos".** Same reason.
- **There's nothing to choose.** The results page is fixed: no filters for hikes only, or for the Pentland Hills, no way to say which fields matter more than others, and no say in what each result shows.

None of that is a bug. It's what a simple search was, fifteen years ago. Visitors today expect more, and Drupal has a better tool for it. We uninstalled the module, and removed it with `ddev composer remove drupal/search`.

%% Author: tested 2026-11-13 on Drupal 12.0.0-beta2 with drupal/search 1.0.0 (requires ^11.5 || ^12; the content search is the submodule `search_node`, page `/search/node`, permission `search content`). Change records: https://www.drupal.org/node/3616233 (deprecated in 11.x) and https://www.drupal.org/node/3624697 (removed from 12). Check the release and the module names before publication. %%

## Search API: the parts

**Search API** is a contributed module, and it's what nearly every Drupal site with a serious search uses. It splits a search into parts, which you can change one at a time:

- A **server** is where the index lives, and the **backend** is the kind of server: the site's own database, or a separate search engine such as Solr (more on those later in this chapter). For the club, the database will do.
- An **index** says *what* goes into the index: which content, which fields of it, and how each field is treated. One server can hold several indexes.
- **Processors** are the processing steps from "What a search does": tokenizing, lowercase, transliteration, stemming, and a few more. You switch them on for each index.
- A **view** shows the results. Search API doesn't make a search page itself: you build one with Views, as you built every list in Chapters 12 and 13, with filters, fields, sorts and a pager. That's where most of the freedom comes from.

The parts are independent. You can move an index from the database to Solr without touching the view, or build three views on one index: a search page, a search box, and a list of the newest matches.

Search API was written by Thomas Seidl (drunken monkey on drupal.org), and has been the standard for search in Drupal since Drupal 7. It works with dozens of other modules, for facets, autocomplete, spelling suggestions and every major search engine, which is why we picked it over the alternatives: there's no other module with that reach.

## Installing Search API

Download Search API with Composer, as in Chapter 11:

```
ddev composer require drupal/search_api
```

> **A note on Drupal 12.** As we write this, Search API's newest release says it supports Drupal 12, but two parts of it don't quite: its pages for managing an index show empty tables, and its **Database Search** module, the backend we need, refuses to install, because its own description file still lists Drupal 10 and 11 only. Both are fixed in Search API's development code, but not yet in a release. Until they are, the club's site uses the fixes as *patches*: small files that change a module's code in a way Composer can repeat every time it installs the module. The two patches are in the book's repository, in `examples/search/patches/`, and **Appendix C, *Patching a Contributed Module***, shows how to add them to your site, step by step. Do that first, then come back here. By the time you read this, a new release of Search API may have made the appendix unnecessary for this chapter; the appendix tells you how to check.

%% Author: Search API 1.43 (2026-11-14): the admin tables need the "initial preprocess" fix (#3552883, committed to 8.x-1.x as ece4453f after 1.43 was tagged), and `search_api_db`'s `.info.yml` needs `^12` (the `.info.yml` part of MR !371, #3630149). Drop the box when a release has both. %%

Go to **Extend**, filter on `search`, and check **Search API** and **Database Search**. Leave **Database Search Defaults** alone: it makes a ready-made server, index and view for you, which is handy, but we want to see how the parts fit together, and build them ourselves. Select **Install**.

%% Screenshot: Extend filtered on "search", with Search API and Database Search checked and Database Search Defaults not. %%

Search API's pages are under **Configuration** > **Search and metadata** > **Search API** (`/admin/config/search/search-api`). The page is empty for now, apart from two buttons: **Add server** and **Add index**. The text at the top sums up the difference between them: a server is the engine that stores the index, and an index defines what goes in it.

## A server in the database

Select **Add server**:

1. **Server name**: `Club database`.
2. Under **Backend**, keep **Database**, the only choice for now. Its description is honest: it "supports several advanced features, but should not be used for large sites". The club has a few dozen pages. A large site, in this sense, has tens of thousands.
3. Under **Configure Database backend**, keep **Minimum word length** at **1**, so that even short words like "A9" (a road) are indexed.
4. **Partial matching**: choose **Match words starting with given keywords**.
5. Keep **Phrase indexing** at **Bigram**.
6. Select **Save**.

%% Screenshot: the Add search server form, with Club database, Database, and Match words starting with given keywords. %%

**Partial matching** decides how much of a word a visitor has to type. **Match whole words only** needs the whole word, "glencorse"; **Match on parts of a word** finds "corse" inside "Glencorse" too, which also finds "horse" in "horseshoe", and makes the index slower. **Match words starting with given keywords** is in between: "glenc" finds "Glencorse", and "photo" finds "photographer". It's the one that suits suggestions while typing, which we add later in the chapter.

**Phrase indexing** is for searches in quotation marks. With **Bigram**, the database stores which words follow which, so that `"winter loop"` finds only pages where the two words come one after the other. It makes the index about five times bigger. For the club's few dozen pages, that's nothing.

## An index of the club's content

Back on the Search API page, select **Add index**:

1. **Index name**: `Club content`.
2. Under **Datasources**, check **Content**. A *datasource* is a kind of thing to index: content (nodes), taxonomy terms, users, media, and so on. The club's visitors look for hikes, albums, news and pages, which are all content.
3. A new section appears, **Configure the Content datasource**. Under **Bundles**, keep **All except those selected**, with none selected: every content type goes in. Under **Languages**, the same: both English and Spanish.
4. Under **Server**, choose **Club database**.
5. Open **Index options**. **Index items immediately** is on: when someone saves a hike, it's indexed straight away, not at the next cron run. Keep it.
6. Select **Save and add fields**.

%% Screenshot: the Add search index form, with Club content, Content checked, the Content datasource settings, and the server Club database. %%

> **Bundles and languages.** "Bundle" is Drupal's general word for a content type, a vocabulary, a media type: the kinds within an entity type (Chapter 7). "All except those selected" means new content types go into the index automatically, which is usually what you want. If the club ever adds a content type that shouldn't be found (internal notes for the committee, say), come back here and select it.

### Fields: what goes into the index

Search API doesn't guess which fields to index. You choose, and for each field, you choose what it's for. The **Fields** tab is empty; select **Add fields**. The dialog lists everything you can index, in two groups: **General**, for things that apply to any content, and **Content**, the fields of the content types.

Add these, with **Add** next to each, and **Done** at the end:

| Field | Group | Why |
|---|---|---|
| **Rendered HTML output** | General | The page as visitors see it, with all its text, for searching. |
| **Title** | Content | The title on its own, so it can count more. |
| **Content type** | Content | To let visitors look for hikes only. |
| **Area** | Content | To narrow down to the Pentland Hills. |
| **Difficulty** | Content | To find easy hikes. |
| **Date** | Content | For the hikes' dates; more on this later. |

**Rendered HTML output** asks what to render: for each content type, a *view mode* (Chapter 8), and which role to render it as. Keep **Anonymous user** as the role, so the index contains only what a visitor may see. For the view modes, choose **Default** for every content type for now; we come back to it in a moment.

%% Screenshot: the Add fields dialog, with Rendered HTML output, Title, Content type, Area, Difficulty and Date added. %%

Now set each field's **Type** in the table:

- **Rendered HTML output** and **Title**: **Fulltext**. Full text is text to search in: it's split into words, processed, and ranked.
- **Content type** and **Difficulty**: **String**. A string is a value to match exactly, "hike" or "easy", the way a filter does. It isn't split into words.
- **Area**: **Integer**, the term's ID. (A reference stores the ID of the term it points to, Chapter 10.)
- **Date**: **Date**.

Then set the **Boost** of **Title** to **5.00**. A *boost* multiplies a field's weight in the ranking: a word in the title now counts five times as much as the same word in the text. Someone who types "Turnhouse" most likely wants the hike with Turnhouse in its title, not the album that mentions it once. Select **Save changes**.

%% Screenshot: the Fields tab with the six fields, their types, and the boost 5.00 on Title. %%

You'll see two more fields in the table that you didn't add: **Published** (`status`) and **Authored by** (`uid`), in grey, without a **Remove** button. Search API's processors added them, as we see in a moment: they need them to check who may see what.

### Processors

Select the **Processors** tab. Each processor is one step from "What a search does", or a check. Turn these on:

- **Content access**: a result only shows if the visitor may see it, with the same rules as the rest of the site (Chapter 15).
- **Entity status**: unpublished content stays out of the index.
- **Highlight**: shows an *excerpt* with each result, the part of the text where the words were found, with the words in bold.
- **HTML filter**: removes the HTML tags from the rendered page, so `<strong>` isn't a word to search for.
- **Ignore case**: lowercase.
- **Tokenizer**: splitting text into words.
- **Stemmer**: cutting words down to their stem. Its description says it: "Currently, this only acts on English language content."
- **Transliteration**: "ó" becomes "o".

Below the list, **Processor order** shows the order the processors run in, at three moments: when content is indexed (**Preprocess index**), when a visitor's words are processed (**Preprocess query**), and when results come back (**Postprocess query**). The defaults are in a sensible order: transliteration and lowercase before splitting into words, stemming after. Under **Processor settings**, each processor that has settings has a tab: for **Highlight**, check that **Create excerpt** is on. Select **Save**.

%% Screenshot: the Processors tab, with the eight processors checked. %%

> **No stemming in Spanish.** The stemmer only knows English. It's built on the *Porter2* algorithm, a set of rules for English endings ("-ies" to "-y", "-ing" off), and Spanish needs rules of its own ("embalses" to "embalse", "caminatas" to "caminata"). Search API leaves the Spanish pages alone, which is the right thing to do: English rules would damage Spanish words. Thanks to **Match words starting with given keywords**, "embalse" still finds "embalses", because one starts with the other. The other way around, it doesn't. For real Spanish stemming, a search engine such as Solr (later in this chapter) has languages built in.

### Indexing

Back on the **View** tab, the index says **0%** and **0/26 indexed**: it knows about the club's 26 pieces of content, in both languages, but hasn't read them yet. New and changed content is indexed when it's saved, and the rest at cron, 50 items each run. To do it now, select **Index now**.

%% Screenshot: the index's View tab after indexing: 100%, 26/26 indexed, Server Club database. %%

> **On the command line.** Drush has Search API commands too, such as `ddev drush search-api:index`. As we write this, that one fails with Drush 14's development version ("The log level "success" does not exist"), so use **Index now**, or let cron do it.

%% Author: `drush search-api:index` fails with Drush 14.x-dev on Drupal 12.0.0-beta2 (2026-11-14). Check with a Drush 14 release. %%

## The search page

Search API has an index; now visitors need a page to search it. Go to **Structure** > **Views** > **Add view**, as in Chapter 12:

1. **View name**: `Search`.
2. **Show**: **Index Club content**. Search API's indexes are a choice of their own here, next to Content, Users and the rest.
3. Check **Create a page**. **Page title**: `Search`. **Path**: `search`.
4. **Display format**: **Unformatted list** of **fields**. **Items to display**: `10`. Check **Use a pager**.
5. Select **Save and edit**.

%% Screenshot: the Add view wizard, showing Index Club content, the page at search. %%

The view looks like Chapter 12's, with one difference: everything in it comes from the index, not from the database tables. Its fields, filters and sorts are in groups named after where they come from: **Index Club content** for the index's own fields, **Content datasource** for the fields of the content, and **Search** for the parts of the search itself.

### The search box

Under **Filter criteria**, select **Add** and choose **Search: Fulltext search**. This is the filter a visitor types words into:

1. Check **Expose this filter to visitors, to allow them to change it**.
2. **Label**: `Search for`.
3. **Filter identifier**: `keys`, the name of the search words in the address: `/search?keys=reservoir`.
4. **Parse mode**: **Multiple words**: the visitor's words are looked up one by one.
5. Under **Operator**, **Contains all of these words**: a page needs all of them to match.
6. Leave **Searched fields** empty, which means all the full-text fields.
7. Select **Apply**.

A view with no words to search for shows everything, which is a strange search page. Under **Exposed form** (in the right column, under **Advanced**), select **Basic** next to **Exposed form style**, and choose **Input required**. Now the page shows only the search box until the visitor searches. Its **Text on demand** is what shows before that; leave it empty.

%% Screenshot: the Fulltext search filter settings. %%

### Narrowing down

Add three more filters, exposed the same way: **Content datasource: Content type** (label `Type`), **Content datasource: Area** (label `Area`) and **Content datasource: Difficulty** (label `Difficulty`). A visitor who leaves them at **- Any -** searches everything. (**Allow multiple selections** would let a visitor pick *Easy* and *Moderate* at once; we kept one choice each, which is simpler on a phone.)

The last filter isn't exposed. Add **Index Club content: Item language**, and choose **Interface text language selected for page**. Without it, an English visitor gets the Spanish hikes too, as with the old Search module; with it, each visitor gets the pages in the language they're reading the site in.

### What each result shows

Under **Fields**, Views has added **Rendered HTML output**: the whole page, in each result. Remove it, and add:

1. **Content datasource: Title**, with **Link to the Content item** checked, and no label.
2. **Content datasource: Content type**, no label.
3. **Search: Excerpt**, no label: the text around the words that were found, from the **Highlight** processor.

### The order of the results

Under **Sort criteria**, add **Search: Relevance**, and choose **Sort descending**: the best match first. That's what a search should do by default.

### When nothing is found

Under **No results behavior**, add **Global: Text area**, and write `Nothing found. Try fewer or other words.` Under **Pager**, choose **Mini**: a search with eleven results doesn't need numbered pages.

Save the view, and try it at `/search`: search for `reservoirs`.

%% Screenshot: /search with "reservoirs": the Glencorse hike, with "Reservoir" in bold in the excerpt. %%

The Glencorse hike comes first, with "Reservoir" in bold in the excerpt, even though you typed "reservoirs": stemming at work. Try `photos`, which finds the albums, and `glencorse` in lowercase.

> **Try it:** search for `meeting`. Every hike comes back. Why?

### The view mode for the index

The answer is in what the index read. **Rendered HTML output** renders each hike with its **Default** view mode, and the Default view mode shows the field labels: every hike has "Meeting place" on it, so every hike matches "meeting". Labels are for people reading a page, not for an index.

The index should read a version of the hike made for searching: its text, without labels or photos. Drupal has a view mode for that, **Search index**. Go to **Structure** > **Content types** > **Hike** > **Manage display**, open **Custom display settings** at the bottom, check **Search index**, and save. A new tab, **Search index**, appears at the top. On it:

1. Keep **Description**, **Meeting place**, **Area** and **Difficulty**, and set the **Label** of each to **- Hidden -**.
2. Move **Photo**, **Hike leader**, **Date**, **Distance** and **Elevation gain** down to **Disabled**: the photo has no words, and the rest are better as filters than as text.
3. Select **Save**.

%% Screenshot: Hike's Search index display, with the labels hidden. %%

Now tell the index to use it. On the index's **Fields** tab, select **Edit** next to **Rendered HTML output**, and choose **Search index** for **Hike**. Save, and select **Index now** on the **View** tab again: changing what the index reads means reading everything again, and Search API says so, with a message that the index needs to be rebuilt.

Search for `meeting` again. Now only pages that talk about meeting come back.

> **Under the hood: rendered output.** Why index the rendered page at all, rather than the Description field? Because the rendered page has everything a visitor reads, in the right language, whatever fields a content type has: an album's photo captions, a Basic page's text, a hike's meeting place. You don't have to add every text field of every content type, and when Chapter 13's club adds a field, the index picks it up. The price is the one you saw: what's on the page, labels and all, is what gets indexed. A view mode for searching gives you the best of both.

### In Spanish

Switch the site to Spanish, at `/es/search`, and search for `embalse`: *Vuelta invernal al embalse de Glencorse* comes up, and the English hike doesn't. Try `como`, without the accent: *Cómo unirse* is found, thanks to transliteration.

The page itself needs two translations. Its address: Spanish visitors deserve `/es/buscar`. Go to **Configuration** > **Search and metadata** > **URL aliases**, select **Add alias**, and give `/search` the alias `/buscar`, with the language **Spanish**. Redirect (Chapter 17) now sends anyone who opens `/es/search` on to `/es/buscar`. And its words: translate the view, as in Chapter 18, under **Configuration** > **Region and language** > **Configuration translation**: **Views**, **Search**, **Translate**, **Spanish**. The title becomes `Buscar`, the label `Buscar`, the button `Buscar`, and the text for no results `No se encontró nada. Prueba con menos palabras u otras.`

%% Screenshot: /es/buscar with "embalse". %%

%% Author: the Spanish view title, label, button and empty text aren't translated on the test site yet (2026-11-14); do it when taking the screenshots. %%

## A search box on every page

A search page is good; a search box on every page is better. A view can have more than one display (Chapter 13), and a *block* display can show only the exposed form, the box, and send the visitor to the page for the results.

1. On the Search view, select **Add** > **Block**. Its **Block name**: `Search box`.
2. Under **Filter criteria**, select **For: This block (override)**, and remove the Type, Area and Difficulty filters from the block: the box only needs the words.
3. Under **Advanced** > **Other**, set **Link display** to **Page**: the block's form sends the visitor to `/search`.
4. Save the view.

The block shows no results of its own, only the box: the **Input required** exposed form style, which the block shares with the page, shows results only after a search, and a search from the box goes to the page.

Now place it, as in Chapter 14: **Structure** > **Block layout**, **Place block** in Olivero's **Sidebar** region, and choose **Search box** (from the Search view). Title it `Search the club`. Under **Pages**, enter `/search` and choose **Hide for the listed pages**: on the search page itself, a second box would be one too many.

%% Screenshot: the front page with the Search the club block in the sidebar. %%

Why the sidebar, and not the header, where most sites have their search box? Because of how Olivero's header works: when its main menu doesn't fit, Olivero folds it into a **Menu** button, and a search box in the header region makes it not fit much sooner. The sidebar keeps the header as it was. (*Theming Drupal* puts the box in the header, with a theme made for it.)

> **Try it:** search for `pentland` from the box on the front page. You land on `/search?keys=pentland`, with the results, and the Type, Area and Difficulty filters to narrow them down.

## Suggestions while you type: Search API Autocomplete

Most visitors know search boxes that suggest words as they type, and show the first results before they've finished. **Search API Autocomplete** adds that to any Search API view. It's a separate contributed module, by the same team as Search API.

> **On Drupal 12.** As we write this, Search API Autocomplete has no release for Drupal 12. Its maintainers have the changes it needs in a *merge request*, a proposed change waiting to be accepted, and it works on the club's site with it. Appendix C shows how to install a module like this: Composer's *lenient* plugin lets Composer install it anyway, and the merge request goes in as a patch. If you followed the appendix for Search API, the autocomplete patch is already in the same list.

%% Author: Search API Autocomplete 1.12 requires ^10.1 || ^11 (2026-11-14); MR !64 on #3634845 adds Drupal 12. Drop the box when a release supports 12. %%

```
ddev composer require drupal/search_api_autocomplete
```

Install **Search API Autocomplete** on **Extend**. The index has a new tab, **Autocomplete**, which lists the views that search this index. Select **Edit** next to **Search**:

1. Check **Enabled**.
2. Under **Suggester plugins**, check **Display live results** and **Retrieve from server**. The first shows matching pages as you type; the second suggests words from the index, such as "reservoir" when you've typed "reser".
3. Keep **Minimum length of keywords for autocompletion** at **3**: after "res", not after "r".
4. Keep **Display result count estimates** on: each suggested word shows how many pages it would find.
5. Select **Save**.

Visitors need permission to use it: under **People** > **Permissions**, give **Anonymous user** and **Authenticated user** the permission **Use autocomplete for the Search search** (the second "Search" is the view's name).

Type `res` in the search box:

%% Screenshot: the search box with "res" typed, and suggestions below it: the Glencorse hike, and "reservoir" with a count. %%

## Old hikes, and why they stay

Search for `arthur`, and both Arthur's Seat hikes come back: *Arthur's Seat by night*, in January, and *Arthur's Seat at sunrise*, which was in October. Should a past hike be found?

For the club, yes. A past hike is a description of a walk the club does again, and its album has the photos. A new member who searches for "Arthur's Seat" wants to know what it's like, not only when the next one is. And the hike archive from Chapter 13 shows past hikes on purpose.

> **Leaving out past hikes.** If your site does want only what's coming up, there's a catch: you can't leave past hikes out of the *index*. An index is written when content is saved, and it doesn't know what day it is: a hike for next Saturday is in the future when you save it, and in the past a week later, without anyone saving it again. Search API has no way to say "index only what's in the future".
>
> Do it in the view instead, which runs at the moment someone searches. Add the filter **Content datasource: Date**, with the operator **Is greater than or equal to**, **An offset from the current time…**, and the value `now`. Every search then leaves out what's already happened. It also leaves out everything without a date, which is everything but hikes, so it suits a view of hikes only: a "Search upcoming hikes" box, for example.

## On Drupal CMS: search is a recipe

Drupal CMS doesn't come with search either, but it's one click away: **Search** is one of the recommended add-ons, like the AI Assistant in Chapter 19.

1. Go to **Extend** > **Browse projects**, and select the **Recommended add-ons** tab (`/admin/modules/browse/recommended`).
2. Find **Search** ("Adds a search to help visitors find content"), and select **Install**.

%% Screenshot: the Recommended add-ons with the Search card. %%

The recipe sets up what we built by hand on core, and a little more. Under **Configuration** > **Search and metadata** > **Search API**, there's a server, **Database**, and an index, **Content** ("Can search within all content types"). The index has two datasources: content, and Canvas pages (**Page**), so the pages you build in Canvas are found too. The recipe also:

- made a **Search index** view mode for every content type, a copy of its **Default** view mode;
- installed **Search API Exclude**, which adds a checkbox to the content form to keep a single page out of the search;
- installed **Automated Cron**, so the index stays up to date even on a site without a cron job (Chapter 11);
- made a view, **Search**, with a block that shows a search box.

%% Author: drupal_cms_search 2.2.9 (2026-11-14). We applied it with `drush recipe`, not with Project Browser: the first run failed with an error, and the second applied cleanly (from snapshot `ch22-hikes` on the Drupal CMS site). Try it from Project Browser on a fresh copy of the site before publication, and check what Search API Exclude's checkbox is called, and what the ECA model `search_exclude` the recipe adds does. %%

The search index view modes are copies of **Default**, labels and all, so they have the "meeting" problem from earlier in this chapter. Fix it as on core: for **Hike** (and **Album**), open **Manage display** > **Search index**, hide the labels, and disable the photo, the hike leader, the date and the distance.

### Facets

The core site's search has filters to narrow the results: Type, Area, Difficulty, each with all its choices. *Facets* are filters that know about the results. Search for `pentland`, and a facet for Area lists only the areas that have results, with the number of results next to each. A visitor sees at once where the results are, and never picks a choice that gives nothing. Shops use them for sizes and brands; the club uses them for areas, types and difficulties.

**Facets** is a contributed module, built on Search API, with a submodule, **Facets Exposed Filters**, that turns facets into exposed filters in a view. We use it here, on Drupal CMS, because it doesn't work on Drupal 12 yet: the core site would need it rebuilt, not patched. Drupal CMS runs Drupal 11, where it does.

%% Author: Facets 3.0.7 can't run on Drupal 12: its plugin managers use annotation discovery, which Drupal 12 removed (a 500 on every page; 2026-11-14). When Facets supports Drupal 12, move this section to the core site, before "On Drupal CMS". %%

Install **Facets** and **Better Exposed Filters** from **Extend** > **Browse projects** (Project Browser downloads them; Chapter 11), then check **Facets Exposed Filters** on **Extend** and install it too. **Better Exposed Filters** gives a view's exposed filters other shapes than a drop-down list: checkboxes, links, sliders.

Facets need fields in the index to count. On the **Content** index's **Fields** tab, add **Content type**, **Area** and **Difficulty** (Content group), as on core, and select **Index now** on the **View** tab.

The recipe's Search view has only a block, which a Canvas page shows. Facets don't show when the view is a block placed with Canvas: we tried, and the facets stayed empty. So give the view a page of its own. Edit the **Search** view, select **Add** > **Page**, with the path `search`. Then, for the page:

1. Under **Filter criteria**, select **Add**, and look at the **Facets** group: every field of the index is there as a facet, such as **Area (field_area)**. Add **Area (field_area)**, **Content type (type)** and **Difficulty (field_difficulty)**.
2. For each, expose it to visitors, give it a label (`Area`, `Type`, `Difficulty`), and check **Show the amount of results**. Under **Facet settings**, check **Transform entity ID to label** for Area and Content type, so the facet shows "Pentland Hills" rather than the term's ID, and **List item label** for Difficulty, so it shows "Moderate" rather than `moderate`.
3. Add **Index Content: Item language**, set to **Interface text language selected for page**, as on core.
4. Under **Exposed form**, change **Exposed form style** to **Better Exposed Filters**. In its settings, choose **Checkboxes/Radio Buttons** for the three facets.
5. Save the view.

%% Screenshot: the facet filter's settings in Views. %%

Search for `pentland` at `/search`:

%% Screenshot: /search on Drupal CMS with "pentland": the results, and the Area, Type and Difficulty facets as checkboxes with counts. %%

Check *Easy* under Difficulty, and the results, and the counts in the other facets, change to match.

The search box goes in the header, which on Drupal CMS is a Canvas page template (Chapter 14). Open Canvas, **Templates**, **Mercury theme**, and in the **Library**, find the Search view's exposed form block; drag it into the **Navbar**'s **CTAs** slot, next to the main menu. It works in both languages: `/es/search` gives Spanish results.

%% Author: the block is `views_exposed_filter_block:search-search`, placed in the Navbar's `links` slot (labelled CTAs in Layers? check when taking the screenshot). %%

## Bigger search engines

The Database backend is a fine search for a site the size of the club's, and for much bigger ones. It has limits, though, and big sites run into them: it gets slow with tens of thousands of pages, its ranking is basic, and it knows only English stemming. That's where separate search engines come in: programs made for nothing but searching, which run next to Drupal on a server of their own, or as a service you rent. Search API talks to all the common ones, each with a module that adds a backend:

- **Apache Solr**, the oldest and the most used with Drupal, with the **Search API Solr** module. It has stemming for dozens of languages, spelling suggestions ("Did you mean *Glencorse*?"), synonyms, and fast facets. Most Drupal hosting companies offer it.
- **Elasticsearch** and **OpenSearch**, its open-source fork, with the **Elasticsearch Connector** and **Search API OpenSearch** modules: similar to Solr, popular outside Drupal, often rented as a service.
- **Typesense** and **Meilisearch**, newer and smaller, built for search-as-you-type with typos forgiven ("glencrose" still finds Glencorse), with the **Search API Typesense** and **Search API Meilisearch** modules.

Changing the backend is mostly changing the server. The index, the fields, the processors (some of which the engine does itself) and the view stay. That's the point of Search API's parts: the club could move to Solr the day it has ten thousand albums, without rebuilding its search page.

Setting one up is beyond this book: it means running another program, which is a job for a server, not for a site builder's browser. If you'd like to try, DDEV can run Solr next to your site, with an add-on (`ddev add-on get ddev/ddev-solr`).

## Search by meaning: AI search on Drupal CMS

Everything so far looks for *words*. A visitor who types "an easy walk by the water" finds pages that contain "easy", "walk" and "water" (with Contains all of these words, all three). The Glencorse hike doesn't say "water": it says "reservoir". So it isn't found, though it's exactly what she wants.

An AI search looks for *meaning*. It uses a model, like the ones in Chapter 19, to turn each piece of text into an *embedding*: a long list of numbers, 1536 of them in our case, that places the text in a kind of map of meanings. Texts about similar things end up close to each other on the map, whatever words they use: "a walk by the water" lands near "a loop around the reservoir". A search turns the visitor's words into an embedding too, and looks for the pages nearest to it. That also works across languages: "un paseo fácil junto al agua" lands in the same place as its English translation.

> **Under the hood: embeddings and vector databases.** An embedding is a *vector*, a point in a space with as many directions as it has numbers. You can't picture 1536 directions, but the idea is the same as on a map with two: points close together mean similar things. "Close" is measured by the angle between two vectors (the *cosine similarity*), and a *vector database* is a database made to find the nearest vectors quickly, among millions. Long pages are cut into *chunks* first, a few hundred words each, so that a long page about many things can be found by any of them. Making an embedding costs a little money each time: the club pays for every page indexed, and every search, at the rates of the model's provider.

The AI module from Chapter 19 has a backend for Search API that does this, **AI Search**, which keeps the index in a vector database instead of Drupal's database. The rest is Search API as you know it: a server, an index, a view.

You need three services for this, each with an account and an API key:

- **An embeddings model.** We use OpenAI's `text-embedding-3-small`, the provider the AI module calls OpenAI. Indexing the club's hikes, and a few hundred searches, cost less than one US cent when we tried it.
- **A vector database.** We use **Pinecone**, a vector database you rent as a service, because its free plan is enough for a small site, and the AI module has a provider for it. The AI module also has providers for Milvus, PostgreSQL and others you'd run yourself. If you chose amazee.ai in Chapter 19, it offers a vector database and embeddings too; we haven't tried them for this chapter.
- **A chat model,** to count the tokens in each chunk (Chapter 19). We use Anthropic's Claude Haiku, from Chapter 19.

Chapter 19 showed how to store API keys with the **Key** module, under **Configuration** > **System** > **Keys**: add an `OpenAI API key` and a `Pinecone API key` there the same way. Then set up OpenAI under **Configuration** > **AI** > **Providers**, as Chapter 19 did with Anthropic.

%% Author: tested 2026-11-14 on Drupal CMS 2.2.8 (11.4.11) with AI 1.5.2, ai_vdb_provider_pinecone 1.1.0-beta5, OpenAI embeddings and Anthropic Claude Haiku 5.5. The AI module's own AI Search submodule is marked deprecated: it's moving to a standalone project, AI Search (drupal/ai_search), which only had alpha releases (https://www.drupal.org/node/3570322). Check before publication which one to use, and rewrite the steps if the new project has different screens. amazee.ai's vector database not tried. %%

### A vector database on Pinecone

At [pinecone.io](https://www.pinecone.io), create a free account, then create an *index* (Pinecone's word for a database):

1. **Name**: `lens-and-trail`.
2. Set the **dimension** to `1536`, the length of `text-embedding-3-small`'s vectors (the two have to match), and the **metric** to **cosine**.
3. Choose a serverless index on AWS, in `us-east-1`, the region of the free plan.
4. Create it, and copy your API key from **API keys**.

%% Author: Pinecone's labels are from our notes, not checked on its current screens (2026-11-14). Screenshot of its index form, if you want outside services shown. %%

### The modules

The Pinecone provider is a contributed module. As we write this, it only has *beta* releases, so ask for one by name:

```
ddev composer require 'drupal/ai_vdb_provider_pinecone:^1.1@beta'
```

On **Extend**, install **AI Search** (Extend marks it as deprecated; see the box below) and **Pinecone Serverless VDB Provider**. Then go to **Configuration** > **AI** > **Vector Database Configuration** (`/admin/config/ai/vdb_providers`), select **Pinecone Configuration**, choose your **Pinecone API key**, and save.

> **AI Search is moving.** The AI module's **AI Search** module is being moved into a project of its own, also called AI Search, so that it can grow at its own pace. That's why **Extend** shows it as deprecated. When we wrote this, the new project had only test releases, and the one inside the AI module was the one to use. By the time you read this, check the AI Search project page on drupal.org: if it has a stable release, use that one; the steps should look much the same.

### A server and an index

Under **Configuration** > **Search and metadata** > **Search API**, select **Add server**:

1. **Server name**: `AI search`.
2. **Backend**: **AI Search** ("Index items on Vector DB").
3. **Embeddings Engine**: **OpenAI | text-embedding-3-small**.
4. **Tokenizer chat counting model**: **Anthropic - Claude Haiku 5.5**.
5. **Vector Database**: **Pinecone DB**. Then **Database Name** **lens-and-trail**, **Namespace** `content` (a part of the Pinecone index, so other indexes could share it), and **Similarity Metric** **Cosine Similarity**.
6. Under the embedding strategy, keep **Enriched Embedding Strategy** and its defaults: chunks of 500 tokens, with the title repeated in each.
7. Select **Save**.

%% Screenshot: the AI search server form. %%

Then **Add index**:

1. **Index name**: `Hikes by meaning`.
2. **Datasources**: **Content**; under its settings, **Bundles**: **Only those selected**, with **Hike**. Visitors who describe a walk want hikes, not albums.
3. **Tracker**: choose **AI Search Chunked Tracker**, *not* **Default**. This one matters, and nothing chooses it for you. The tracker keeps track of what needs indexing; AI Search indexes long pages a few chunks at a time, and only its own tracker remembers to start again from the first chunk when a hike changes. With the **Default** tracker, a changed hike is never indexed again, and its old version stays in Pinecone for good, without any error message. (We found out the hard way.)
4. **Server**: **AI search**.
5. Select **Save and add fields**.

%% Screenshot: the index form, with the Tracker choice. %%

The **Fields** tab looks different for an AI index: each field has an **Indexing option** instead of a boost. The descriptions at the top of the page explain them. Add these fields, and set their options:

| Field | Indexing option | What it does |
|---|---|---|
| **Rendered HTML output** (Hike: **Search index**) | **Main content** | The text that's cut into chunks and turned into embeddings. |
| **Title** | **Contextual content** | Added to every chunk, so each chunk knows which hike it's from. |
| **Date** | **Contextual content** | The same: the date travels with each chunk. |
| **Area**, **Difficulty**, **Language** | **Filterable attributes** | Stored next to each vector, to filter on before searching. |

Save, and **Index now**. To check what went in, the **Fields** tab has **Preview content to be vectorized**, which shows a hike as the embeddings model sees it.

### Find a hike

Now a view, as for the core site's search: **Add view**, **Show** **Index Hikes by meaning**, a page at `find-a-hike` titled `Find a hike`, showing **Rendered entity** in the **Teaser** view mode, 3 items, no pager. Then:

1. Add **Search: Fulltext search**, exposed, with the label `What kind of hike?`, the identifier `describe`, and the placeholder `an easy walk by the water`. Set its **Parse mode** to **Multiple words**. (**Direct query** sounds like the right choice for a sentence, but with AI Search it returned nothing in our tests.)
2. Set **Exposed form style** to **Input required**.
3. Add **Search: Relevance**, descending.
4. Add **Index Hikes by meaning: Language**, *not* exposed, set to `en`.

Why a fixed `en`, and not **Item language** with the interface language, as on the core site's search page? Because the AI Search backend ignores **Item language**: it passes filters to the vector database only when they're on the index's own fields, such as **Language**, which we added as a filterable attribute. So this display shows English hikes, and we make a second one for Spanish: **Add** > **Page**, with the path `buscar-excursion`, and for this page only (**This page (override)**), the **Language** filter set to `es`. Save.

Last, the menu: add a link to `/find-a-hike` called `Find a hike` in the main menu, and translate its title to `Buscar excursión` (Chapter 18). A menu link's address can't be translated, so Spanish visitors would land on `/es/find-a-hike`, the English display. Send them on with a redirect (Chapter 17): under **URL redirects**, **Add redirect**, from `find-a-hike` to `/buscar-excursion`, with the language **Spanish**.

Try it. "An easy walk by the water":

%% Screenshot: /find-a-hike with "an easy walk by the water": Glencorse Reservoir winter loop, North Berwick Law and the harbour, Arthur's Seat by night, as teasers. %%

The Glencorse loop comes first, though it never says "water", then North Berwick, by the sea. "A hard climb with sea views" gives the Pentland Hills ridge, Turnhouse Hill and Arthur's Seat at sunrise. And on `/es/buscar-excursion`, "un paseo fácil junto al agua" finds the Spanish Glencorse hike first.

The results aren't perfect: every search gives three hikes, even when none of them fits, because a search by meaning always finds *something* nearest. Arthur's Seat by night is no walk by the water. That's the trade: a search by words gives nothing rather than something wrong; a search by meaning gives its best guess. For a club with six hikes, a best guess is helpful. For a site where a wrong answer matters, combine the two, or let people check.

> **On Drupal core:** none of this is special to Drupal CMS: the AI module and its AI Search work on Drupal 11 core too. On Drupal 12, when we wrote this, the AI module wasn't available yet (Chapter 19).

### A hike guide to talk to

Chapter 19's AI Assistant answers questions about building the site. With the AI Search index, an assistant can answer questions about the *club*: "Is there an easy hike by the water before Christmas?" It searches the index for the hikes that fit, and writes an answer from what it finds, with links. This is called *retrieval-augmented generation*, or *RAG*: the model doesn't answer from what it learned in training, which knows nothing about Lens & Trail, but from what the search *retrieved* from your site.

> **A hike guide, in the admin chatbot.** We built one, with the AI module's agents (Chapter 19), in three steps:
>
> 1. An **AI agent**, under **Configuration** > **AI** > **AI Agents** (`/admin/config/ai/tools-automation/agents`): `Hike guide`, with one tool, **RAG/Vector Search**. In the tool's settings, we set **index** to *Force value* `hikes_by_meaning` and hid it from the model, so the guide can't search anything else, and **amount** to `4`. Its instructions:
>
> <!-- include: examples/search/hike-guide-instructions.txt as=Instructions -->
>
> `[current-date:html_date]` is a token (Chapter 17): the agent knows what day it is, so it can tell a hike that's coming from one that's over.
>
> 2. An **AI assistant**, under **Configuration** > **AI** > **AI Assistants** (`/admin/config/ai/ai-assistant`), using that agent, with **Anthropic**'s **Claude Haiku 5.5** as the model, and the roles **Anonymous user** and **Authenticated user** allowed.
>
> 3. The chatbot block. Here we hit a wall: on Drupal CMS, the header and footer are a Canvas page template (Chapter 14), and Canvas only offers blocks whose settings it can check fully, which the chatbot block's aren't (yet). So visitors can't get the chatbot. We tried the guide in the admin chatbot instead: edit the **Drupal Agent Chatbot** block in the Default Admin theme's block layout, and choose the hike guide as its **AI Assistant**.
>
> Asked "Is there an easy hike by the water before Christmas?", it answered with the Glencorse Reservoir winter loop on Saturday 19 December at 9:30, rated easy, meeting at Flotterstone car park, and offered North Berwick on 5 December "if you'd like the sea instead", with links to both. Asked in Spanish about a hike with sea views, it answered in Spanish, with the Spanish North Berwick page. It never made up a hike.
>
> Two more things we noticed. Drupal CMS's privacy settings (the *Klaro* consent manager) ask before the chatbot loads, because it sends what you type to an outside service: a visitor-facing chatbot needs that consent too, and a line in the privacy policy. And each question costs a few model calls, paid by the token: little for one question, real money for thousands. A chatbot on a busy public site needs a budget, and a limit.

%% Author: the hike guide was tested 2026-11-14 (agent `hike_guide`, assistant `hike_guide`, tool `ai_search:rag_search` with index forced). Labels to check when taking screenshots: the agent and assistant pages, the tool's restriction table, and the chatbot block's settings. Issue drafts for the tracker default and for the chatbot block in Canvas are in the author's `issue-drafts` folder (PROJECT-LOG Backlog); if either is fixed, update the text. %%

## Coming from WordPress?

> **Coming from WordPress?** WordPress has a search built in: every theme has a search form, and `?s=reservoir` searches posts and pages, title and text, with posts that have the words in their title first. It has no stemming, no facets, and no say in which fields count; many WordPress sites add a plugin for that, such as Relevanssi or SearchWP (which keep their own index in the database, like Search API's Database backend), or ElasticPress (Elasticsearch, like Search API with an Elasticsearch backend). Drupal's old Search module was the closest to WordPress's built-in search. Search API is closer to those plugins, with one difference: the results page is a view, which you build and change like any other list on the site.

## Summary

You can now:

- explain what a search index is, and the processing steps that make a search find "reservoir" when you type "Reservoirs";
- explain why Drupal 12 no longer has the Search module, and what it couldn't do;
- set up Search API with a Database server, an index with fields, types and boosts, and processors;
- give the index a view mode made for searching, and explain why labels don't belong in an index;
- build a search page as a view, in two languages, with exposed filters, excerpts and relevance;
- add a search box to every page with a block display, and suggestions while typing with Search API Autocomplete;
- explain why past content can't be left out of an index, and leave it out in the view instead;
- on Drupal CMS, add search with the recipe, and narrow results with facets;
- tell when a site needs a separate search engine, and name the common ones;
- explain embeddings and vector databases, and build a search by meaning with AI Search, Pinecone and Views;
- explain what RAG is, and what a chatbot on a public site needs.

## Exercises

1. Members ask to find albums by photographer. Add the photographer to the core site's index: in **Add fields**, open **Photos** (the album's photos) with **Expand**, then the media, and find **Photographer**. Which type should it be, and why? Index again, and search for a photographer's name.
2. Make the text for no results more helpful: add a link to the hike archive (`/hikes/archive`) for visitors who were looking for a hike, and translate the text into Spanish.
3. On the core site, switch to Spanish, and search for `embalse`, then for `embalses`. Explain both results with what this chapter says about stemming and partial matching. What would a Spanish visitor have to type to find the hike if the server matched whole words only?
4. *(challenge)* Make a second block for the Search view, **Search hikes only**, for the hikes page: the box searches only hikes, and the results page shows only hikes. Which filter goes where? Does it need a page display of its own?
5. *(advanced)* Visitors who search for `arthur` get both Arthur's Seat hikes, past and future, in order of relevance. Make the upcoming ones come first, without hiding the past ones. Why doesn't **Number field-based boosting** on the hike's date do it? (The answer is in Appendix C.)

%% Author: Exercise 5's answer is in `appendix-c-answers-to-the-advanced-exercises.md`. When the renumbering happens, its "(The answer is in Appendix C.)" becomes D. %%

## Want to know more?

- [Search API](https://www.drupal.org/project/search_api), whose project page links to its documentation, with a page for each processor and backend.
- [Search API Autocomplete](https://www.drupal.org/project/search_api_autocomplete), [Facets](https://www.drupal.org/project/facets) and [Better Exposed Filters](https://www.drupal.org/project/better_exposed_filters).
- The contributed [Search](https://www.drupal.org/project/search) project, Drupal's old Search module.
- Search engines: [Search API Solr](https://www.drupal.org/project/search_api_solr), [Elasticsearch Connector](https://www.drupal.org/project/elasticsearch_connector), [Search API OpenSearch](https://www.drupal.org/project/search_api_opensearch), [Search API Typesense](https://www.drupal.org/project/search_api_typesense) and [Search API Meilisearch](https://www.drupal.org/project/search_api_meilisearch).
- AI search: the [AI module](https://www.drupal.org/project/ai), the new [AI Search](https://www.drupal.org/project/ai_search) project, the [Pinecone provider](https://www.drupal.org/project/ai_vdb_provider_pinecone), and [Pinecone's own introduction to vector databases](https://www.pinecone.io/learn/vector-database/).
- For comparison, WordPress's [Search block](https://wordpress.org/documentation/article/search-block/), and the plugins [Relevanssi](https://wordpress.org/plugins/relevanssi/) and [ElasticPress](https://wordpress.org/plugins/elasticpress/).

%% Author: links checked 2026-11-14. drupal.org answers scripts with a challenge page, so the drupal.org project links were checked through packages.drupal.org (all exist); Search API's documentation pages redirected to new.drupal.org and gave 404 to our fetcher, so the text links the project page only. Check the docs links by hand. %%
