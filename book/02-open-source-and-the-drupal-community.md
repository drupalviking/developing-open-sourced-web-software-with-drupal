# Open Source and the Drupal Community

Before the Lens & Trail club builds anything, someone at the committee meeting is bound to ask the obvious questions. "Why Drupal, and not one of those website builders you pay for every month? Who's behind it? If it's free, what's the catch? And what happens if the people who make it lose interest?"

They're good questions, and this chapter answers them. Drupal is *open source* software, and that shapes everything about it: what you're allowed to do with it, what it costs, who makes it, and why it has been around since 2001. Understanding that is part of understanding Drupal.

In this chapter we look at:

- What open source means, and where the idea came from.
- The GPL, Drupal's license, and what it means for you as a site builder.
- Other licenses you'll come across, for code and for content (such as photos).
- Why you'd choose open source software, and the honest trade-offs.
- Who makes Drupal: the people, the companies, and the Drupal Association.

There's no hands-on work in this chapter. We start building in Chapter 4. How *you* can take part in the community is the topic of Chapter 22, at the end of the book, once you know your way around.

## What is open source?

When you buy a program, or download a free app, you usually get the program in a form your computer can run, but not in a form a person can read. The human-readable form, the *source code*, is kept by the company that wrote it. You may use the program, under the conditions the company sets, but you can't see how it works, change it, or share it.

*Open source* software turns that around. Its source code is published, and anyone may read it, use it, change it, and share it, under the terms of its *license*. A license is the legal text that says what you may and may not do with the software. With open source, the license is written to give you those rights, not to take them away.

### Free as in freedom

The idea is older than the name. In the early 1980s, Richard Stallman, a programmer at MIT, grew frustrated that more and more software came with its source code locked away. In 1983 he started the GNU project, to build a complete operating system made of software that anyone could use and share, and in 1985 he founded the Free Software Foundation.

Stallman described *free software* by four freedoms. As a user of a program, you should be free:

0. to run the program, for any purpose;
1. to study how the program works, and change it to do what you want (which needs access to the source code);
2. to share copies of the program with others;
3. to share copies of your changed versions with others.

Yes, they're numbered from zero. Programmers count from zero ;-)

Note what "free" means here. The Free Software Foundation's own way to put it is "free as in free speech, not as in free beer". Free software is about your freedom to do things with the software. It usually costs nothing as well, but that isn't the point, and selling free software is perfectly allowed.

### From free software to open source

The term *open source* came later, in 1998. That year, Netscape published the source code of its web browser, and a group of people in the free software world felt that the word "free" confused businesses: it sounded like "no price", or "no value". They proposed "open source" instead, and founded the Open Source Initiative (OSI), which keeps a definition of what counts as an open source license.

The two names come with different emphases. "Free software" stresses the users' freedom, as a matter of principle. "Open source" stresses the practical benefits: better software, made together. In practice they describe almost exactly the same software and licenses, and you'll hear both in the Drupal world. In this book we say *open source*.

The best-known open source project is probably Linux, started by Linus Torvalds in 1991. It runs most of the world's web servers, and Android phones are built on it. Drupal, the PHP language it's written in, the MySQL and MariaDB databases it stores its data in, and the Apache and nginx web servers that deliver its pages are all open source too. A Drupal website can run entirely on open source software, from the operating system up.

## The GPL, and what it means for you

Drupal's license is the **GNU General Public License**, the *GPL*, which Stallman wrote for the GNU project. Drupal was released under the GPL in January 2001, and it has been GPL ever since. To be precise, it's "GPL version 2 or later": you may use it under version 2 of the GPL, or under any later version, such as version 3 (from 2007).

### Copyleft: share alike

The GPL gives you all four freedoms. It also has one condition, and that condition is what makes the GPL special: **if you share the software, or a changed version of it, you must share it under the GPL too, with its source code.** You can't take GPL software, improve it, and then sell the improved version as a closed, proprietary program.

This is called *copyleft*, a play on copyright: it uses copyright law to keep software free, instead of to restrict it. The freedoms travel with the software, to everyone who gets a copy. That's why Drupal is still open source more than twenty-five years later, and why every improvement anyone has shared has stayed available to everyone else.

