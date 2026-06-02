One of the first thing you will discover in your Drupal journey are content types. A content type stores structured data in a database, you can add fields to it, control how it displays etc. 

From an entity perspective (take a look at the chapter name), content types comes with Drupal core, so that we have a building block to build our content on.

In Drupal, a “content type” is the configuration blueprint that defines a particular kind of node—the core content **entity** that Drupal stores and renders. The entity type is always _node_; a content type is a _bundle_ of that entity type, expressed as configuration that Drupal uses to shape both the structure of the data and the editorial experience around it. Put simply: the node is the thing that holds content, while the content type is the rulebook that says what that content looks like, how it’s edited, and how it’s displayed.

Because a content type is configuration, it does not hold data itself. Instead, it declares which **fields** nodes of this kind possess (for example, a title, a body, an image, a taxonomy reference), and it determines how those fields behave. Drupal separates “field storage” (the underlying data definition shared by all bundles of an entity type) from “field instance” settings (how a given field is attached to this specific content type). This gives site builders strong control over cardinality, translatability, and data types at the storage layer, while letting them tune requirements, help text, and defaults per type.

A content type also governs the **editorial interface** through _form displays_. Here, site builders choose widgets for each field, arrange their order, and group them to create an efficient edit form. The **public presentation** is controlled separately via _view displays_ and _view modes_. The same node can therefore appear differently in different contexts—say, a concise “Teaser” on a listing page and a full “Default” rendering on the canonical page—without duplicating content. This separation of edit-time and view-time concerns is central to Drupal’s flexibility.

Beyond fields and displays, content types carry behavioral policies. They can be configured to create a new revision for every edit and to require revision log messages, which is vital for auditability in collaborative teams. If Content Moderation and Workflows are enabled, a content type participates in states like Draft, Review, and Published, adding governance to the publishing process. Language and translation settings live at both the bundle and field levels, allowing the same type to support multilingual content with per-field translation when needed.

Finally, content types intersect with access and routing. Drupal exposes per-type permissions such as creating, editing, or deleting content of that type, enabling role-based access control. Modules can attach third-party settings to the type—menu options, table-of-contents behavior, or revision pruning policies—so that broader site features can act consistently across all nodes of that type. URL patterns (often via Pathauto) are typically defined per type as well, producing predictable, human-friendly paths.

Taken together, a Drupal content type is the canonical, configuration-driven definition of a content model slice: it specifies the schema of nodes, curates the editorial workflow, orchestrates how content is displayed in varied contexts, and integrates with permissions and routing. The node entity stores the actual data; the content type ensures that data is structured, editable, and presentable in a coherent, repeatable way.

![[Content type listing of a newly installed Drupal site 1.png]]
*When you explore /admin/structure/types this could be the list of content types on a newly installed Drupal CMS\* site, but it depends on other selections as well*

## Navigating a content type
The menu to the right of the description gives you a contextual menu of what you can do to manipulate the effect of the content type. If you open up the menu you will see the following options:
![[Contextual menu of a content type.png]]

### Edit
The Edit menu gives you access to the basic components of the content type, the human-readble name, a description box for content editors to distinguish between what content types to use and then some more detailed settings, down to if to display the post information (Author and date information) or not. 

You can change the label of the Title field, decide if the node should be previewed before submitting and have submission guidelines.

It's also easy to configure if you want the content to be pubished by default or not, if it should be promoted to the front page, sticky at top of lists and if Drupal should create a new revision of the content each time you save.

You also have access to the menu settings, if you'd want this particular content to be a part of any menu or not.

### Manage Fields
As explained above, content types or bundle of a content type is composed of **fields**, that physically stores the data. Please read the following chapter on fields to get a deeper knowledge, but basically, in order to store any content as simple or complex it needs to be, we store each part of it in different fields. 

When exploring the field list of a Basic page that ships with Drupal CMS, you will see a list similar to this one:

![[Field list of Basic Page.png]]
We will cover fields in more detail later in this book (The Fields Chapter).
### Manage form display
Drupal is highly configurable, and one thing you might want to do is configure how the content editors add and/or edit their data. 

![[Manage Form display of Basic Page.png]]
*Manage form display for Basic page, as found here: /admin/structure/types/manage/page/form-display*

As you can see from this screenshot, there are many fields available, even more than the fields listed in previous screenshots. That's because some fields you can add and configure, others are **system fields** that are created for each entity type, such as the **Content type** entity.

These fields can be dragged and dropped to change the order the user will enter them, and you could even move some of them to the Disabled part, if you don't want the user to physically edit them, as the Scheduler Moderation module fields are in this example.

Whats notable here is the fact that every field has a *widget* attached to it. Widgets are the display form of each field, since every field are different. Instead of just having everything as text boxes (which would not function at all!), you can have a Text field widget for simple text fields like title, Text areas (configurable with text editors if you want) for fields like Description and Content and a Autocomplete field for something like Author. Some of the field widgets are even configurable (the cog symbol to the far right). Between the widget selector and the cog is the summary of the config for the field.

### Manage Display
In the manage display view, here we configure how the actual data is displayed to the user. Here we have (as almost always) multiple ways to configure multiple things. 
![[Manage display for Basic Page.png]]
*/admin/structure/types/manage/page/display*

First we see a list of three things: Default, Card and Teaser. These are what we call *view modes*, a configurable way to look at the content in different ways. You might want to arrange a page view differently from when you are displaying list of items (like news articles), show different fields, and maybe skip fields between displays. In this particular content type (Basic page), it's configured do use those three view modes.

But for every bundle of content types, you could configure more view modes. If you open the *Custom display settings* menu, you see that there are three more view modes available for content types:
![[Custom display settings for Basic Page.png]]
*The Custom display settings for Content type entity*

Based on your needs, you could check any of them, and then configure what fields to be displayed for that particular display. There is also a link to the *Manage view modes* page, which we will cover in more detail later.

For the **Default** view, the Layout builder* has been selected. Very briefly, the Layout builder is a drag-and-drop page-building UI for arranging content in sections with chosen layout plugins. 

But when you take a look at either Card or Teaser displays, you can see that they are arranged with fields and field formatters:
![[Card Display for Basic Page.png]]*Card display for Basic Page. Can you spot the difference between Card and Teaser layout?*

The Layout Builder is quite a new tool in Drupal, before it we did arrange the displays with fields. What is very notable here are the **Field formatters**, that configure "how" the content of the field is rendered. If we take a look at the formatter for Featured image, we can see it actually has four:
![[Field formatters for Featured image.png]]
*Field formatters for Media type **image** 

If you would choose the Entity ID formatter, instead of displaying an image in 16:9 format in medium size, you would only display the ID of the media entity itself. Not very "usable", but it shows that you could display each piece of data in different ways, based on the view point.

### Manage permissions
Drupal has a very elaborate user permission system, where you can very granularly configure who can access, edit and manipulate every single config on the page. We will go into the access control system in more detail later, but for now, we are taking a quick look on how it works for the Basic page bundle.

![[Manage permissions for Basic Page.png]]
*Manage permissions for Basic Page*

Here we see that there are three categories of permissions, one for the Content Moderation module, another for the Layout Builder and the third for the Node itself. Some of those permissions belong to the Administrator group, other also to the Content editor group, but none of them are available for Anonymous users (users that are not logged in) and Authenticated users (users that are logged in, but have very limited access on what they can do in the system).