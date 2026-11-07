# Preface

Welcome to *Developing Open Sourced Web Software with Drupal*. This is a book for people who have never seen Drupal before, and who want to learn how to build a real website with it. Not a toy website, but the kind of site an organization actually runs: with different kinds of content, people who log in and edit, lists that update themselves, images in all sizes, and more than one language.

The book is also open source, meaning that you can freely download, reuse, modify and redistribute any part of it as you like, under the terms of the Creative Commons Attribution-ShareAlike 4.0 International license (CC BY-SA 4.0). Why write a book on open source if we don't do it open-sourcingly! ;-) If you find a mistake, or think something could be explained better, you're very welcome to help. More on that at the end of this preface.

## Who is this book for?

I've written this book with three kinds of readers in mind.

- **Students** in universities and colleges, taking a course on web development or content management. The book follows a semester well: one chapter a week, with exercises at the end of each one.
- **Participants in a Drupal in a Day workshop**, held at DrupalCons, Drupal Camps, and other events. A workshop day covers a lot of ground quickly. This book is the place to read about it all again, more slowly and in more depth. The workshop covers roughly Chapters 4 to 20, without Chapter 13, which goes deeper into Views than a day allows.
- **The curious**, who want to learn Drupal on their own, at their own pace. Read the book from the start, and do the exercises. That's how it sticks.

You don't need to know how to program. You don't need to know PHP, the language Drupal is written in, and you won't write any code in this book. You do need to be comfortable with a computer, and not afraid of typing a few commands into a terminal (the text window where you type commands to your computer). We install Drupal on your own computer in Chapter 4, and I show you every command you need, and what it does.

If you already know Drupal and want to write your own modules, this book is a good refresher, but the book you're looking for is its companion, *Drupal Module Development for Drupal 11 and 12*, which picks up where this one ends.

## What this book covers

We start with the big picture, and then build a site, one piece at a time.

- **Chapter 1, What Is a CMS, and What Is Drupal?**, explains what a content management system is, gives you a map of Drupal's building blocks, and introduces the website we build throughout the book.
- **Chapter 2, Open Source and the Drupal Community**, explains what open source means, why it matters, and who the people behind Drupal are.
- **Chapter 3, A Short History of Drupal**, tells the story from a student's message board at the University of Antwerp to the Drupal of today.
- **Chapter 4, Installing Drupal**, gets Drupal, and Drupal CMS, running on your own computer.
- **Chapter 5, Finding Your Way Around**, is a tour of the administration interface.
- **Chapter 6, Your First Page**, creates content: the club's first pages, their revisions, and drafts that someone checks before they go online.
- **Chapter 7, Everything Is an Entity**, explains how Drupal structures its data, with content types and fields.
- **Chapter 8, Laying Out Pages**, decides how content looks: field displays, and the two ways of laying out a page, Layout Builder and Drupal Canvas.
- **Chapter 9, Media and Image Styles**, handles photos, videos, and documents, and how Drupal resizes images for you.
- **Chapter 10, Taxonomy**, classifies content with categories and tags.
- **Chapter 11, Extending Drupal**, adds features with modules and recipes, and introduces Composer, the tool that manages them.
- **Chapter 12, Views: Lists of Content**, builds lists of content, such as upcoming hikes or the newest photos.
- **Chapter 13, Going Deeper with Views**, adds tables of fields, relationships between content, and lists that change with the page they're on. You can skip it on a first reading.
- **Chapter 14, Blocks, Regions, and Menus**, places things on the page, and builds the site's navigation.
- **Chapter 15, Users, Roles, and Permissions**, decides who can do what.
- **Chapter 16, Appearance**, changes the look of the site with themes.
- **Chapter 17, Nice URLs and SEO**, gives pages readable addresses, and helps search engines find them.
- **Chapter 18, Multilingual Sites**, translates the site, its content, and its interface.
- **Chapter 19, AI in Drupal CMS**, looks at what AI tools can, and can't, do for a site builder.
- **Chapter 20, Keeping Your Site Safe**, covers updates, security advisories, and backups.
- **Chapter 21, Configuration and Going Live**, moves your settings from one copy of the site to another, and goes through what to check when the site goes live on a real server.
- **Chapter 22, Where Next?**, shows how to get involved in the community, and where to go from here.

There are two appendices. **Appendix A, Development Tools**, explains the tools we use to run Drupal on our own computers (Docker, DDEV, Lando, editors, Git). **Appendix B, How Drupal Is Built**, looks under the hood, at the software Drupal is built from, for those who are curious.