### Everything on drupal.org is GPL

Every module, theme, and recipe you can download from drupal.org is GPL too, version 2 or later. This is a rule of drupal.org: it only hosts code under that license (and code from elsewhere with a license that works with it).

That rule is a big part of Drupal's success. Because everything shares one license, any module can be combined with any other, and with Drupal core, without anyone having to check whether their licenses allow it. When we install modules for the club site in Chapter 11, you'll never have to read a license first.

### What the GPL asks of a site builder: almost nothing

Here's the part that surprises people. The GPL's condition only applies when you **distribute** the software, meaning when you give someone else a copy. Running a website isn't distributing. Visitors look at the pages Drupal produces; they don't get a copy of Drupal or of your modules.

So for you, as a site builder:

| Can I... | |
|---|---|
| ...use Drupal for a commercial website, or for a client? | Yes. Anyone can use Drupal for any purpose, and you may charge for your work. |
| ...keep my site's settings, and any custom code on my server, to myself? | Yes. You only have to share code you give to others. |
| ...keep my content to myself? | Yes. The GPL is about code, not about your content. The club's texts and photos are the club's, under whatever terms the club chooses. |
| ...sell a Drupal theme or module I made? | Yes, but under the GPL. Your buyers get all four freedoms, so they may change it and share it, even for free. |
| ...take Drupal, change it, and sell it as a closed product? | No. That's the one thing copyleft prevents. |

The last two lines explain something you may notice later: there are "premium" Drupal themes for sale on some websites. That's allowed. What you pay for is usually the work, the support, and the convenience, because the theme's code itself is GPL, like everything else in Drupal.

> **Coming from WordPress?** WordPress is GPL version 2 or later too, so the same rules apply. If you know how "premium" WordPress themes and plugins are licensed, you know how it works in Drupal.

> **Note:** This section is a summary for site builders, not legal advice. The details, such as which parts of a theme have to be GPL, and how to use code libraries under other licenses, are in drupal.org's *Licensing FAQ*, listed at the end of this chapter.

## Other licenses you'll meet

The GPL is one of many open source licenses. Roughly, they come in two families.

- **Copyleft** licenses, like the GPL, ask that changed versions are shared under the same license. They keep the software open.
- **Permissive** licenses, like MIT, BSD, and Apache, let you do almost anything with the software, including using it in a closed, proprietary product, as long as you keep the copyright notice. They make the software easy to use anywhere.

Neither family is better. They're different choices about what matters most to the people who wrote the software. Drupal itself uses code under permissive licenses: much of Symfony, the PHP framework underneath Drupal, is MIT-licensed. A permissive license fits inside a GPL project; it doesn't work the other way around.

Code isn't the only thing with a license. Text, photos, music, and videos have copyright too, and the licenses for software don't fit them well. For those, most people use **Creative Commons** licenses. This book is one of them: it's licensed under Creative Commons Attribution-ShareAlike 4.0 (*CC BY-SA*), which is the copyleft idea applied to writing. You may share and change the book, as long as you credit it and share your changes under the same license. drupal.org's documentation uses a CC BY-SA license too.

Here are the licenses you're most likely to meet:

| License | Family | For | In short |
|---|---|---|---|
| GPL (v2, v3) | Copyleft | Code | Share changed versions under the GPL, with source. Drupal, WordPress, Linux. |
| AGPL | Copyleft | Code | Like the GPL, but running the software as a website counts as sharing it. |
| LGPL | Weak copyleft | Code libraries | Changes to the library itself must be shared; programs that only use it needn't be. |
| MIT, BSD | Permissive | Code | Do almost anything, but keep the copyright notice. |
| Apache 2.0 | Permissive | Code | Like MIT, plus explicit rules on patents. |
| CC BY | Creative Commons | Text, images | Use it as you like, but credit the author. |
| CC BY-SA | Creative Commons, copyleft | Text, images | Credit the author, and share changed versions under the same license. This book. |
| CC BY-NC | Creative Commons | Text, images | Credit the author, and no commercial use. |
| CC0 | Public domain | Anything | No conditions at all. |
| Proprietary | Closed | Anything | Only what the owner allows, usually in a license agreement. |

