# A Short History of Drupal

You might not know it, but Drupal is old enough to buy alcohol in almost every country that sells it, and has been for somewhere between four and seven years! It turned 25 on 15 January 2026. And no, it wasn't a millennium bug ;-)

Twenty-five years is a very long time for software. Most of the websites, tools and companies that were around when Drupal started are long gone. Drupal has survived by changing, sometimes a little, sometimes completely, and those changes are why it looks and works the way it does today.

So why should a site builder care about history? Three reasons:

- **You'll meet old Drupal.** Many sites still run older versions, and much of what you find online, in forums, blog posts and videos, was written for them. Knowing the versions helps you tell whether advice still applies.
- **It explains the odd corners.** Why are pages called "nodes"? Why are there both Views and blocks? Why does Drupal CMS exist next to Drupal core? The answers are all in the history.
- **It tells you what to expect.** How Drupal is updated today, and why that's much less painful than it used to be, is the result of hard lessons. You'll update the Lens & Trail site many times, so it's worth knowing how that works.

In this chapter, we go through Drupal's life from a student's message board to the Drupal of today, era by era, and end with a table of every major version, and what all those version numbers mean for you. There's no hands-on work, so the Lens & Trail site stays as it is until Chapter 4, where we install Drupal.

> **Note:** This is the site builder's version of the story. The programmer's version, how Drupal's code changed and how developers keep their modules up to date, is in Appendix B, *How Drupal Is Built*.

## A message board in Antwerp (2000 and 2001)

In 2000, Dries Buytaert was a student at the University of Antwerp, in Belgium. He and his friends shared an internet connection in their student housing, and Dries wrote a small message board, in PHP, so the group could leave each other notes and share news.

He wanted to call the site *dorp.org*, after the Dutch word for "village". He mistyped it as *drop.org*, and the mistake stuck. When Dries graduated and moved out, he put drop.org on the internet, so the group could stay in touch. It soon attracted people from outside the group too, who were interested in the same things: new web technologies, and how people could work together online. They used the site to try out ideas, and the software grew with them.

On 15 January 2001, Dries released the software as open source, under the GPL, and called it **Drupal**: the English pronunciation of *druppel*, the Dutch word for "drop". That was Drupal 1.0.

> **Drupalism:** The Drupal logo is a drop of water with a face, called the *Druplicon*. Now you know why it's a drop.

Early Drupal wasn't meant to be a content management system. It was a tool for a community to share and discuss things, and an experiment. The content management came from the people who used it, and needed it to do more.

> **Coming from WordPress?** WordPress came two years later, in 2003, when Matt Mullenweg and Mike Little forked an older blogging tool, b2/cafelog. The two grew up side by side, from different roots: WordPress from a blog, Drupal from a community site. That still shows today. WordPress is at its best publishing posts and pages; Drupal is at its best with many kinds of structured content, many editors, and complex permissions. It's never a contest: they're good at different things.

## Growing into a CMS (2001 to 2006)

Once Drupal was open source, other people started adding to it. In its first years, Drupal got the building blocks it still has today: **modules** that add features, **themes** that change the look, and **users** with **roles** and **permissions**. From very early on, Drupal was built so that a module could change how Drupal behaves without anyone changing Drupal itself. That idea, extending Drupal from the outside, is the reason there are tens of thousands of modules today.

Releases came every year or so: 2.0 and 3.0 in 2001, then a long series of 4.x versions, from 4.0 (2002) to 4.7 (2006).

Two of the most important things in Drupal's history happened outside Drupal core, in contributed modules:

- **CCK**, the Content Construction Kit, let site builders create their own kinds of content, with their own fields: an event with a date and a place, a product with a price. Before CCK, adding a field meant writing code.
- **Views** let site builders make lists of content, such as "the ten newest events, with their dates", by clicking instead of writing database queries.

Together, CCK and Views turned Drupal from a tool for programmers into a tool for site builders. Both are now part of Drupal core, as you'll see in Chapter 7 (content types and fields) and Chapter 12 (Views).

Drupal 4.7, released in May 2006, is often called the release where Drupal grew up. It made Drupal fit for big, complex sites, and it was the first version that CCK and Views worked with. (For developers, it was also the release that brought the Form API, which Appendix B describes.)

