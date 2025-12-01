Installing Xdebug used to be a daunting process. You would need to add extensions to PHP, configure all kinds of files and more **Rephrase this a bit! :-)** 

But Xdebug is already bundled with DDEV and Lando! So it's just the matter of enabling it and configure your IDE to listen to it.

## DDEV configuration
In order to enable Xdebug in DDEV you have two options:
1. Locate your `config.yml` file. This file is typically under the `.ddev` folder.
2. Edit the file. Add or modify the `xdebug_enabled` key to `true`.
3. Rebuild your DDEV environment by running `ddev restart`

You could also just run the command `ddev xdebug on` when your DDEV project is running. That will enable Xdebug just for now, but keeps it otherwise disabled, which is probably a better choice, since running Xdebug constantly has a huge performance impact.

## Lando configuration
In order to enable Xdebug in Lando, follow these steps:
1. Locate your `.lando.yml` file. This file is typically in the root directory of you Lando project.
2. Edit the file. Add or modify the `config` section to include `xdebug: true`. If you are using a recipe like Drupal, you might add it under the `config` key. Otherwise, you can add it under the `appserver`service definition.
3. Rebuild your Lando environment: Run `lando rebuild -y` to apply the changes.

After rebuilding, Xdebug will be active and ready to receive connections from your IDE for debugging. Remember that enabling Xdebug can impact performance, so you might want to toggle it on and off as needed using custom commands.

You can read more about configure Lando, Xdebug and PHPStorm here: https://docs.lando.dev/guides/lando-phpstorm.html

## Configure PHPStorm to listen to Xdebug
The next step is to configure PHPStorm to work with Xdebug. 

1. Go to **File -> Settings**
2. Navigate to **PHP -> Servers**. The best way is to enter **Servers** into the search window.
3. Press the **+** key to add a new server. 
4. Give it a name, although the name is irrelevant for functionality.
5. The host name should be `YOUR_PROJECT_NAME.ddev.site`. Port should be **80** and Debugger should be **Xdebug**
6. Check the **"Use path mappings (select if the server is remote or symlinks are used)"**
7. Press the **+** key to add these two path mappings:
   1. **PATH_TO_YOUR_PROJECT/web**  ->  **/var/www/html/web**
   2. **PATH_TO_YOUR_PROJECT/vendor** -> **/var/www/html/vendor**
8. Press **Apply** to accept the config.

Lastly, you need to search for the listening **"Bug"** and click it, to change it from off to on:

![1-debugging-off.png](screenshots/1-debugging-off.png) -> ![2-debugging-on.png](screenshots/2-debugging-on.png)

## Configure VSCode to listen to Xdebug
@TODO
