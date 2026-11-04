# A Short History of Drupal

You might not know but Drupal has been able to buy alcohol in almost all countries that sell alcohol for from three to seven years! It has been around since 2000, although it's not a millennium bug! 

## Origins of Drupal (2000 - 2001)
Drupal was created by Dries Buytaert, a Belgian Student at University of Antwerp in Belgium. He started developing a small PHP-based message board system in late 2000. The purpose of the message board was to share news and files with friends on his university LAN. The software was named drop.org, referencing the idea of a "drop" in a network.

Early on, Drop wasn't intended to be a CMS. It was a collaboration and experimental tool. The content management capabilities emerged from community use and expansion. It's code was released under the GNU GPL on January 15th, 2001. At the same time it got re-branded as Drupal, which is derived from the Dutch word Druppel, which means "drop" and also got it first version number, 1.0.

## Drupal becomes a CMS (2001 - 2005)
The newly open-sourced Drupal quickly grew as contributors added features like modules, themes and user management to it, elements that are still in the system today, although it has changed significantly.

The first versions introduced a hook system, allowing extensibility without modifying the core, the ability to define content types and custom fields.

It also had a budding template system, very basic theming layer, which were the first steps toward separating content logic from presentation — but still far from the robust template engines we have today.

The first version had very primitive separation of HTML from PHP and was mostly hardcoded into PHP files. Theming basically meant editing `.php` files that would output the HTML directly. The "theme" was just a folder containing HTML and stylesheets.

Some variables were passed into template functions, but there was no sophisticated templating language as we have today.

It was called "budding" because it was the "beginning of a theming system", a move away from mixing logic and presentation entirely. The architecture was extensible, you could swap themes and override rendering functions without changing core. It also hinted at what would later become fully mature template engines.

## Maturing into a Community CMS (2006 - 2010)
### Drupal 4.7
Drupal 4.7 was released in May 2006 and is often considered to be a milestone in the Drupal history. That's the point where Drupal jumped from being a small but flexible CMS to a platform capable of powering large, complex and highly customized sites.

It included a new Form API (FAPI) which was game changing for module developers. It standardized the way forms were built, rendered and validated and allowed easy theming of form elements. It also centralized input validation and security (e.g. CSRF protection).

It introduced the Node Access System, a more granular permission system for controlling access to individual pieces of content (nodes) and enabled complex workflows and per-role/per-user content restrictions. This feature was huge for enterprise, government and community sites.

It had a full menu system overhaul that made navigation menus dynamic and customizable. Improved the API for developers to register and alter menus and offered better integration with access control, so menus could adapt based on permissions.

4.7 also offered taxonomy enhancements which meant more flexible categorization tools, it improved term relationships and vocabularies and was a yet another cornerstone for Drupal's reputation for structured content management.

There was also a huge theme system improvements which offered better separation of logic from presentation compared to earlier versions. It was still PHP-based templates but was paving the way for the `.tpl.php` approach which appeared in Drupal 5

Lastly there was significant caching improvements and better handling of large databases and high-traffic sites. Drupal started to be taken seriously for large-scale deployments!

To sum it up, before 4.7, Drupal was flexible but still best for small-to-medium sites run by tech-savvy admins. But after 4.7 it became a serious application framework that could handle complex permissions, build dynamic, data driven forms easily, supported intricate navigation and taxonomy structures and scaled up to enterprise-level needs.

### Drupal 5 and 6
In these years Drupal 5 and 6 also marked significant maturity. They had more polished admin interfaces, they consolidated contribution modules into core like FCKeditor and jQuery and they had strong support for multi-language and access control.

In these years DrupalCon events began forming globally, and drupal.org became a hug for module sharing, documentation and development. 

During this period, Drupal solidified its reputation as the go-to CMS for structured content, especially in government, education and nonprofit sectors. That became very clear when the White House launched its site in Drupal in 2009 along with MIT, Amnesty International and various UN agencies.

## Framework ambitions and Enterprise shift (2011 - 2015)
Drupal 7 (2011) was a watershed release. It introduced the Entity API, which meant treating content as structured data, core fields became available on all entities and not just nodes. It also had a vast ecosystem of contributed modules like Views, Rules and Features, which became staple modules in almost every single Drupal site built.

By this point, Drupal had become less a CMS and more content platform, developers used it to build bespoke applications with complex content models.

But there were also some drawbacks. Legacy procedural PHP made maintainability and testing harder. There was also a lack of standardized configuration management across environments.

And lastly, customers and users were getting tired of the fact that with every major Drupal upgrade came a system overhaul, new theming and new data models usually meant that there was no "update" button, but a major transformation to the new system.

## The Big Rewrite - Drupal 8 the Reinvention with Symfony (2015)
Drupal was at an intersection. It needed to make a decision to mature even further, but without forcing the users, the customers to entirely redesign with every update. So with Drupal 8, the community decided to make the "last rewrite of Drupal".

