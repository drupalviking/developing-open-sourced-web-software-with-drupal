# Appendix C: Patching a Contributed Module

%% Author: this appendix becomes Appendix C, and the answers move to D, when the chapter list is final (Backlog: renumbering). Until then both files start with "Appendix C". %%

Sooner or later, a module you need doesn't quite work. Maybe it has a bug, maybe it doesn't support your version of Drupal yet. Very often someone has already found the problem, and posted a fix in the module's issue queue (*Where Next?* shows how the queue works), but the maintainers haven't made a release with it yet. This appendix shows how to use such a fix on your site, safely, until the release comes. We use the three fixes Chapter 22 needs on Drupal 12 as the example.

The one rule: **never change a module's files by hand.** Composer put them there, and Composer replaces them the next time you update, or when a colleague runs `composer install` on another computer. Your change would be gone, without a word. Instead, you tell Composer about the change, and it makes the change for you, every time.

## What a patch is

A *patch* is a file that describes a change to some files: which lines to remove, and which to add. Here's the smallest one Chapter 22 uses. Search API's Database Search module says, in its description file, which Drupal versions it supports, and the patch adds Drupal 12:

<!-- include: examples/search/patches/search_api-3630149-db-info.patch lines=1-12 as=patches/search_api-3630149-db-info.patch -->

Lines starting with `-` go, lines starting with `+` come, and the lines around them show where. Programs that apply patches use those lines to find the place, even if the file has changed a little elsewhere.

## Where fixes come from

On drupal.org, fixes come in three forms, and you can turn each into a patch file:

- **A merge request** (*MR*): a proposed change, waiting for the maintainers to accept it. The issue page links to it, as **!64** or similar. Add `.diff` to its address on git.drupalcode.org, and you have it as a patch: `https://git.drupalcode.org/project/search_api_autocomplete/-/merge_requests/64.diff`. Keep in mind that a merge request can still change: people improve it until it's accepted.
- **A commit**: a change the maintainers have accepted into the module's development code, but not yet released. Add `.patch` to the commit's address: `https://git.drupalcode.org/project/search_api/-/commit/ece4453f.patch`.
- **A patch file** attached to an issue: the older way, still common in older issues.

Download the file, and save it in a folder called `patches/` next to `composer.json`, with a name that says what it is: the module, the issue number, and a few words. `search_api-3552883-initial-preprocess.patch`, for example. Keeping the file in your project, rather than downloading it from drupal.org every time, means it can't change under you.

Sometimes you need only part of a merge request. Chapter 22's Database Search fix is the description-file part of a bigger merge request, which also changes code we don't need yet. A patch is a text file, and you can cut it down to the files you want; that's what we did.

## The composer-patches plugin

Composer can't apply patches on its own. The **composer-patches** plugin, by Cameron Eagans, teaches it, and nearly every Drupal project uses it. Add it once:

```
ddev composer require cweagans/composer-patches:^2
```

Composer asks whether to trust the plugin, because plugins run code during installs; answer `y`. Then list your patches in `composer.json`, under `extra`, with the module's Composer name, a description, and the file. These are Chapter 22's, in the book's repository:

<!-- include: examples/search/composer-extra.json as=composer.json -->

The descriptions are for people: say what the patch fixes, and link the issue, so that you, or whoever looks after the site next year, can check whether it's still needed. (Ignore `drupal-lenient` for now; it's the next section.) Copy the three patch files from `examples/search/patches/` into your `patches/` folder. If your `composer.json` already has an `extra` section, as Drupal's usually does, add `patches` inside it, next to what's there.

Then tell the plugin to read the list, and apply it:

```
ddev composer patches-relock
ddev composer patches-repatch
```

`patches-relock` writes `patches.lock.json`, a record of every patch and a checksum of its file, which you commit with `composer.json` and `composer.lock`. `patches-repatch` removes the patched modules and installs them again, with the patches applied. Composer lists each module as it patches it:

```
  - Patching drupal/search_api
  - Patching drupal/search_api_autocomplete
```

From now on, every `composer install` and `composer update` applies them, on every copy of the site.

## Modules without a release for your Drupal: the lenient plugin

Search API Autocomplete is a different case. Its newest release says, in its own Composer file, that it works with Drupal 10 and 11. On a Drupal 12 site, Composer refuses to install it, before any patch has a chance. The **composer-drupal-lenient** plugin, by Matt Glaman, lets Composer install it anyway, for the modules you name, and only those:

```
ddev composer require mglaman/composer-drupal-lenient
ddev composer config --merge --json extra.drupal-lenient.allowed-list '["drupal/search_api_autocomplete"]'
```

The second command adds the module to the plugin's list, `drupal-lenient` in the `composer.json` above. Now `ddev composer require drupal/search_api_autocomplete` works, and the patch from its merge request makes it actually run on Drupal 12.

Be careful with this. The plugin only stops Composer from checking; it doesn't make the module work. A module whose release doesn't list your Drupal version may work fine (often the maintainers haven't updated the list yet), or it may break the site. Try it on a copy of the site first, as we did, and look at the module's issue queue for "Drupal 12" before you do: the work is usually there.

## When the release comes

A patch is meant to be temporary. When the module has a release with the fix, update the module, and Composer will fail to apply the patch, because the change is already there:

```
No available patcher was able to apply patch patches/search_api-3630149-db-info.patch to drupal/search_api
```

Composer stops there, and the module may be left half installed, so don't leave it like that. That's your sign. Remove the patch from `composer.json`, delete its file from `patches/`, run `ddev composer patches-relock`, and commit. For a lenient module, remove it from the `allowed-list` too, once it has a release for your Drupal.

Check your patches now and then anyway: the issue's status (*Where Next?*) tells you whether the fix was accepted, changed, or turned down.

## Giving back

If you made a patch yourself, because nobody had posted a fix, post it. Open an issue, or comment on the one that's there, describe the problem and how to see it, and offer your fix as a merge request from the issue's fork. (drupal.org used to take patch files attached to issues; its documentation now calls that deprecated, and asks for merge requests.) *Where Next?* walks through it. The next person with the same problem will find it, and the maintainers can include it in the next release, and then you can remove the patch from your own site. That's how open source works: a fix shared once saves everyone else the trouble.

## Want to know more?

- [composer-patches](https://docs.cweagans.net/composer-patches/) documentation, and Drupal's own page on [patching with Composer](https://www.drupal.org/docs/develop/using-composer/manage-dependencies#patches).
- [composer-drupal-lenient](https://github.com/mglaman/composer-drupal-lenient).
- [Making a patch](https://www.drupal.org/docs/develop/git/using-git-to-contribute-to-drupal/making-a-drupal-patch-with-git) and [merge requests on drupal.org](https://www.drupal.org/docs/develop/git/using-gitlab-to-contribute-to-drupal/creating-merge-requests).

%% Author: checked 2026-11-14. The drupal.org documentation links were confirmed by a fetch (manage-dependencies has the `#patches` section). git.drupalcode.org served our script an HTML page instead of the diff for the `.diff` and `.patch` example addresses (bot protection, probably): open both in a browser before publication. The failed-patch message is from composer-patches 2 on the core site; `patches-repatch` output shows "Patching drupal/..." lines only. %%
