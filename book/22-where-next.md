# Where Next?

Twenty-one chapters ago, Lens & Trail was an idea: a small club in Edinburgh that wanted a place for its hikes and its photos. Now it has a site, in two languages, with hikes, albums, news, members, roles, nice addresses, backups, and a plan for going live. And you built it.

This last chapter has no new screens on the club's site. It's about what comes after the book: the people behind Drupal, and how you can be one of them. Chapter 2 told you who makes Drupal. Here we show you how you can take part, even if you never write a line of code, with a real example from the writing of this book. Then we look at where to learn more, where Drupal skills can take you, and what the club could build next.

## You're already part of it

Remember the motto from the front page of a new Drupal site: "Come for the code, stay for the community." Most people come for the code, the way you did. Staying means doing something, however small, that helps the next person.

That's less daunting than it sounds. Drupal needs a lot more than programmers. Look at what you've done in this book: you've read documentation, compared modules, checked whether they support Drupal 12, read a security advisory, and noticed when a screen didn't match what the book said. Every one of those is something the project needs people for:

- **Reporting a bug** well, so someone else can see it too.
- **Testing a fix** someone else wrote, and saying whether it works on your site. Site builders are the best testers: you use the screens every day.
- **Writing and fixing documentation**, on drupal.org's documentation pages, which anyone with an account can edit.
- **Translating** Drupal's interface into your language (more on that below).
- **Answering questions** from people who know less than you, in the forums or on Drupal Slack. After this book, that's a lot of people.
- **Organizing**: a meetup in your city, a stand at a conference, a Drupal in a Day for students.
- **Design, accessibility, marketing and events**, which all have teams of their own.

drupal.org's [Contributor guide](https://www.drupal.org/community/contributor-guide) sorts all of this into tasks, roles and skills, and many of the tasks take a few minutes. It's the place to start.

> **Drupalism: d.o and friends.** The community has its own shorthand, and you'll see it everywhere once you start reading issues:
>
> - **d.o** is drupal.org, as in "post it on d.o".
> - **The queue** is a project's list of issues: "it's in the queue".
> - **Core** and **contrib**: Drupal core, and the contributed modules and themes (Chapter 11).
> - **NR**, **NW** and **RTBC**: the statuses *Needs review*, *Needs work*, and *Reviewed & tested by the community*. We come to them below.
> - **MR**: a merge request, a proposed change to the code.
> - **The DA**: the Drupal Association (Chapter 2).
> - **A camp**: a DrupalCamp, a local or regional conference.

## How an issue works: a story from this book

Every change to Drupal, from a typo in a help text to a new feature, starts as an **issue**: a page on drupal.org that describes a problem, where people discuss it, propose a fix, and test it. Each project, core included, has its own list of issues, its **issue queue**. Here's how one of them came to be, while we were writing this book.

### Something isn't right

While we retook the screenshots for Chapter 15, our script deleted the user fields *Camera* and *About me*, and made them again, with the same names. A few days later, the club's Status report showed an error we hadn't seen before: **Entity/field definitions: Mismatched entity and/or field definitions**, with "The user.field_camera field needs to be updated." Nothing on the site was broken. The fields worked, the data was there. But an error on the Status report is an error, and Chapter 20 told you not to ignore them.

### Search first

The first rule on drupal.org is to search the queue before you report anything: the chances are that someone has seen it before you. We searched Drupal core's queue for the message. There were many issues with it, because it can have many causes, and one that looked like ours: an issue from 2016 about deleting a field and making a new one with the same name. It was fixed, though: it was about the field's *data*, and our data was fine. Ours was something else.

So we tried to make it happen again, on purpose, on a fresh copy of the newest development version of Drupal core (the second rule: check that the problem is still there in the newest code). Add a field, give it a value, delete the field, make a new one with the same name, run cron. The error came back every time. That's the most valuable thing a bug report can have: **steps to reproduce**, a recipe anyone can follow to see the problem for themselves.

### Find the cause, if you can

Deleting a field that has data doesn't remove the data at once: Drupal keeps it until cron cleans it up, a little at a time. When it finally cleaned up the old *Camera* field, it also threw away a small record that Drupal keeps about each field's database table, and by then that record belonged to the new *Camera* field. Hence the error.