This meant new thinking. Object-oriented architecture was chosen instead of procedural approach. The old PHPTemplate system was switched out for a more robust Twig templating engine. And to speed things along and get assistance with core features, the Symfony framework was adopted.

It introduced a full Configuration Management System (CIM) with YAML, embedded composer as a package/dependency manager and provided RESTful Web Services out of the box.

Drupal 8 also marked the start of the "API-first" era, preparing for decoupled (headless) architectures using React, Vue, or other front-end frameworks.

And last but not least, it introduced semantic versioning system, leaving the old major/minor system behind.

These changes did not come without a cost though. While they made Drupal more modern and aligned with PHP standards, they alienated many casual site builders. The learning curve became even steeper and the ecosystem experienced fragmentation during the transition. The biggest hurdle was the transition to object-oriented programming since the 

Drupal 8.0.0 was launched in November 15th, 2015 on Dries' birthday.

## Modernization and Streamlining (2020-2024)
In June 2020 we experienced the first big upgrade after the "Let's not do any more upgrades" upgrade. Dries Buytaert himself quoted: "The big deal about Drupal 9, is that it isn't a big deal!" And he was right. With the semantic update path Drupal had chosen, such updates were (almost) walk in the park. At least for core. The last version of Drupal 8 was 8.9.14 (9 minor
updates and 14 bugfixes for the x.9 branch). And the only difference between 8.9.14 and 9.0.0 was the removal of deprecated code. Drupal 9 wasn't an "upgrade". It was a "cleanup"!

As you might imagine, code and methods get old as the language, the frameworks and methods change. When that happens within a semantic-versioned code, instead of changing the behavior of a code function, we write a completely new function and mark the old one deprecated.

> **Example:**
> 
> In version 8.3.0 we introduce a new functionality: `renderUpsideDown(Node $node): array` which will render the content of a node upside down. In 8.5.0 we added a parameter to the function to add taxonomy terms too: `renderUpsideDown(Node $node = null, Term $term = null): array` And finally, in 8.9.0 we decided that no one is using the
> function but a huge request is for `renderSideways(Term $term): array` And although we were able to add the parameter for `renderUpsideDown` with ease, `renderSideways` is a totally different functionality that `renderUpsideDown`. So what will happen is that `renderUpsideDown` function is marked `@deprecated` in the code, from 8.9.0. If anybody is writing a code (and has an IDE), a warning will display in the editor indicating that you are using deprecated code and should use `renderSideways` instead. The good thing though is that if somebody implemented a module in 8.5.3, it would still work all the way through 8.9.14. Nothing would break. Except the fact that when 9.0.0 is released, `renderUpsideDown` is removed from
> the codebase. 
> 
> And that would prevent the upgrade from 8.9.14 to 9.0.0.  The module maintainer would need to upgrade the module to use the 9.0.0 approved function `renderSideways` in order to upgrade to 9.0.0

Which was a headache to begin with. Module maintainers weren't very quick to upgrade from 7 to 8 and they were even slower to make their code 9.x compatible. Even though in many cases, the only thing needed to do was to modify one line in the `MODULE_NAME.yml` file! First there was a huge movement of people who went on to fix those modules, but in later versions we actually have an automated procedure called Drupal Rector that updates modules that could be easily updated like that.

Of course that doesn't apply to all modules and there is still a lot of them that need manual updates. But still, the transition from 8.x - 9.0 was easier than ever before and from 9.x - 10.0 was even easier!

We continued using Symfony and Twig, but upgraded them also to new versions, kept innovating with our collaborators.

The major breakthroughs in 9, 10 and 11 were:
* Removal of deprecated code
* Symfony 6 and CKEditor 5
* Starter kits for themes
* Better front-end developer kits
* Refine automatic updates and the project browser UI
* Drop legacy modules (e.g. CKEditor 4, jQuery UI)
* Improve out-of-the-box user experience
* Enhance front-end performance and DX

Drupal 11 also focused on strategic initiatives like:
* Low-code/no-code admin experience
* Better starter kits and distributions
* Stronger Javascript integration
* Tighter composer-based ecosystem
* Recipes for installation and configuration of modules instead of installation profiles

The key shift was toward continuous innovation rather that disruptive rebuilds.

## The Road ahead (Drupal CMS, 11 and 12)
In 2023, Dries showed us his vision of Drupal. He wanted to make Drupal more accessible to larger groups. Single button installs, fully configurable GUI tools, automatic updates....

In the beginning, his vision was called Starshot, but it was later rebranded as Drupal CMS. Drupal CMS is literally Drupal core with some recipes added on top to make the "out-of-the-box" experience better. 

**Write a little bit more about Starshot and the road map in 12**