The community was growing too. The first **DrupalCon**, the Drupal conference, was held in Antwerp in 2005. Today there are DrupalCons in North America and Europe every year, and Drupal Camps, smaller local events, all over the world.

## Drupal 5 and 6: growing up (2007 to 2010)

**Drupal 5** came out on Drupal's sixth birthday, 15 January 2007. For site builders, it brought:

- an **installer** you could run in the browser, instead of setting up the database by hand;
- **jQuery**, a JavaScript library that made the interface more interactive;
- *installation profiles*, ready-made setups for a particular kind of site, the great-grandparents of today's recipes;
- a reorganized administration section, and a new default theme, Garland, which a whole generation of Drupal sites looked like.

**Drupal 6** followed in February 2008. It rebuilt the menu system, and made multilingual sites possible in core, with support for right-to-left languages, such as Arabic and Hebrew. It also brought the **Update status** module (today's Update Manager), which checks whether your site needs updates, and tells you about security releases. We use it in Chapter 20.

Around Drupal, an ecosystem was forming. The **Drupal Association**, a non-profit, was founded in 2006 to look after drupal.org and to support DrupalCon. In 2007, Dries co-founded **Acquia**, a company that offers Drupal hosting and services. It was one of the first companies built around Drupal, and today there are thousands of them, from one-person agencies to companies with hundreds of employees. (Chapter 2 tells you more about who's who.)

Drupal also became famous. In October 2009, **whitehouse.gov** moved to Drupal 6. For many governments, universities and large organizations, that was the moment Drupal became a serious choice, and many followed: if it's good enough for the White House, it's good enough for us.

## Drupal 7: fields everywhere (2011)

**Drupal 7** took almost three years to make, and was released on 5 January 2011. It was a big step for site builders:

- **Fields moved into core.** What CCK did as a contributed module became part of Drupal itself, and not only for content: users and taxonomy terms could have fields too. Behind that was a new idea, the *entity*, a general name for any piece of data Drupal manages. Entities are the subject of Chapter 7, and they're the reason Drupal is as flexible as it is.
- **Images in core.** Image fields, and *image styles*, which resize and crop images automatically for every place they're shown. Chapter 9 covers them.
- **A new look.** Two new themes, Bartik for the site and Seven for the administration pages, a toolbar along the top of the screen, and shortcuts.

Views stayed a contributed module, and Drupal 7 sites came to depend on a set of contributed modules almost every site used: Views, Pathauto, Token, Features, Rules, Panels, and more.

Drupal 7 was a huge success, and it lived for an incredibly long time: its support ended on **5 January 2025**, fourteen years after its release. Many Drupal 7 sites are still online today, unsupported, and you may be asked to help move one to a modern Drupal. You'll also find a lot of Drupal 7 advice online, so check which version a blog post or video is about before you follow it.

There was one thing nobody liked about Drupal, up to and including Drupal 7: **upgrading to a new major version meant rebuilding the site.** Every major version changed so much that themes had to be rewritten, modules had to be ported, and content had to be moved over. Site owners dreaded it, and many sites stayed on old versions for years. That problem shaped what came next.

## The big rewrite: Drupal 8 (2015)

By the early 2010s, Drupal had a decision to make. The web had changed: phones, web services, a modern PHP. Drupal's code was showing its age, and it was written in its own, Drupal-only style, which made it hard for programmers from elsewhere to join in.

So the community decided to rebuild Drupal on modern foundations, and to "get off the island": instead of writing everything itself, Drupal would use well-known open source code from the wider PHP world. Its new motto was *Proudly Found Elsewhere*. The biggest of those borrowed foundations is **Symfony**, a PHP framework (Appendix B describes it). And the plan was that this would be the *last* big rewrite: once Drupal stood on these foundations, it should never have to start over again.

It took almost five years. **Drupal 8** was released on **19 November 2015**, Dries's birthday. For site builders, it brought a lot:

- **Views in core**, and many administration pages rebuilt as views, so you can change them.
- **A text editor in core** (CKEditor), so editors no longer need to write HTML.
- **Multilingual everything**: the interface, the content, and the configuration, in four core modules. Chapter 18 uses them.
- **Configuration management**: the site's settings can be exported to files, and moved from one copy of the site to another, such as from your computer to the live server. Chapter 21 shows how.
- A **mobile-friendly** administration interface, and **Twig**, a new template language for themes (Chapter 16).

And a new way of releasing. Drupal 8 introduced **semantic versioning**, with three-part version numbers such as 8.5.3, and a new *minor* release every six months. Minor releases may add features, but they must not break anything. So Drupal 8 kept growing for five years after its release: content moderation, media handling, the Media Library, and Layout Builder (Chapter 6) all arrived as minor releases.

The rewrite came at a cost, and it's fair to say so. Drupal 8 was much harder to learn, especially for programmers used to the old style, and many contributed modules took years to be ported. Upgrading a Drupal 7 site to Drupal 8 wasn't an upgrade at all: it was a new site, with the content *migrated* over, and for many site owners it was the most expensive rebuild yet. Some people disagreed with the whole direction strongly enough to fork Drupal 7, in 2013, as **Backdrop CMS**, which is still around. That's open source working as it should: when people disagree, they can take the code and go their own way.

%% Author: your own memories here? Which version did you start on, and what was the move from 7 to 8 like for you, or your clients? %%

## Easy upgrades: Drupal 9, 10 and 11 (2020 to 2024)

So, did the plan work? Was Drupal 8 really the last rewrite?

It was. **Drupal 9**, released on 3 June 2020, was the first major release after the "no more big rewrites" rewrite. Dries had promised that "the big deal about Drupal 9 is that… it should not be a big deal", and he was right. Drupal 9.0 was the same as the last Drupal 8 at the time, 8.9, with one difference: old code that had been marked for removal was removed. Drupal 9 wasn't an upgrade. It was a clean-up!

### Deprecation, explained with roads

How does Drupal change without breaking things? With *deprecation*. Think of a town that builds a new road to replace an old one. It doesn't close the old road the day the new one opens. It puts up a sign: "This road closes next year. Please use the new road." Everyone has a year to change their route, and nobody is stranded.

Drupal does the same with its code. When a better way of doing something is added, the old way keeps working, but it's marked **deprecated**: "this will be removed in the next major version, please use the new way". During the minor releases, nothing breaks. Then, in the next major version, the deprecated code is removed, the old roads are closed, and everything that still used them has to be updated first.

For you as a site builder, this means:

- **Minor updates** (from 11.3 to 11.4, say) are safe, and you should do them. They add features, and fix bugs, without breaking things.
- **Major updates** (from 10 to 11, say) are no longer rebuilds. Your site, its content and its configuration stay as they are. What you need is for your contributed modules and themes to be ready for the new version, and in most cases, they are long before you need them. A module called **Upgrade Status** tells you which of yours aren't. We come back to that in Chapter 20.

The programmers' side of this, and the tools that update modules automatically, are in Appendix B.

### What came in 9, 10 and 11

Each major version since has followed the same pattern: new features in the minor releases, and a clean-up, plus newer versions of the foundations underneath, in the major ones.

- **Drupal 9** (June 2020) ran on newer versions of Symfony and Twig, and was otherwise Drupal 8.9 without the deprecated code. Its minor releases brought a new administration theme, Claro, and a new site theme, Olivero, and **CKEditor 5**.
- **Drupal 10** (15 December 2022) made Claro and Olivero the defaults, made CKEditor 5 the only editor, and brought a tool for starting your own theme. Its minor releases brought an easier way to add fields (Drupal 10.2), and **recipes** (Drupal 10.3, 2024), ready-made bundles of modules and configuration you apply to a site, which Chapter 11 explains.
- **Drupal 11** (2 August 2024) ran on Symfony 7 and PHP 8.3, and dropped a few old modules from core, such as Forum, which live on as contributed modules. Its minor releases brought a lot:
  - **11.1** (December 2024): recipes that ask questions when you apply them (an API key for a remote service, say), and new content types that no longer get a Body field automatically.
  - **11.2** (June 2025): much faster installation of modules and recipes, and support for the AVIF image format.
  - **11.3** (December 2025): the biggest performance boost in a decade (the same server handles 26 to 33% more requests), the new **Navigation** menu down the side of the screen, links to your own content picked from a list in the text editor, and a separate permission for publishing and unpublishing content.
  - **11.4** (July 2026): **Default Admin**, the new administration theme based on Gin, with a dark mode, which you'll use throughout this book; a leaner Standard installation, without the Article and Page content types; an overview of all of a content type's display modes; a full-screen mode in the text editor; and recipes that apply twice as fast.
  - **11.5** (December 2026), released together with Drupal 12, is a *long-term support* release: Drupal 11 will be supported until {{ number:drupal11_supported_until }}.

The key shift of these years is the one Drupal 8 was built for: continuous improvement, instead of a disruptive rebuild every few years.

## Starshot and Drupal CMS (2024 to 2026)

There was still one big problem. Drupal could do almost anything, but getting started with it was hard. A new user installed Drupal, got an almost empty site, and had to know which of thousands of modules to add, and how to set them up, before they had a useful website. Meanwhile, products like WordPress and commercial site builders got people from nothing to a nice site in minutes.

At DrupalCon Portland, in May 2024, Dries announced **Starshot**: a new product, built on Drupal core, that should be ready to use the moment it's installed, for people who aren't Drupal experts, such as marketers and content editors. Starshot was the project's code name; the product got its own name, **Drupal CMS** (the Starshot name had to go, for legal reasons).

- **Drupal CMS 1.0** was released on 15 January 2025, Drupal's 24th birthday. It's Drupal core with a carefully chosen set of contributed modules, put together with recipes, and set up with sensible defaults: an SEO setup, a blog, events, forms, a search, and optional AI tools. It also brought Project Browser, which lets you find and install modules from inside the site.
- **Drupal CMS 2.0** followed on 28 January 2026, with **Drupal Canvas**, a visual page builder where you drag and drop components onto a page, as the default way to build pages, and the first *site templates*, complete starting points for a particular kind of site.

As I write this, the newest version of Drupal CMS is {{ number:drupal_cms_version }}. So today there are two ways to start: Drupal core, and Drupal CMS on top of it. Chapter 1 explains the difference, and this book shows both, in its "On Drupal CMS" boxes. Drupal CMS changes quickly: expect new versions, new site templates, and new features in Canvas more often than in core.

## Drupal 12, and what's next

**Drupal 12** is planned for the week of 7 December 2026, together with **Drupal 11.5**. As with Drupal 9, 10 and 11, the major release is mostly a clean-up: for a site builder, 11.5 and 12 are the same. That's why this book is written for Drupal 12, but works with 11.5 too. Default Admin, experimental in 11.4, is stable in both.

Drupal 10 reaches its end of life in the same week, on 9 December 2026: from then on, it gets no more security updates. If you have a Drupal 10 site, it's time to move it to 11 or 12. (With Upgrade Status, and the deprecation process, that's an afternoon's work for most sites, not a rebuild.)

What comes after is decided in public, like everything else in Drupal: in the issue queues on drupal.org, in the strategic initiatives, and in Dries's keynote at every DrupalCon, called the **Driesnote**, where the plans for the coming year are presented. If you want to know where Drupal is going, the most recent Driesnote is the place to start.

## Every major version, at a glance

The support dates were checked on {{ number:checked }}; drupal.org has the current ones.

| Version | Released | Supported until | What it meant for site builders |
|---|---|---|---|
| 1.0 to 4.6 | 2001 to 2005 | | Modules, themes, users, roles and permissions. CCK and Views start as contributed modules. |
| 4.7 | May 2006 | February 2008 | Drupal grows up, for big and complex sites. |
| 5 | 15 January 2007 | January 2011 | The installer, jQuery, installation profiles, the Garland theme. |
| 6 | 13 February 2008 | 24 February 2016 | Multilingual in core, a new menu system, Update status. whitehouse.gov (2009). |
| 7 | 5 January 2011 | 5 January 2025 | Fields and entities in core, image styles, the Seven and Bartik themes. The longest-lived Drupal. |
| 8 | 19 November 2015 | 2 November 2021 | The big rewrite, on Symfony. Views, CKEditor, configuration management and multilingual in core. A new minor release every six months. |
| 9 | 3 June 2020 | 1 November 2023 | The first easy upgrade: Drupal 8 without the deprecated code. Claro, Olivero, CKEditor 5. |
| 10 | 15 December 2022 | {{ number:drupal10_supported_until }} | Claro, Olivero and CKEditor 5 by default. Recipes (10.3). |
| 11 | 2 August 2024 | {{ number:drupal11_supported_until }} | Much faster (11.2, 11.3). Recipes that ask questions, the Navigation side menu, links to your own content in the editor. Default Admin and a leaner Standard installation (11.4). 11.5 is a long-term support release. |
| 12 | {{ number:drupal12_released }} | {{ number:drupal12_supported_until }} | Drupal 11.5 without the deprecated code. |

And on top of core: **Drupal CMS 1.0** (15 January 2025) and **Drupal CMS 2.0** (28 January 2026).

## What all those numbers mean for you

You'll see version numbers everywhere: on your site's status report, on every module's page on drupal.org, and in the commands you type. Here's how to read them.

**Drupal core** uses three numbers, *major.minor.patch*. As I write this, the newest stable version is **{{ number:drupal_version }}**. Take 11.4.11 as an example:

- The **major** version (11) changes every two years or so, and removes deprecated code.
- The **minor** version (4) changes every six months, and adds features without breaking anything.
- The **patch** version (the last 11) changes whenever bugs or security problems are fixed, often several times a month. Patch updates are the ones you must never put off, because security fixes come as patch releases.

**Contributed modules and themes** use the same idea, with their own numbers, which have nothing to do with core's. A module's version **2.1.3** says nothing about which Drupal it works with; its project page on drupal.org tells you that, such as "Works with Drupal: ^10.3 || ^11". (The `^` means "this version, or any later version with the same major number".)

You'll also meet older module versions written like **8.x-1.5** or **7.x-3.2**. That's the old style, from before 2020, where the first part said which Drupal core the module was for. Many modules still have a few of those releases on their pages. A module in the 7.x style is for Drupal 7, and won't work on a modern site.

> **Note:** Each Drupal version is supported for a limited time, and the dates are on drupal.org, on the page *Drupal core release cycle: major, minor, and patch releases*. When a version reaches its end of life, it gets no more security updates, and a site on it should be updated. We look at keeping a site up to date in Chapter 20.

## Summary

In this chapter, you learned:

- that Drupal started in 2000 as a student's message board in Antwerp, became open source on 15 January 2001, and is named after the Dutch word for "drop";
- that the features site builders use most, content types with fields, and Views, started as contributed modules (CCK and Views), and moved into core in Drupal 7 and 8;
- why upgrading to a new major version used to mean rebuilding the site, and why Drupal 8 was rebuilt on Symfony so it would never have to happen again;
- how deprecation lets Drupal improve without breaking things, which is why minor updates are safe, and major updates are no longer rebuilds;
- that Drupal CMS, which started as Starshot in 2024, is Drupal core with a ready-made setup on top, and that Drupal CMS 2.0 brought Drupal Canvas;
- how to read the version numbers of Drupal core and of contributed modules.

## Exercises

1. Go to Drupal core's project page on drupal.org, <https://www.drupal.org/project/drupal>. What's the newest version of Drupal? Which versions are supported, and until when?
2. Find the project page of the **Pathauto** module on drupal.org. Which versions of Pathauto are there, and which Drupal versions does each one work with? Is there an old-style version number (such as 7.x-1.x) on the page?
3. Watch the most recent Driesnote (search for "Driesnote" on YouTube, or on dri.es). Write down three things it announces, and which of them a site builder would notice.
4. Search the web for a question about Drupal, such as "how to add a field to a content type in Drupal". Look at the first five answers: which Drupal version is each one written for, and how can you tell?
5. *(challenge)* Read the release notes of the newest Drupal minor release (on drupal.org, under Drupal core's releases). Make two lists: the changes a site builder would notice, and the changes only a developer would. Which list is longer, and why do you think that is?

## Want to know more?

- *The history of Drupal*, on drupal.org: <https://www.drupal.org/about/history>
- *Drupal core release cycle*, the support dates for every version: <https://www.drupal.org/about/core/policies/core-release-cycles/schedule>
- *Drupal 7 end of life*, and what it means for Drupal 7 sites: <https://www.drupal.org/about/drupal-7/d7eol>
- Dries Buytaert's blog, where many of the decisions in this chapter were first explained: <https://dri.es>
- *Drupal CMS*, the product page: <https://new.drupal.org/drupal-cms>
- *Backdrop CMS*, the fork of Drupal 7: <https://backdropcms.org>