That part took a developer, and you don't need it to report a bug: a clear report with steps to reproduce is a real contribution on its own. But since we had found the cause, we wrote a fix (a few lines), and a test: a small program that runs the steps and checks that the record is still there afterwards. The test fails without the fix and passes with it, which is how the people who look after core know the fix does what it says.

### Write it up

A good issue has a clear title, and a summary that a stranger can follow. Drupal core's issues use the same headings, and ours had them all:

- **Problem/Motivation**: what goes wrong, and why it matters.
- **Steps to reproduce**: the recipe.
- **Proposed resolution**: what we think should change.
- **Remaining tasks**: what's left to do, such as a review, or a decision about sites that already have the error.
- Changes to the **user interface**, the **API** (what other code relies on) and the **data model**: none, in our case.

We posted it as [issue #NNNNNNN](https://www.drupal.org/project/drupal/issues/NNNNNNN), *Purging a deleted field removes the schema data of a new field with the same name*, in the *field system* part of core, as a **Bug report** with **Normal** priority, and linked it to the issue from 2016.

### What happens next

An issue moves through **statuses**, which you can see at the top of every issue, and filter by in every queue:

1. **Active**: reported, nobody has proposed a fix yet.
2. **Needs review**: there's a proposed fix, and it needs someone to look at it and test it. That's where ours started.
3. **Needs work**: someone looked, and something needs changing. Issues go back and forth between these two, often several times. It's normal, and nobody takes it personally.
4. **Reviewed & tested by the community** (RTBC): someone other than the author has tested it and is happy with it.
5. **Fixed**: a core committer (Chapter 2) has accepted it into Drupal. Two weeks later it becomes **Closed (fixed)**.

There are other endings too: **Closed (duplicate)** if it was reported before, **Closed (works as designed)** if it isn't a bug after all, **Postponed** if it waits for something else. None of them is a failure: they all save somebody's time.

This can take days or years, depending on how many people care about the issue and how risky the change is. When it's fixed, everyone who helped gets **credit** on drupal.org (Chapter 2): not only whoever wrote the code, but the people who reported it, tested it, and commented usefully. 

> **Note:** Security holes are the one exception to "report it in the queue". Never post them in public: report them to the security team, which works in private until a fix is out (Chapter 20).

> **Try it:** Look at a queue. Go to the Pathauto project page (Chapter 17), and select **All issues** in the box on the right. You'll see the queue, with a filter at the top. Set **Status** to **Needs review**, and open one of the issues. Read the summary and the comments: what's the problem, who proposed the fix, and what did the reviewers say?
>
> 

### Your first contribution

To post, comment or edit documentation on drupal.org, you need an account. It's free: select **Log in** at the top of drupal.org, then **Create new account**. Once you have one, you can **follow** an issue (a button at the top of the issue), and drupal.org emails you when someone comments. Following a few issues in modules you use is a good way to learn how the community works, before you say anything yourself.

When you're ready, a good first issue is one tagged **Novice**: they're picked out as good first tasks, often small fixes to text or documentation. The contributor guide has [a search for them](https://www.drupal.org/project/issues/search?projects=&project_issue_followers=&status%5B%5D=1&status%5B%5D=13&status%5B%5D=8&issue_tags_op=%3D&issue_tags=Novice). Read drupal.org's [issue etiquette](https://www.drupal.org/docs/develop/issues/issue-procedures-and-etiquette/issue-etiquette) first: be patient, be kind, and don't post "+1" or "any update?": say what you tested and what happened instead.

### Translating Drupal

In Chapter 18, Drupal downloaded thousands of Spanish translations of its interface for you. Volunteers wrote every one of them, on **[localize.drupal.org](https://localize.drupal.org/)**. If you speak another language, it's one of the most direct ways to help, and you see the result on every site in that language. Find your language, join its team, and suggest translations for strings that don't have one yet. A second person from the team approves each suggestion, and then it's on its way to every Drupal site that uses your language, the club's included.

> **Try it:** On localize.drupal.org, find the Spanish team (or your own language's), and look at its translation of a module the club uses, such as Pathauto. How much of it is translated? You don't need to translate anything to look.

### Talking to people

Most of the community's conversation happens in **[Drupal Slack](https://www.drupal.org/slack)**, which anyone can join. Start in **#support** for questions and **#contribute** for help with contributing. There are channels for most countries and many cities, and for most big modules.

## Meeting people

The community is at its best in person, and there's an event for every size:

- **Meetups**: an evening, often in a pub or at a company's office, once a month. Edinburgh has one, *Drupal Drinks*: the club's webmaster could go along.
- **DrupalCamps**: one to three days, run by volunteers in a city or a country, with talks, often a contribution day, and tickets that cost little.
- **DrupalCon**: the big ones, run with the Drupal Association, with thousands of people. The next DrupalCon Europe is in Edinburgh, 25 to 28 October 2027, in the club's own city. Lens & Trail could lead a walk up Arthur's Seat for the attendees. :-)
- **Contribution days**: a day of working on issues together, usually the last day of a DrupalCon or a camp, with **mentors** who help first-timers with everything from making an account to their first merge request. If you go to one event in your life, go to the contribution day.
- **Drupal in a Day**: a free workshop for students and newcomers, at DrupalCons and camps, where you build a site in a day. It's run by the **Drupal Open University Initiative**, which is also behind this book and the teaching of Drupal at universities. 

drupal.org's [events page](https://www.drupal.org/community/events) lists them all, and you can search it by place and type.

## The Drupal Association

Chapter 2 introduced the **Drupal Association**: the nonprofit that runs drupal.org, its issue queues, its translations server and its security infrastructure, and DrupalCon. All of the tools in this chapter are paid for by it, and through it by the companies and people who support it.

You can support it too. [Individual membership](https://www.drupal.org/association/individual-membership) starts at nothing at all (which gives you a vote in the Association's elections), and from there you pick a small monthly or yearly amount. If Drupal saves your club, your school or your employer money, it's a good place to put some of it back. Companies that build Drupal sites can become partners, and many of the hosts from Chapter 21 do.

## Learning more

This book teaches site building. Where you go next depends on what you liked best:

- **More site building**: the [Drupal User Guide](https://www.drupal.org/docs/user_guide/en/index.html), written and translated by the community, covers much of this book in a different order, and goes further in places. The documentation of each module you use is on its project page.
- **Theming**: how a site looks, with HTML, CSS and Drupal's template language, Twig. drupal.org's [Theming Drupal](https://www.drupal.org/docs/develop/theming-drupal) guide starts where our Chapter 16 stopped.
- **Module development**: writing your own modules, in PHP. Appendix B shows how Drupal's code is built, and drupal.org's [Creating modules](https://www.drupal.org/docs/develop/creating-modules) guide is the next step.
- **Running sites**: servers, deployment, and the developer tools from Appendix A.

Among other places, [Drupal at your fingertips](https://drupalatyourfingertips.com/) is a free book for developers, [Drupalize.me](https://drupalize.me/) has tutorials (some free, most for subscribers), the [Talking Drupal](https://www.talkingdrupal.com/) podcast talks to the people who build Drupal every week, and [The Weekly Drop](https://weeklydrop.com/) newsletter collects the week's news.

## Drupal and your career

Drupal runs sites for governments, universities, newspapers and charities all over the world, and the people who build them are often hard to find. There's work at every level:

- **Site builders**, which is what you are now: content models, views, permissions, configuration.
- **Front-end developers** and **themers**: how it looks, and whether everyone can use it.
- **Back-end developers**: modules, integrations, migrations from other systems.
- **DevOps**: servers, hosting, deployment, performance.
- **Project managers**, **product owners**, **trainers** and **content strategists**, who need to know what Drupal can do without building it themselves.

Most Drupal jobs are with the agencies that build sites for others, and with the organizations that run big Drupal sites themselves. drupal.org's [list of Drupal service providers](https://www.drupal.org/drupal-services) shows the agencies, with their offices and their contribution (Chapter 2's exercise), and many of them are hiring. Meetups and camps are where many people find their first Drupal job: the people who hire are there too.

Contribution counts here. Your drupal.org profile shows your issues and your credits, and to anyone hiring for Drupal it's a portfolio: proof that you can work with others in public, and that you know how the project works.

> **Note:** There's also a certificate, if you want one: Acquia, the company Dries Buytaert co-founded (Chapter 3), offers [certification exams](https://www.acquia.com/support/training-certification/acquia-certification), including one for site builders. They cost money, and they're not required for Drupal work: many people in the community never take one. But some employers ask for them, and after this book you know most of what the site builder exam covers.

## What's next for Lens & Trail?

Look back at the club's site for a moment. You've built:

- four content types, with fields, displays and layouts, and media with credits (Chapters 6 to 9);
- vocabularies for areas and photo themes (Chapter 10);
- lists of upcoming hikes, albums and photos, and reports for the club (Chapters 12 and 13);
- blocks, menus and a theme (Chapters 14 and 16);
- members, roles and permissions, and a moderation workflow (Chapters 6 and 15);
- nice addresses, a sitemap, and a site in two languages (Chapters 17 and 18);
- updates, backups, and a way to move configuration to a live site (Chapters 20 and 21);
- and, on Drupal CMS, a site with AI to help (Chapter 19).

A club never stops having ideas, though. Here are a few the club could ask for next, and where you'd start:

- **Sign up for a hike**: members say they're coming, and the hike leader sees a list. Look at the **Registration** module, or **Webform** for a form per hike.
- **A members-only area**: pages, albums or a forum that only members can see. Roles and permissions get you part of the way (Chapter 15); the **Group** module gives each group of people its own content and members.
- **A newsletter**: the next hikes, every month, by email. Look at **Simplenews**, or a mailing service with a Drupal module.
- **Favorites and photo of the month**: members mark photos they like, and the most popular wins. The **Flag** module lets people mark content, and a view counts the marks.
- **A shop**: calendars and prints of the members' photos. **Drupal Commerce** is a whole shop, built from Drupal's own pieces: products are entities, with fields.

You know how to find each of these now (Chapter 11), how to judge them, and how to check whether they support your Drupal version. They're all big, well-kept modules with many sites using them, and their Drupal 12 releases are expected soon after Drupal 12 itself; check the project page all the same, as Chapter 20 showed. Whichever you pick, you'll recognize the pieces: content types, fields, views, roles, and configuration that moves from your computer to the live site.

## Summary

In this chapter you learned:

- That contributing to Drupal isn't only code: reporting, testing, documentation, translation, answering questions, and organizing all count.
- How an issue works, from a report with steps to reproduce to a fix with credit for everyone who helped, and what the statuses mean.
- Where to start: the contributor guide, Novice issues, localize.drupal.org, and Drupal Slack.
- What events there are, from a meetup to DrupalCon, and why the contribution day is worth going to.
- What the Drupal Association does, and how to support it.
- Where to learn more, and what kinds of work there are for people who know Drupal.
- What the club could build next, and how to start.

## Exercises

1. Find the issue queue of a module the club uses (Chapter 17's Redirect, say). How many issues are open? How many need review? Open one that's RTBC: who reported it, who fixed it, and who tested it?
2. Find the next Drupal events near you on drupal.org's events page: a meetup, a camp, and the next DrupalCon. Which would you go to first, and why?
3. Make a drupal.org account, and fill in your profile. Follow two issues in modules you've used in this book, and read what happens to them over the next few weeks.
4. On localize.drupal.org, find your language's team (or Spanish, the club's second language). How much of Drupal core is translated? Find a string from a module the club uses that has no translation yet.
5. Pick one of the club's next ideas. Find the module, check its Drupal version support and its issue queue, and write a plan: which content types, fields, views and roles you'd make, and what the hike leaders and Morag would see.
6. *(challenge)* Find a Novice issue, or a documentation page that's out of date, in an area you know from this book. Make one useful contribution: test a fix and report what happened, or correct the page. Then tell someone about it. :-)

## Want to know more?

- drupal.org's [Contributor guide](https://www.drupal.org/community/contributor-guide): ways to help, by task, role and skill.
- [Issue etiquette](https://www.drupal.org/docs/develop/issues/issue-procedures-and-etiquette/issue-etiquette), before you post your first comment.
- Our issue: [#NNNNNNN](https://www.drupal.org/project/drupal/issues/NNNNNNN), *Purging a deleted field removes the schema data of a new field with the same name*.
- [localize.drupal.org](https://localize.drupal.org/), for translators.
- [Drupal Slack](https://www.drupal.org/slack), and how to join.
- drupal.org's [events](https://www.drupal.org/community/events), and [DrupalCon Edinburgh 2027](https://events.drupal.org/edinburgh2027).
- The Drupal Association's [individual membership](https://www.drupal.org/association/individual-membership).
- The [Drupal User Guide](https://www.drupal.org/docs/user_guide/en/index.html).
- This book's own repository, from the Preface: if something in it was wrong or unclear, an issue or a pull request there is a fine first contribution too.
