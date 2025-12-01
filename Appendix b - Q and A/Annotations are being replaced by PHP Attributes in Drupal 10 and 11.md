## The Evolution

### Drupal 8/9: Annotations (Doctrine Annotations)

`/**`
 * `Provides a 'Hello World' block.`
 `*`
 * `@Block(`
 *   `id = "hello_block",`
 *   `admin_label = @Translation("Hello Block"),`
 *   `category = @Translation("Custom"),`
 * `)`
 `*/
`class HelloBlock extends BlockBase {`
  `// ...`
}`
### Drupal 10/11: Attributes (PHP 8 Native)

`use Drupal\Core\Block\Attribute\Block;`

`#[Block(`
  `id: 'hello_block',`
  `admin_label: new TranslatableMarkup('Hello Block'),`
  `category: new TranslatableMarkup('Custom'),`
`)]`
`class HelloBlock extends BlockBase {`
  `// ...`
`}`

## Why the Change?

### Problems with Annotations

1. Not native PHP - Required Doctrine library
2. DocBlock comments - Mixed documentation with metadata
3. Performance - Slower to parse
4. No IDE support - IDEs treat them as comments
5. No type safety - Just strings in comments

### Benefits of Attributes

6. ✅ Native PHP 8+ - Built into the language
7. ✅ Actual code - Not comments, real PHP syntax
8. ✅ Type safety - PHP can validate them
9. ✅ IDE support - Full autocomplete and validation
10. ✅ Performance - Faster to parse
11. ✅ Cleaner syntax - Named parameters

## Current Status in Drupal 11

Both work, but attributes are preferred:

- ✅ Attributes are the recommended approach
- ⚠️ Annotations still work but deprecated
- 🔄 Core is transitioning to attributes
- 📅 Annotations will be removed in future Drupal versions

### Side-by-Side Comparison

#### Block Plugin

OLD (Annotations):
`<?php`

`namespace Drupal\mymodule\Plugin\Block;`

`use Drupal\Core\Block\BlockBase;`

`/**`
 `* Provides a custom block.`
 `*`
 `* @Block(`
 `*   id = "my_custom_block",`
 `*   admin_label = @Translation("My Custom Block"),`
 `*   category = @Translation("Custom Blocks"),`
 `* )`
 `*/`
`class MyCustomBlock extends BlockBase {`

  `public function build() {`
    `return [`
      `'#markup' => $this->t('Hello from block'),`
    `];`
  `}`

`}`

NEW (Attributes):
`<?php`

`namespace Drupal\mymodule\Plugin\Block;`

`use Drupal\Core\Block\BlockBase;`
`use Drupal\Core\Block\Attribute\Block;`
`use Drupal\Core\StringTranslation\TranslatableMarkup;`

`#[Block(`
  `id: 'my_custom_block',`
  `admin_label: new TranslatableMarkup('My Custom Block'),`
  `category: new TranslatableMarkup('Custom Blocks'),`
`)]`
`class MyCustomBlock extends BlockBase {`

  `public function build(): array {`
    `return [`
      `'#markup' => $this->t('Hello from block'),`
    `];`
  `}`

`}`

#### Field Formatter

OLD (Annotations):
`<?php`

`namespace Drupal\mymodule\Plugin\Field\FieldFormatter;`

`use Drupal\Core\Field\FormatterBase;`
`use Drupal\Core\Field\FieldItemListInterface;`

`/**`
 `* Plugin implementation of the 'custom_formatter' formatter.`
 `*`
 `* @FieldFormatter(`
 `*   id = "custom_formatter",`
 `*   label = @Translation("Custom Formatter"),`
 `*   field_types = {`
 `*     "string",`
 `*     "text"`
 `*   }`
 `* )`
 `*/`
`class CustomFormatter extends FormatterBase {`

  `public function viewElements(FieldItemListInterface $items, $langcode) {`
    `$elements = [];`
    `foreach ($items as $delta => $item) {`
      `$elements[$delta] = [`
        `'#markup' => strtoupper($item->value),`
      `];`
    `}`
    `return $elements;`
  `}`

`}`

NEW (Attributes):
`<?php`

`namespace Drupal\mymodule\Plugin\Field\FieldFormatter;`

`use Drupal\Core\Field\FormatterBase;`
`use Drupal\Core\Field\FieldItemListInterface;`
`use Drupal\Core\Field\Attribute\FieldFormatter;`
`use Drupal\Core\StringTranslation\TranslatableMarkup;`

