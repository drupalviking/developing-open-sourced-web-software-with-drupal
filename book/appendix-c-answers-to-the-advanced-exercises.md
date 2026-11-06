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