Creative Commons licenses will matter to the Lens & Trail club, by the way. The club needs photos for its site before its members have uploaded their own, and many of the photos you can find online are under Creative Commons licenses. We come back to finding photos you're allowed to use in Chapter 9.

## Why choose open source?

So, back to the committee meeting. Why would the club choose Drupal, rather than a commercial website builder that charges a monthly fee?

This isn't a contest, and commercial website builders are good products. For a one-page site that never changes, one of them might be the right choice. But open source software has real advantages, especially for a site that should grow and last.

- **You own your site.** The code, the content, and the data are yours, on a server you choose. If your hosting company raises its prices, or closes, you move the site to another one.
- **No lock-in.** If you stop paying for a commercial website builder, the site usually goes away, and moving it elsewhere is hard. With open source, nobody can switch your site off, or force you to upgrade.
- **The cost.** Drupal costs nothing to download or use. You pay for hosting, and for people's time, which you would anyway.
- **Security out in the open.** Anyone can read Drupal's code, including security experts, and Drupal has a dedicated security team that handles vulnerabilities and publishes security advisories. We look at how that works in Chapter 20.
- **It lasts.** Drupal has been developed for more than twenty-five years. It doesn't depend on one company's business plans.
- **A community.** When you're stuck, thousands of people have probably had the same problem, and many of them are happy to help.

And the honest trade-offs:

- **There's no company to call.** If something breaks, nobody is obliged to fix it for you. You can pay a Drupal agency or hosting company for support, but you have to choose one.
- **You're responsible.** Updates, security, and backups are your job, or the job of whoever you pay. Chapter 20 shows how.
- **It takes learning.** Drupal can do a lot, so there's a lot to learn. You're reading this book, so you've already accepted that ;-)
- **It depends on people.** Open source projects are kept alive by people who contribute, as volunteers or because their employers pay them to. A project nobody contributes to slowly dies. Which brings us to who makes Drupal.

## Who makes Drupal?

Drupal isn't made by one company. It's made by thousands of people, all over the world, and most of them never meet. They work together in public, on drupal.org, and once or twice a year many of them do meet, at DrupalCon and at the many local Drupal Camps.

### The project lead

**Dries Buytaert** started Drupal in 2000, as we see in Chapter 3, and he's still the project's lead. He sets the overall direction, such as the Drupal CMS product, and has the final word when the community can't agree. The name "Drupal" is a registered trademark that he owns, which is how the project protects its name from misuse.

### Core committers and maintainers

Anyone can suggest a change to Drupal core, but only a small team of **core committers** can add a change to the code. They review proposals, decide whether they're ready, and look after the releases. Committers have different areas of responsibility: some look after the code's architecture, some after the releases, and some after the product, meaning how Drupal works for the people who use it.

Below them are **subsystem maintainers**, experts in one part of core, such as the media system or Views, and the **maintainers** of the contributed modules and themes. Every project on drupal.org has one or more maintainers, who decide what goes into it, and make its releases.

### Contributors

And then there are the **contributors**: everyone who reports a bug, suggests a fix, tests someone else's fix, writes documentation, translates Drupal's interface into their own language, designs, checks accessibility, organizes an event, or mentors a newcomer. All of that is contribution, and a lot of it isn't code. Every change to Drupal starts as an *issue*, a public discussion on drupal.org where anyone can take part, and goes through review by other people before it's accepted.

The **Drupal Security Team** is a group of people, many of them volunteers, who handle security problems: they work with maintainers to fix them, privately, before they're announced, and then publish security advisories. When you saw the shield icon on a module's page in Chapter 1's exercises, that was the security team's coverage.

### The companies

Many contributors are paid by their employers to work on Drupal: Drupal agencies, hosting companies, and organizations that run big Drupal sites. They do it because they depend on Drupal, and because a better Drupal is better for their business.

