As you might imagine, a CMS system has to have an elaborate Media system in order to function properly. In order to save space we only want to have each item uploaded once and then displayed in multiple different pages.

Drupal’s Media module provides a first-class system for managing reusable assets—images, documents, audio, video, and remote media—through media entities. Instead of pasting files directly into content, you create media types (e.g., Image, Document, Remote video), give them fields and display rules, and then reference those media items from nodes, paragraphs, or blocks. This separation brings consistent metadata, permissions, revisions, and reuse across the site: the same image can appear in many places with centralized updates and usage tracking. Editors work through the Media Library, a searchable, filterable UI that supports bulk upload, selection, and embedding; CKEditor 5 integration lets them insert media inline with the right view mode. Site builders control how media renders via view modes, formatters, image styles, and responsive image mappings, while oEmbed support handles external providers like YouTube or Vimeo. Under the hood, Media ties into Drupal’s file system, access control, workflows, and caching, and it exposes structured media over JSON:API/REST for headless use—making assets consistent, discoverable, and portable across the whole site.

## Navigating the Media system
In order to see what Media types are installed on your Drupal instance, navigate to (/admin/structure/media). That will give you a list, similar to this one:

![[Media Types List.png]]
*Media types list from a fresh Drupal CMS install*

This list might seem familiar, and if you have already read the Content types chapter, it should, since this is a *list of bundles* from the *Media* entity. You can add fields to it, change how the form(s) are displayed and the different type of rendering options it has. 

Let's take a look at Image display for an example (/admin/structure/media/manage/image/display).

![[Manage display of Media part 1.png]]
*Actual list is longer, cut for demoing purposes*
![[Manage display of Media part 2.png]]
*Manage display (Default option) for Media type Image*

Yes, that's a long list! But that's one of Drupals' many amazing capabilities, to be able to configure everything in the way YOU want it to be configured.