`#[FieldFormatter(`
  `id: 'custom_formatter',`
  `label: new TranslatableMarkup('Custom Formatter'),`
  `field_types: [`
    `'string',`
    `'text',`
  `],`
`)]`
`class CustomFormatter extends FormatterBase {`

  `public function viewElements(FieldItemListInterface $items, $langcode): array {`
    `$elements = [];`
    `foreach ($items as $delta => $item) {`
      `$elements[$delta] = [`
        `'#markup' => strtoupper($item->value),`
      `];`
    `}`
    `return $elements;`
  `}`

`}`

#### Field Widget

OLD (Annotations):
`/**`
 * `Plugin implementation of the 'custom_widget' widget.`
 `*`
 * `@FieldWidget(`
 *   `id = "custom_widget",`
 *   `label = @Translation("Custom Widget"),`
 *   `field_types = {`
 *     `"string"`
 *   `}`
 * `)`
 `*/`
`class CustomWidget extends WidgetBase {`
  `// ...`
`}`

NEW (Attributes):
`use Drupal\Core\Field\Attribute\FieldWidget;`

`#[FieldWidget(`
  `id: 'custom_widget',`
  `label: new TranslatableMarkup('Custom Widget'),`
  `field_types: [`
    `'string',`
  `],`
`)]`
`class CustomWidget extends WidgetBase {`
  `// ...`
`}`

#### Action Plugin

OLD (Annotations):
`/**`
 * `Provides a custom action.`
 `*`
 * `@Action(`
 *   `id = "custom_action",`
 *   `label = @Translation("Custom Action"),`
 *   `type = "node"`
 * `)`
 `*/`
`class CustomAction extends ActionBase {`
  `// ...`
`}`

NEW (Attributes):
`use Drupal\Core\Action\Attribute\Action;`

`#[Action(`
  `id: 'custom_action',`
  `label: new TranslatableMarkup('Custom Action'),`
  `type: 'node',`
`)]`
`class CustomAction extends ActionBase {`
  `// ...`
`}`

#### Views Plugin

OLD (Annotations):
`/**`
 * `Custom views field plugin.`
 `*`
 * `@ViewsField("custom_field")`
 `*/`
`class CustomField extends FieldPluginBase {`
  `// ...`
`}`

NEW (Attributes):
`use Drupal\views\Attribute\ViewsField;`

`#[ViewsField("custom_field")]`
`class CustomField extends FieldPluginBase {`
  `// ...`
`}`

## Key Syntax Differences

### Translation

Annotations:
`@Translation("Some text")`

Attributes:
`new TranslatableMarkup('Some text')`

### Arrays

Annotations:
`field_types = {`
  `"string",`
  `"text"`
`}`

Attributes:
`field_types: [`
  `'string',`
  `'text',`
`]`

### Named Parameters

Annotations:
`@Block(`
  `id = "my_block",`
  `admin_label = @Translation("My Block")`
`)`

Attributes:
`#[Block(`
  `id: 'my_block',`
  `admin_label: new TranslatableMarkup('My Block'),`
`)]`

Note: Attributes use : instead of =

## Common Attribute Classes in Drupal

`| Plugin Type     | Attribute Class   | Namespace                                  |`
`|-----------------|-------------------|--------------------------------------------|`
`| Block           | #[Block]          | Drupal\Core\Block\Attribute\Block          |`
`| Field Formatter | #[FieldFormatter] | Drupal\Core\Field\Attribute\FieldFormatter |`
`| Field Widget    | #[FieldWidget]    | Drupal\Core\Field\Attribute\FieldWidget    |`
`| Field Type      | #[FieldType]      | Drupal\Core\Field\Attribute\FieldType      |`
`| Action          | #[Action]         | Drupal\Core\Action\Attribute\Action        |`
`| Condition       | #[Condition]      | Drupal\Core\Condition\Attribute\Condition  |`
`| Views Field     | #[ViewsField]     | Drupal\views\Attribute\ViewsField          |`
`| Views Filter    | #[ViewsFilter]    | Drupal\views\Attribute\ViewsFilter         |`

## Migration Guide

### Step 1: Add Use Statements

`// Remove old annotations, add new imports`
`use Drupal\Core\Block\Attribute\Block;`
`use Drupal\Core\StringTranslation\TranslatableMarkup;`

### Step 2: Replace DocBlock

Before:
`/**`
 * `Provides a block.`
 `*`
 * `@Block(`
 *   `id = "my_block",`
 *   `admin_label = @Translation("My Block"),`
 * `)`
 `*/`
`class MyBlock extends BlockBase {`

