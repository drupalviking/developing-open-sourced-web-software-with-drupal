No, hooks are becoming less common in Drupal 11 compared to Drupal 8, and the trend is moving away from hooks toward more object-oriented approaches.
## The Evolution

### Drupal 7 and Earlier
- Everything was hooks - the primary extension mechanism
- Procedural code in .module files
### Drupal 8/9
- Transitional period - mix of hooks and OOP
- Many hooks still heavily used
- New alternatives introduced (events, plugins, services)
### Drupal 10/11
- Hooks are being deprecated - many converted to events
- OOP patterns are preferred
- Hooks still exist but considered "legacy" for many use cases
## What's Replacing Hooks?
### Event Subscribers (Replacing Most Hooks)

**OLD (Hook in .module file):**
  `<?php`
  `// my_module.module`

  `/**`
   `* Implements hook_user_login().`
   `*/`
  `function my_module_user_login($account) {`
    `\Drupal::logger('my_module')->notice('User @name logged in', [`
      `'@name' => $account->getAccountName(),`
    `]);`
  `}`

  **NEW (Event Subscriber):**
  `<?php`
  `// src/EventSubscriber/UserLoginSubscriber.php`

  `namespace Drupal\my_module\EventSubscriber;`

  `use Drupal\user\Event\UserLoginEvent;`
  `use Symfony\Component\EventDispatcher\EventSubscriberInterface;`
  `use Psr\Log\LoggerInterface;`

  `/**`
   `* Subscribes to user login events.`
   `*/`
  `class UserLoginSubscriber implements EventSubscriberInterface {`

    `public function __construct(`
      `private LoggerInterface $logger,`
    `) {}`

    `public static function getSubscribedEvents(): array {`
      `return [`
        `UserLoginEvent::EVENT_NAME => 'onUserLogin',`
      `];`
    `}`

    `public function onUserLogin(UserLoginEvent $event): void {`
      `$account = $event->getAccount();`
      `$this->logger->notice('User @name logged in', [`
        `'@name' => $account->getAccountName(),`
      `]);`
    `}`

  `}`

  **Service definition (my_module.services.yml):**
  `services:`
    `my_module.user_login_subscriber:`
      `class: Drupal\my_module\EventSubscriber\UserLoginSubscriber`
      `arguments: ['@logger.factory']`
      `tags:`
        `- { name: event_subscriber }`
### Plugins (Replacing hook_block_view, hook_field_widget, etc.)
**OLD (Hook):**
`/**`
   *`Implements hook_block_view().`
`*/`
`function my_module_block_view($delta = '') {`
  `if ($delta === 'my_block') {`
    `return [`
      `'subject' => t('My Block'),`
      `'content' => ['#markup' => 'Block content'],`
    `];`
  `}`
`}`

**NEW (Plugin):**
`<?php`
`// src/Plugin/Block/MyBlock.php`

`namespace Drupal\my_module\Plugin\Block;`

`use Drupal\Core\Block\BlockBase;`

`/**`
 `* Provides a 'My Block' block.`
 `*`
 `* @Block(`
 `*   id = "my_block",`
 `*   admin_label = @Translation("My Block"),`
 `*   category = @Translation("Custom"),`
 `* )`
 `*/`
`class MyBlock extends BlockBase {`

  `public function build(): array {`
    `return [`
      `'#markup' => $this->t('Block content'),`
    `];`
  `}`
`}`

### Services (Replacing Utility Hooks)

**OLD (Hook helper):**
`/**`
 * `Helper function to process data.`
`*/`
`function my_module_process_data($data) {`
  `// Business logic`
  `return $processed;`
`}`

**NEW (Service):**
`<?php`
`// src/Service/DataProcessor.php`

`namespace Drupal\my_module\Service;`

`/**`
 `* Service for processing data.`
 `*/`
`class DataProcessor implements DataProcessorInterface {`

  `public function processData(array $data): array {`
    `// Business logic`
    `return $processed;`
  `}`

`}`

### Entity Hooks → Event Subscribers

Many entity hooks are being converted to events:

`| Hook                  | Modern Alternative    |`
`|-----------------------|-----------------------|`
`| hook_entity_presave() | EntityEvents::presave |`
`| hook_entity_insert()  | EntityEvents::insert  |`
`| hook_entity_update()  | EntityEvents::update  |`
`| hook_entity_delete()  | EntityEvents::delete  |`
`| hook_entity_view()    | EntityEvents::view    |`

 **Example:**
 `<?php`