## The site we build

Throughout the book, we build one website: the site of **Lens & Trail**, a small photography and hiking club in Edinburgh, Scotland. The club goes on hikes, takes photos along the way, and shows the best of them on its website. It has members, a news page, a calendar of upcoming hikes, and galleries. Many of its members speak Spanish, so the site is in English and Spanish.

Every chapter adds something to the site, and starts where the previous chapter left off. By the end of the book you will have built a complete site, and you'll know how every part of it works. Chapter 1 describes the site in more detail.

## Drupal and Drupal CMS

There are two ways to start with Drupal today. **Drupal core** is Drupal itself: the software that everything else is built on. **Drupal CMS** is a ready-made product built on top of Drupal core, with a selection of extra features already set up. Chapter 1 explains the difference in more detail.

This book builds the Lens & Trail site on Drupal core. Drupal CMS is amazing, and it gets you further, faster. But I strongly believe that you should understand how Drupal works, before you let a product hide the details from you. So we build on core, and wherever Drupal CMS does something differently, we show that too, in a box like this one:

> **On Drupal CMS:** This is where you'll read how Drupal CMS does the same thing, or what it has already done for you.

This book was written for **Drupal 12** and **Drupal CMS 2**. Drupal 12 was released together with Drupal 11.5, and for a site builder the two are the same: what Drupal 12 changes is mostly under the hood, where it drops old code that had been marked for removal. So if your site runs Drupal 11.5, you can follow along too. Drupal changes quickly, especially Drupal CMS, so some screens may look a little different on your computer. The ideas behind them change much more slowly.

## How to read this book

Each chapter opens with what it covers, and why it matters for our club site. Then we get our hands dirty. You'll see these along the way:

> **Try it:** Steps to do on your own Lens & Trail site. Don't skip them: you'll need the result in later chapters.

> **Note:** Something worth knowing, but not needed right now.

> **Drupalism:** A term that means something different in Drupal than you might expect, or that means different things in different corners of the Drupal world. Everyone gets tripped up by these, so we point them out where you first meet them.

Every chapter ends with a **summary** of what you've learned, a set of **exercises**, and **Want to know more?**, a list of places to read further. The exercises go from repeating what the chapter showed on new data, to small open tasks on the club site. The harder ones are marked *(challenge)*. If you're using the book in a course, the exercises make good assignments.

## Conventions used

- Text you see on the screen, such as the names of buttons, links, and fields, is in **bold**: click **Save**.
- Paths in the admin interface are written like this: **Structure** > **Content types**. The address of a page on your site is written like this: `/admin/structure/types`. Add it to your site's address in the browser, such as `https://lens-and-trail.ddev.site/admin/structure/types`.
- Commands you type in the terminal, and the contents of files, are in blocks like this one:

  ```bash
  ddev launch
  ```

- New terms are in *italics* the first time they appear, with an explanation right away.

## For teachers

A teachers' kit is being written alongside the book, with slides and teaching notes for each chapter: how long it takes, what to show live, and what to leave for the exercises. It works for a Drupal in a Day workshop and for a university course. You'll find it in the `slides/` folder of the book's repository.

## How this book was made

%% For the author: a first version of the backlog item "How this book was written, and how it's kept up to date" (2026-11-05), because Chapter 19 points here. The part about covering two versions at once, and moving to one around Drupal 12.1, is still to come. Please check that it describes how you work. %%

We say it openly, because Chapter 19 asks you to be honest about AI on your own site: an AI assistant, Claude, helps with this book, mostly with keeping it up to date. The layout of the book, its structure and its text were decided by people first. The AI's work is the part that's dull for people and quick for a machine: checking every step against a running Drupal site, retaking the screenshots when Drupal's screens change, checking facts and links against drupal.org, and keeping version numbers and support dates current. A person reviews everything before it goes in.

The book is built so that this is possible. Screenshots are taken by a script from two test sites, version numbers and dates come from one file, and the files you see in the book come from the `examples/` folder. When Drupal changes, we replace the parts that changed, without rewriting the book around them.

## Help make this book better

This book lives in a public Git repository: <https://github.com/drupalviking/developing-open-sourced-web-software-with-drupal>. If you find a mistake, a screen that has changed, or an explanation that didn't work for you, please open an issue there, or, even better, send a pull request with the fix. That's how open source works, and it's how this book will stay current. Come for the code, stay for the community!

%% Author: add acknowledgments here (Drupal in a Day co-presenters, reviewers, contributors)? %%