After:
`/**`
 * `Provides a block.`
 `*/`
`#[Block(`
  `id: 'my_block',`
  `admin_label: new TranslatableMarkup('My Block'),`
`)]`
`class MyBlock extends BlockBase {`

### Step 3: Update Syntax

- Change = to :
- Change @Translation() to new TranslatableMarkup()
- Change {} to [] for arrays
- Use single or double quotes (doesn't matter)

### Real-World Complete Example

#### Full Block Plugin with Attributes:

?php`

`namespace Drupal\mymodule\Plugin\Block;`

`use Drupal\Core\Block\BlockBase;`
`use Drupal\Core\Block\Attribute\Block;`
`use Drupal\Core\Form\FormStateInterface;`
`use Drupal\Core\Plugin\ContainerFactoryPluginInterface;`
`use Drupal\Core\StringTranslation\TranslatableMarkup;`
`use Symfony\Component\DependencyInjection\ContainerInterface;`
`use Psr\Log\LoggerInterface;`

`/**`
 `* Provides a configurable welcome block.`
 `*/`
`#[Block(`
  `id: 'welcome_block',`
  `admin_label: new TranslatableMarkup('Welcome Block'),`
  `category: new TranslatableMarkup('Custom'),`
`)]`
`class WelcomeBlock extends BlockBase implements ContainerFactoryPluginInterface {`

  `public function __construct(`
    `array $configuration,`
    `$plugin_id,`
    `$plugin_definition,`
    `private LoggerInterface $logger,`
  `) {`
    `parent::__construct($configuration, $plugin_id, $plugin_definition);`
  `}`

  `public static function create(ContainerInterface $container, array $configuration, $plugin_id, $plugin_definition): self {`
    `return new self(`
      `$configuration,`
      `$plugin_id,`
      `$plugin_definition,`
      `$container->get('logger.factory')->get('mymodule'),`
    `);`
  `}`

  `public function defaultConfiguration(): array {`
    `return [`
      `'welcome_text' => $this->t('Welcome to our site!'),`
    `] + parent::defaultConfiguration();`
  `}`

  `public function blockForm($form, FormStateInterface $form_state): array {`
    `$form['welcome_text'] = [`
      `'#type' => 'textfield',`
      `'#title' => $this->t('Welcome Text'),`
      `'#default_value' => $this->configuration['welcome_text'],`
    `];`
    `return $form;`
  `}`

  `public function blockSubmit($form, FormStateInterface $form_state): void {`
    `$this->configuration['welcome_text'] = $form_state->getValue('welcome_text');`
  `}`

  `public function build(): array {`
    `return [`
      `'#markup' => $this->configuration['welcome_text'],`
      `'#cache' => [`
        `'max-age' => 3600,`
      `],`
    `];`
  `}`

`}`

## When to Use Each

### Use Attributes (Recommended)

✅ All new Drupal 11 code
✅ PHP 8.1+ projects
✅ New plugins (blocks, fields, formatters, etc.)
✅ When refactoring existing code

### Still Using Annotations (Legacy)

⚠️ Maintaining Drupal 9 compatibility
⚠️ Existing code not yet migrated
⚠️ Legacy modules

Checking Drupal Core's Approach

Look at core plugins to see the current standard:

# See how core does it
`cat web/core/modules/block/src/Plugin/Block/PageTitleBlock.php`

Most core plugins in Drupal 11 use attributes.

IDE Support

Modern IDEs (PHPStorm, VS Code) provide:

- ✅ Autocomplete for attribute parameters
- ✅ Type checking
- ✅ Navigation to attribute class definitions
- ✅ Validation of required parameters

This doesn't work with annotations (they're just comments).

## Summary

`| Aspect      | Annotations      | Attributes               |`
`|-------------|------------------|--------------------------|`
`| Status      | Deprecated       | Recommended              |`
`| Syntax      | @Block(id = "x") | #[Block(id: 'x')]        |`
`| Translation | @Translation()   | new TranslatableMarkup() |`
`| Performance | Slower           | Faster                   |`
`| Type Safety | No               | Yes                      |`
`| IDE Support | Limited          | Full                     |`
`| PHP Version | Any              | 8.0+                     |`
`| Future      | Being removed    | Standard going forward   |`

Bottom Line for Drupal 11

For all new code:
- ✅ Use PHP Attributes
- ✅ Import the attribute classes
- ✅ Use new TranslatableMarkup() for translations
- ✅ Use named parameters with :
- ✅ Follow Drupal 11 core examples

Annotations still work but are on their way out!