drupal.org keeps track of this. Since 2015, when an issue is solved, the people who worked on it get **credit**, and they can say which organization paid for their time. Organizations that offer Drupal services are listed on drupal.org, ranked by the credit they've earned. That way, the companies that give the most back to Drupal are the easiest to find, which is a nice incentive to contribute.

### The Drupal Association

The **Drupal Association** is a nonprofit organization that supports the project. It runs drupal.org and its infrastructure, supports DrupalCon and the community, and works to grow Drupal's use. It's funded by memberships, by partner companies, and by sponsorships.

The Drupal Association doesn't decide what goes into Drupal. That's the work of the contributors, maintainers, committers, and project lead. The Association makes it possible for them to work together.

### Drupal CMS

Drupal CMS, the product we met in Chapter 1, is made the same way. It started in 2024 as an initiative called *Starshot*, and it's built by a team of contributors from many companies, in public, on drupal.org, like everything else.

> **Note:** You'll hear the Drupal motto again and again: **"Come for the code, stay for the community."** It's the line on the front page of a new Drupal site, too (look at Figure 1.1). We get to how you can be part of that community in Chapter 22.

## Summary

- Open source software comes with its source code, and a license that lets anyone use, study, change, and share it. The idea started as *free software*, "free as in free speech, not as in free beer".
- Drupal's license is the GPL, version 2 or later, and so is everything on drupal.org. The GPL is *copyleft*: if you share a changed version, you must share it under the GPL.
- Running a website isn't distributing the software. You may use Drupal for any purpose, and keep your site and content to yourself.
- Permissive licenses (MIT, BSD, Apache) ask less than copyleft licenses. Creative Commons licenses are for content, such as this book and the photos the club needs.
- Open source gives you ownership, no lock-in, and a community; in return, you're responsible for keeping your site up to date.
- Drupal is made by its project lead, core committers, maintainers, and thousands of contributors, many paid by companies, with the Drupal Association supporting the project.

## Exercises

1. **Your own software.** List five programs or apps you use every day. For each, find out whether it's open source or proprietary, and what its license is. Which of the four freedoms do you have with each?
2. **The people behind a module.** Open the project page of the Pathauto module on drupal.org (<https://www.drupal.org/project/pathauto>). Who maintains it? Which organizations support it? Is it covered by the security team? How many sites report using it?
3. **Who pays for Drupal?** Find drupal.org's list of organizations that offer Drupal services. Find one in or near your own city (or in Edinburgh, for the club). How much contribution credit does it have, and what kinds of contribution does its profile show?
4. **The committee meeting.** A committee member suggests that the club use a commercial website builder instead of Drupal. Write down three honest arguments for each option. Which would you recommend for the club, and why? There's no single right answer.
5. **The photo** *(challenge)*. A club member finds a beautiful photo of the Pentland Hills on Wikimedia Commons, licensed under CC BY-SA 4.0. The club wants to use it on its website, and a cropped version on a printed poster for its annual photo exhibition. What does the license ask of the club in each case? What would change if the photo were licensed CC BY-NC instead, and the exhibition charged an entrance fee?

## Want to know more?

- [What is free software?](https://www.gnu.org/philosophy/free-sw.html), by the Free Software Foundation: the four freedoms, in their own words.
- [The Open Source Definition](https://opensource.org/osd), by the Open Source Initiative: what makes a license open source.
- [Licensing FAQ](https://www.drupal.org/about/licensing), on drupal.org: the GPL and Drupal, in detail. Read this if you ever sell a theme or module.
- [Choose a license](https://choosealicense.com/licenses/): the common open source licenses, compared side by side.
- [About the Creative Commons licenses](https://creativecommons.org/share-your-work/cclicenses/): the six Creative Commons licenses, and what each allows.
- [The Drupal Association](https://www.drupal.org/association): what it does, and how it's funded.
- [Getting credit for work on issues](https://www.drupal.org/docs/develop/issues/fields-and-other-parts-of-an-issue/getting-credit-for-work-on-issues), on drupal.org: how the credit system works.
