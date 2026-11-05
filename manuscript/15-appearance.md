# Appearance: Themes

%% Not started. The section below was moved here from Chapter 1 on 2026-11-04, to be reworked when we write this chapter. %%

## Core structure of a Drupal Theme
A Drupal theme is a collection of files in a folder, often under the `/themes/custom` for a custom-built theme or `/themes/contrib` for contributed ones. There is not really any difference between the two, except that contributed themes are normally not stored in a versioning system (rather than being controlled by Composer) but custom themes are, for obvious reasons. 

A minimal Drupal theme includes normally these components:
* `theme-name.info.yml` which defines the metadata of the theme. Name, description, regions of the theme, libraries to be included etc.
* `theme-name.libraries.yml` for CSS and JavaScript files to be loaded. 
* **Templates** (`.html.twig`) **files** that define the HTML markup for pages, blocks, nodes, menus and more. 
* `css/` and `js/` directories to hold style and script files
* An optional `theme-name.theme`, which is a PHP file for preprocess functions and logic that affects template variables.

Normally would the theming layer and theming be a separate book, but we will cover some general theming in this book.