`namespace Drupal\my_module\EventSubscriber;`

`use Drupal\Core\Entity\EntityEvents;`
`use Drupal\Core\Entity\EntityInterface;`
`use Symfony\Component\EventDispatcher\EventSubscriberInterface;`
`use Drupal\Core\Entity\EntityEvent;`

`/**`
 `* Subscribes to entity events.`
 `*/`
`class EntitySubscriber implements EventSubscriberInterface {`

  `public static function getSubscribedEvents(): array {`
    `return [`
      `EntityEvents::presave => 'onEntityPresave',`
    `];`
  `}`

  `public function onEntityPresave(EntityEvent $event): void {`
    `$entity = $event->getEntity();`

    `if ($entity->getEntityTypeId() === 'node') {`
      `// Do something before node is saved`
    `}`
  `}`

`}`

### Hooks That Still Exist (But May Be Deprecated)

Some hooks are still around in Drupal 11 but have deprecation notices:

Form Alter Hooks (Still Common, But...)

`// Still works, still common`
`function my_module_form_alter(&$form, FormStateInterface $form_state, $form_id) {`
  `if ($form_id === 'node_article_form') {`
    `$form['title']['#description'] = t('Custom description');`
  `}`
`}`

Better approach: ***Form Event Subscriber or Form Alter Service***

Theme Hooks (Still Necessary)

`/**`
 * `Implements hook_theme().`
 `*/`
`function my_module_theme($existing, $type, $theme, $path) {`
  `return [`
    `'my_template' => [`
      `'variables' => ['data' => NULL],`
      `'template' => 'my-template',`
    `],`
  `];`
`}`
These are still required for defining templates.

Help Hook (Being Replaced)

`/**`
 * `Implements hook_help().`
`*/`
`function my_module_help($route_name, RouteMatchInterface $route_match) {`
  `if ($route_name === 'help.page.my_module') {`
    `return '<p>' . t('Help text') . '</p>';`
  `}`
`}`

Modern: Use help topics (YAML + Twig)

When to Still Use Hooks in Drupal 11

Hooks are still acceptable for:

1. Quick prototyping - Faster than creating full classes
2. Simple alterations - Form alters, render array changes
3. No event alternative exists - Some hooks don't have event replacements yet
4. Legacy module maintenance - Updating old code incrementally
5. Theme-related hooks - hook_theme(), hook_preprocess_HOOK()

Comparison Table

`| Use Case           | Drupal 7/8               | Drupal 11 Best Practice             |`
`|--------------------|--------------------------|-------------------------------------|`
`| User login action  | hook_user_login()        | UserLoginEvent subscriber           |`
`| Entity save action | hook_entity_presave()    | EntityEvents::presave subscriber    |`
`| Custom block       | hook_block_view()        | Block Plugin                        |`
`| Form alteration    | hook_form_alter()        | Form alter hook (still ok) or Event |`
`| Business logic     | Helper functions         | Service class                       |`
`| Custom field       | hook_field_widget_info() | Field Widget Plugin                 |`
`| Route modification | hook_menu()              | Routing YAML + Route subscriber     |`
`| Email alter        | hook_mail_alter()        | Email Event subscriber              |`

 
Why This Shift Matters

Benefits of OOP approach:

6. ✅ Dependency Injection - Properly inject services
7. ✅ Testability - Easy to unit test classes
8. ✅ Type Safety - Full PHP type hints and IDE support
9. ✅ Reusability - Services can be reused across the application
10. ✅ Maintainability - Clear separation of concerns
11. ✅ Performance - Better autoloading and caching
12. ✅ Modern PHP - Follows PSR standards

Drawbacks of hooks:

13. ❌ Global scope - Hard to test
14. ❌ No dependency injection - Must use \Drupal::service()
15. ❌ Procedural - Not object-oriented
16. ❌ Hard to debug - Function names scattered across .module files
17. ❌ Order dependency - Hook execution order can be unpredictable

The Future

Drupal is moving toward:
- Events everywhere - Most hooks will become events
- Pure OOP - Fewer procedural functions
- Symfony alignment - Following Symfony patterns more closely
- Clean .module files - Eventually just for legacy compatibility

Bottom Line

For new Drupal 11 development:
- ✅ Use Event Subscribers instead of entity/user hooks
- ✅ Use Plugins for blocks, fields, formatters
- ✅ Use Services for business logic
- ✅ Use Form classes instead of form builder functions
- ⚠️ Use hooks only when no alternative exists or for quick prototypes

Your .module file should be mostly empty in modern Drupal!