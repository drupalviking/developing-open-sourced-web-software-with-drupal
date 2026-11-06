# Appendix C: Answers to the Advanced Exercises

Most exercises in this book have more than one good answer, and you'll learn the most by trying them before you look. But the exercises marked *(advanced)* go a step further than their chapter, and we don't want to leave you stuck. Here are our answers, with the reasons behind them. If you found another way that works, it's probably fine: in Drupal, there usually is more than one.

## Chapter 13, Exercise 6: the next hike first

*Show the very next hike on its own, before the list on `/hikes`, with an attachment, and skip it in the list below with the pager's **Offset**. Now choose* Easy *in the exposed filter. What goes wrong, and why? Is there a way out, or would you choose a different design?*

### What goes wrong

The straightforward version works, until a visitor uses the filter. Add an attachment that shows one hike before the page, and set the page's **Offset** to `1`, so that it skips the hike the attachment already shows. Then choose *Easy*:

- The attachment still shows the next hike of *any* difficulty: *Turnhouse Hill and Carnethy Hill*, which is Moderate.
- The list skips its first result, which is now the first *easy* hike, *North Berwick Law and the harbour*. It's on neither the attachment nor the list.

So the page shows a moderate hike under *Easy*, and hides an easy one.

### Why

An attachment is a display of its own (see "Displays, in depth" in Chapter 13). It has its own filters, and the exposed filter we added in Chapter 12 belongs to the page only: we overrode the page's filters to add it. The attachment never sees what the visitor chose. The page's offset doesn't know anything about the attachment either: it skips the first result of *its own* list, whatever that is.

The two have to agree on what they're listing. Then the attachment's first hike and the page's skipped hike are always the same one.

### The way out

Give the attachment the same exposed filter, and let it take the visitor's choice from the page.

