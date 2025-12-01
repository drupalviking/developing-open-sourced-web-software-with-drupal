In Drupal, a **field** is the atomic unit of structure you attach to an entity—in your case, to a content type (which is a bundle of the `node` entity). Fields don’t just store values; they carry the semantics of those values (date, text, image, entity reference, etc.) and define how editors enter them and how readers see them. Drupal’s Field API deliberately separates a field’s _data definition_ from its _attachment_ to a particular content type, so that the same kind of data can be reused consistently across bundles while still being tailored to each editorial context.

At the data layer, a field is defined by its **field storage** configuration. Storage says, “for nodes, there exists a field called `field_event_date` of type `datetime`, with this cardinality, these indexes, and this translatability.” Storage is per entity type and shared by all bundles that use it, which is what lets you keep one coherent schema for, say, an “Image” field across multiple content types. When you attach that field to a specific content type, you create a **field instance** (often just called the field on that bundle). The instance adds bundle-specific concerns: is it required, what’s the help text, any default value, and any per-bundle settings the field type exposes. Think of storage as the column definition; the instance is the column’s role on a particular table layout.

Fields come to life through two complementary presentation layers: **widgets** and **formatters**. A **widget** is the edit-time UI: the control editors interact with on the node form. For a date field, that might be a single date picker; for entity references, an autocomplete or a select list; for media, a library browser. Widgets are chosen and arranged in the content type’s **form display**, which is a configuration map of “which widget for which field, in what order, with what widget settings.” You can even define different **form modes** (e.g., a compact “Quick Create” vs. a full “Editorial” form) so that the same fields are optimized for different authoring moments.

A **formatter** is the view-time UI: how a field’s stored value is rendered for readers. A text field might render as trimmed text with a “read more,” a date as a localized long date, an image as a responsive picture with a specific image style, an entity reference as a rendered teaser of the target entity. Formatters are chosen and arranged in the **view display**, and you can vary that choice per **view mode**—so an image might render as a small thumbnail in the Teaser mode but as a full-width responsive image on the Default node page. Each formatter carries its own settings (links on/off, trim length, image style, date format), letting you present the same underlying data in multiple, coherent ways without duplicating content.

Several other facets round out how fields behave. **Translatability** can be enabled at storage and then toggled per instance, allowing per-language values where needed. **Cardinality** controls whether a field holds a single value or a list, which affects both the widget (repeatable inputs) and the formatter (lists, galleries, carousels). **Constraints** (required, allowed file types, reference target bundles) enforce valid content at save time. Some fields are **base fields**—core properties provided by the entity type (e.g., node title, created time)—while others are **configurable fields** that you add. And because fields are first-class citizens of Drupal’s configuration system, they participate in export/import, permissions (e.g., field-level permissions with contrib), and even **third-party settings** when modules need to attach extra behavior to a field or to its displays.

Yet another fact regarding Fields is the fact that fields can be attached to different entity types! You can have a field type like "Email" and create a field on your basic page, for example to display the company's email, but you can use the same field type for the User entity, to store (and maybe display) the users email.

And here is actually a great example for field formatter. Although you would store an email in the email field as example@somewhere.com, you might want to display the employees' emails as example [at] somwhere.com. That kind of formatter most likely exists somewhere, and if not, it's easy to write by yourself.

Put together, a field in Drupal is not just a bucket for data. It is a reusable, strictly defined data type (via storage), a contextualized attachment to a content type (via the instance), and a pair of coordinated presentation strategies: **widgets for authors** and **formatters for readers**, orchestrated through form and view displays (and their modes). This design lets you model content once and then tailor the editing experience and the front-end rendering to each context where that content appears—without compromising the integrity of the underlying schema.

## Field types that ship with Drupal CMS
There are multiple field types that ship with core Drupal CMS

![[Field types in Drupal CMS.png]]*Available field types* 

These are just the field types that *ship* with Drupal CMS. There are multiple custom fields available for download, both via separate modules like YouTube Field and Video Embed fields modules, but also do many functional modules like Commerce create their own fields based on the functionality purpose the have.

Third option, if you cannot find a field that serves the need you have, you can always create one yourself! That will be covered, in detail, later in this book, under the Module development section.
## Adding a field to an entity
As we mentioned in the Content types chapter (and as the title of the section hints), everything in Drupal is an Entity. That's very much a "programmers" explanation but in a nutshell, we can think of "Entity" as a global parent of everything that's being created in Drupal. Entity is the parent of everything. That means that Content type is an entity, Taxonomy vocabularies are entities and also Blocks and Users. And by that definition we can claim that "all entities are field-able". We can add custom fields to all entities! And that's one of the biggest strengths of Drupal.

The method is always the same. In this example we are using a content type, since that's the most frequent use-cases of adding fields to entities, but generally it's the same everywhere.

If you navigate the Content type page (/admin/structure/types) you will see a list of content types. The list below is from a Drupal CMS instance with all shipped content types installed:

![[Content type listing of a newly installed Drupal site 1.png]]
*When you explore /admin/structure/types this would be the list of content types on a newly installed Drupal CMS\* site.*

Press Manage fields for the ***Basic Page*** to bring up the list of fields already in the content type.
![[Manage Fields for Basic Page.png]]
*Manage fields view for Basic Page in Drupal CMS*

Here we have two options: Create a new field or Re-use an existing field. If we have already created an email field for a content type, you should not create another field with the same purpose, you can re-use the previously built field. But I digress.

Press Create a new field to display an option of fields to add:
![[Field types in Drupal CMS.png]]
*Field types available with standard Drupal CMS install*

Let's create an Formatted text field. A contextual window with the configuration for Formatted text appears, where we give the field a name, "Excerpt" and let's choose Text (formatted, long) as the field type.

![[Add Formatted Text Field.png]]

Take notice that the "Machine name" is generated from the label, but you can change the machine name by pressing the Edit link. Normally you can leave this as is, but there are use cases where you want to change the machine name. One of it is when the label is in a non-english language, but company policy is that all machine names should be in English.

After you press continue, another configuration form appears. This form is to configure both the Field Storage part (cardinality for an example) but also all the field specific configuration. Normally you can require the field to be mandatory in all content and you can give it a default value. 

Since this is a text field, if you have languages and translations configured, you can allow the field to be "translate-able". Also you can control what text formats are allowed in the editor, if the editor is shown at all! (That's yet another configuration we'll cover later).

![[Field Settings for Excerpt.png]]
*Field settings for Text (formatted, long) field called excerpt*

When you press Save, the field is created and it's added to the entity. 

![[Excerpt Field added to the Field list.png]]

Now that we have added the field, we can arrange where it's displayed in the form (Manage Form Display) and also how it's displayed as users view the content (Manage Display). That was covered in the Content Types chapter.
