# Extending Drupal: Modules, Recipes, and Composer

## Composer

One of the bigger things that were added in 8.x and forward was to use composer as a package manager, but composer is PHP's de facto dependency manager. Think of it as a tool that keeps track of the libraries your PHP needs, automatically downloads them and ensures they all play nicely together.

It manages dependencies by declaring the libraries your project needs in a `composer.json` file. When run, it downloads the dependencies into a `vendor/` folder. It handles version constrains so that you can specify different version of libraries to work with the compatibility of your code. It Autoloads the code with PSR-4/PSR-0 compliant autoloader, so you don't need to `require`each  PHP file manually. Most modern PHP frameworks (Laravel, Symfony, Drupal) expect Composer for installation. 

Composer also keeps everything reproducible. When you run composer for the first time, it will "bake" your recipe (`composer.json`) into `composer.lock` file. In that file, the exact versions installed are stored so other developers (or production servers) get the same setup. That also means that just a single person needs to update the dependencies (by running `composer update`), others just need to install the latest dependencies (by running `composer install`)  respectively. That avoids almost entirely the "works on my machine" problem.