1. Edit the **Hikes** view, and select **Add** > **Attachment**. (Not **Duplicate as Attachment** on the page: the copy would share the page's pager, and setting its number of items would change every display that shares it.)
2. Select **Display name**, and call the display `Next hike`.
3. Under **Attachment settings**, set **Attach to** to **Page**, and **Inherit exposed filters** to **Yes**.
4. Add the filter **Difficulty (field_difficulty)** for **This attachment (override)**, and turn on **Expose this filter to visitors, to allow them to change it**, with the **Label** `Difficulty`, as you did on the page in Chapter 12. Its **Filter identifier** must be the same as the page's, `field_difficulty_value`: that's how the attachment recognizes the visitor's choice.
5. Under **Pager**, select **10 items**, set **Items to display** to `1`, and select **Apply**.

![The Next hike attachment of the Hikes view: Attach to Page, Attachment position Before, Inherit contextual filters Yes, Inherit exposed filters Yes, and the filters Published, Content type Hike, Date (>= now) and Difficulty (exposed), in italics because they're overridden](images/appendix-c-next-hike-attachment.png)
*Figure C.1: An attachment that listens to the page's exposed filter*

An attachment never shows an exposed form of its own, so visitors still see one **Difficulty** select: the page's. **Inherit exposed filters** passes its value on.

6. Select the **Page** display. Under **Pager**, select **Mini**, set **For** to **This page (override)**, keep **Paged output, mini pager**, and select **Apply (this display)**. In the pager options, set **Offset (number of items to skip)** to `1`, and select **Apply**.

![The Pager options of the Page: Items per page 10, Offset 1, Pager ID 0, and the pager link labels](images/appendix-c-offset.png)
*Figure C.2: The page skips the hike the attachment shows*

We override the pager for the page only: **Page 2** and **Page 3**, the member's hikes and the archive, share the same pager, and they shouldn't skip anything.

7. **Save** the view, and choose *Easy* on `/hikes`.

![The Upcoming hikes page with Easy chosen in the Difficulty filter: North Berwick Law and the harbour first, in the attachment, then Glencorse Reservoir loop in the list](images/appendix-c-easy.png)
*Figure C.3: The next easy hike first, then the other easy hikes*

The attachment shows the next easy hike, and the list starts with the one after it. Without a filter, the attachment shows the next hike of any difficulty, and the list the rest.

### A different design?

It works, but it's a fragile pair: two displays that must always have the same filters. If someone adds a filter to the page and forgets the attachment, the problem is back, and it doesn't show until a visitor uses that filter. Write it in the view's **Administrative comment**, under **Other**, so the next person knows.

If the club only wants the next hike to stand out, there are simpler designs:

- Show the next hike in a *different view mode*, such as Card, in a block above the page, without an offset: the next hike appears twice, once large and once in the list. Many sites do exactly that, and nobody minds.
- Leave the list alone, and make the first teaser look different with the theme (Chapter 16).

The best answer to "is there a way out?" is sometimes another question: do we need this at all? That's a good question to ask in every Views design.

## Chapter 13, Exercise 7: how many photos in each album

*Show the number of photos in each album on the albums page, below the hike's date: "Photos: 4". You'll need a relationship and aggregation. What happens to the list when you add the count, and how do you get one row per album back?*

### Counting the photos

Counting works as it did for the photographers: turn on aggregation, and count an ID. This time, the IDs are the album's photos, so we need a relationship to them first.

1. Edit the **Albums** view. Under **Other**, next to **Use aggregation**, select **No**, turn on **Aggregate**, and select **Apply**.
2. Add the relationship **Media referenced from field_photos**, and select **Apply**. Don't require it: an album without photos should still be listed, with **Photos: 0**.
3. Add the field **ID** (in **Media**). Set **Aggregation type** to **Count**, and select **Apply and continue**. In the field's dialog, set **Relationship** to **field_photos: Media**, turn on **Create a label**, type `Photos`, turn on **Place a colon after the label**, and select **Apply**.

### What goes wrong

Look at the preview:

![The preview of the Albums view with aggregation on: Pentlands, 21 November four times, each with a different photo, photographer, the same hike and date, and Photos: 1](images/appendix-c-count-duplicates.png)
*Figure C.4: Four rows for one album, each with one photo*

*Pentlands, 21 November* is back four times, as in "Too many rows" in Chapter 13, and each copy says **Photos: 1**. The count is right, in a way: each row has one photo.

### Why

With aggregation on, Views makes one row for each different combination of the *grouped* fields. **Photos**, the field that shows the album's first photo, is grouped too, and by default it groups by its own value: the ID of the photo. With the relationship, each album has four rows, one per photo, and each row has a different photo ID. So no two rows are the same, nothing is grouped, and each count is 1.

It's the warning from the end of "Counting: aggregation": a grouped field that's different in every row means no grouping at all. The difficulty here is that the field doesn't *look* different in every row: it shows "the first photo", but it groups by "this row's photo".

### The way out

Tell the **Photos** field to group by the album instead of the photo.

4. Under **Fields**, select **Aggregation settings** next to **Content: Photos**. (Once aggregation is on, every field, sort and filter has this link.)
5. Set **Group column** to **Entity ID**, and select **Apply**.

![The dialog Configure aggregation settings for field Content: Photos: Aggregation type Group results together, Group column Entity ID, and the unchecked additional group columns Bundle, Language, Entity_type, Entity ID and Target_id](images/appendix-c-group-column.png)
*Figure C.5: Group the first photo by its album, not by the photo*

**Entity ID** means the item the field belongs to: the album. All four rows of *Pentlands, 21 November* now have the same values in every grouped field, so they become one row, and the count adds up the photos. The field still shows the album's first photo, because it loads the album and shows its **Photos** as before, with **Display 1 value**.

6. **Save** the view, and open `/galleries`.

![The Albums page as a visitor sees it: Pentlands, 21 November with 4 photos and Edinburgh, 24 October with 1 photo, each with its first photo, photographer, hike and date](images/appendix-c-album-count.png)
*Figure C.6: Every album with its number of photos*

The **Albums from this hike** block on a hike's page uses the same fields, so it shows the number too.

### Is there another way?

Not in Views without aggregation: an album doesn't store its number of photos, so something has to count them. If you'd rather keep the view simple, the theme can count the values of the **Photos** field when it shows an album, in its template (Chapter 16). That moves the counting out of the view, though, and the next person who wonders where "Photos: 4" comes from will look in the view first.
