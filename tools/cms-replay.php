<?php

/**
 * @file
 * Builds parts of the club on the Drupal CMS test site, the way each chapter's "On Drupal CMS" section does by hand.
 *
 * tools/screenshots.py replays the Drupal CMS site chapter by chapter (PROJECT-LOG, Decisions: "The club on Drupal
 * CMS, the grilling round"). It does by hand, in the browser, what the screenshots show, and calls this script for
 * the rest: the same settings a reader would choose in the forms, made with Drupal's API. Each step is named, so a
 * sequence can stop between two of them, to photograph a form before it's saved.
 *
 * Usage, from the Drupal CMS site's folder (DDEV's container sees only that folder, so copy the script there):
 *   ddev drush php:script cms-replay.php -- STEP [STEP...]
 */

use Drupal\Core\Entity\Entity\EntityFormDisplay;
use Drupal\Core\Entity\Entity\EntityViewDisplay;
use Drupal\field\Entity\FieldConfig;
use Drupal\field\Entity\FieldStorageConfig;
use Drupal\node\Entity\Node;
use Drupal\node\Entity\NodeType;
use Drupal\workflows\Entity\Workflow;

/**
 * Adds a field to a bundle, as Field UI does: storage (if new), field, and a place on the default form and display.
 */
function replay_field(string $entity_type, string $bundle, string $name, string $type, string $label, array $field = [], array $storage = [], ?string $widget = NULL, ?string $formatter = NULL): void {
  if (!FieldStorageConfig::loadByName($entity_type, $name)) {
    FieldStorageConfig::create([
      'entity_type' => $entity_type,
      'field_name' => $name,
      'type' => $type,
    ] + $storage)->save();
    // Something on Drupal CMS has already cached the field storage definitions in this request; without this,
    // the field below says its storage doesn't exist.
    \Drupal::service('entity_field.manager')->clearCachedFieldDefinitions();
  }
  if (!FieldConfig::loadByName($entity_type, $bundle, $name)) {
    FieldConfig::create([
      'entity_type' => $entity_type,
      'bundle' => $bundle,
      'field_name' => $name,
      'label' => $label,
    ] + $field)->save();
  }
  // Field UI puts a new field at the end of the default form and the default display, with the type's default
  // widget and formatter (or the ones given).
  $field_type = \Drupal::service('plugin.manager.field.field_type')->getDefinition($type);
  $form = EntityFormDisplay::load("$entity_type.$bundle.default") ?? EntityFormDisplay::create([
    'targetEntityType' => $entity_type, 'bundle' => $bundle, 'mode' => 'default', 'status' => TRUE,
  ]);
  if (!$form->getComponent($name)) {
    $form->setComponent($name, ['type' => $widget ?? $field_type['default_widget'], 'weight' => replay_last_weight($form) + 1])->save();
  }
  $view = EntityViewDisplay::load("$entity_type.$bundle.default") ?? EntityViewDisplay::create([
    'targetEntityType' => $entity_type, 'bundle' => $bundle, 'mode' => 'default', 'status' => TRUE,
  ]);
  if (!$view->getComponent($name)) {
    $view->setComponent($name, ['type' => $formatter ?? $field_type['default_formatter'], 'label' => 'above', 'weight' => replay_last_weight($view) + 1])->save();
  }
}

function replay_last_weight($display): int {
  $weights = array_map(fn($c) => $c['weight'] ?? 0, $display->getComponents());
  return $weights ? (int) max($weights) : 0;
}

/**
 * A content type, as the Add content type form makes it, with no menus available.
 */
function replay_node_type(string $type, string $name, string $description, bool $submitted): void {
  if (NodeType::load($type)) {
    return;
  }
  $node_type = NodeType::create([
    'type' => $type,
    'name' => $name,
    'description' => $description,
    'new_revision' => TRUE,
    'display_submitted' => $submitted,
    'preview_mode' => 1,
  ]);
  $node_type->setThirdPartySetting('menu_ui', 'available_menus', []);
  $node_type->setThirdPartySetting('menu_ui', 'parent', '');
  $node_type->save();
  // As the form does: the default form and display, with the title and the base fields Field UI shows.
  \Drupal::service('entity_display.repository')->getFormDisplay('node', $type)->save();
  \Drupal::service('entity_display.repository')->getViewDisplay('node', $type)->save();
}

function replay_workflow_add(string $bundle): void {
  $workflow = Workflow::load('basic_editorial');
  $workflow->getTypePlugin()->addEntityTypeAndBundle('node', $bundle);
  $workflow->save();
}

/**
 * Chapter 7: the Hike content type, before its description.
 */
function replay_ch07_hike_type(): void {
  replay_node_type('hike', 'Hike', 'A hike or photo walk the club organizes, with its date, meeting place, distance and difficulty.', FALSE);
}

/**
 * Chapter 7: re-use Content (field_content) on Hike, as Description.
 */
function replay_ch07_hike_description(): void {
  replay_field('node', 'hike', 'field_content', 'text_long', 'Description', [
    'description' => 'What the hike is like: the route, the views, and what to bring.',
  ] + replay_field_settings_from('node', 'page', 'field_content'));
}

/**
 * Settings of a field on another bundle (Field UI's re-use copies them), without label, description and bundle.
 */
function replay_field_settings_from(string $entity_type, string $bundle, string $name): array {
  $field = FieldConfig::loadByName($entity_type, $bundle, $name);
  return [
    'required' => $field->isRequired(),
    'settings' => $field->getSettings(),
    'third_party_settings' => $field->get('third_party_settings'),
  ];
}

/**
 * Chapter 7: the hike's own fields, the form order, and the workflow.
 */
function replay_ch07_hike_fields(): void {
  replay_field('node', 'hike', 'field_date', 'datetime', 'Date',
    ['description' => 'The day and time we meet.', 'required' => TRUE],
    ['settings' => ['datetime_type' => 'datetime']]);
  replay_field('node', 'hike', 'field_meeting_place', 'string', 'Meeting place',
    ['description' => 'Where we meet, for example: Flotterstone car park.', 'required' => TRUE]);
  replay_field('node', 'hike', 'field_distance', 'decimal', 'Distance',
    ['description' => 'The length of the walk, in kilometers.', 'settings' => ['min' => 0, 'max' => NULL, 'prefix' => '', 'suffix' => ' km']],
    ['settings' => ['precision' => 10, 'scale' => 1]]);
  replay_field('node', 'hike', 'field_difficulty', 'list_string', 'Difficulty',
    ['description' => 'Easy: short and flat. Moderate: some climbing. Hard: long, steep, or rough ground.', 'required' => TRUE],
    ['settings' => ['allowed_values' => ['easy' => 'Easy', 'moderate' => 'Moderate', 'hard' => 'Hard']]]);
  replay_field('node', 'hike', 'field_hike_leader', 'entity_reference', 'Hike leader',
    ['description' => 'The member who leads the hike.', 'settings' => ['handler' => 'default:user', 'handler_settings' => [
      'target_bundles' => NULL, 'sort' => ['field' => 'name', 'direction' => 'ASC'], 'auto_create' => FALSE,
      'filter' => ['type' => '_none'], 'include_anonymous' => FALSE,
    ]]],
    ['settings' => ['target_type' => 'user']]);
  // Manage form display: the order an editor thinks in, radio buttons and a select list.
  $form = EntityFormDisplay::load('node.hike.default');
  $order = ['title', 'field_date', 'field_meeting_place', 'field_distance', 'field_difficulty', 'field_hike_leader', 'field_content'];
  foreach ($order as $weight => $name) {
    $component = $form->getComponent($name) ?? [];
    $component['weight'] = $weight;
    if ($name == 'field_difficulty') {
      $component['type'] = 'options_buttons';
      $component['settings'] = [];
    }
    if ($name == 'field_hike_leader') {
      $component['type'] = 'options_select';
      $component['settings'] = [];
    }
    $form->setComponent($name, $component);
  }
  $form->save();
  replay_workflow_add('hike');
}

/**
 * Chapter 7: the News content type, with Content re-used, and the first news item.
 */
function replay_ch07_news(): void {
  replay_node_type('news', 'News', 'News from the club: trip reports, competition results, and announcements.', TRUE);
  replay_field('node', 'news', 'field_content', 'text_long', 'Content', [
    'description' => '',
  ] + replay_field_settings_from('node', 'page', 'field_content'));
  replay_workflow_add('news');
  if (!\Drupal::entityQuery('node')->accessCheck(FALSE)->condition('title', 'The club has a website')->execute()) {
    Node::create([
      'type' => 'news',
      'title' => 'The club has a website',
      'uid' => 1,
      'field_content' => [
        'value' => "<p>Lens &amp; Trail finally has a website of its own. From now on, you'll find the hike program, news from the club, and the members' best photos here.</p><p>The website is new, and we're building it as we go. If something is missing or wrong, tell the secretary.</p>",
        'format' => 'content_format',
      ],
      'moderation_state' => 'published',
    ])->save();
  }
}

/**
 * A view display with exactly these components, everything else hidden (made if the view mode isn't enabled yet).
 */
function replay_display(string $bundle, string $mode, array $components): void {
  $display = EntityViewDisplay::load("node.$bundle.$mode") ?? EntityViewDisplay::create([
    'targetEntityType' => 'node', 'bundle' => $bundle, 'mode' => $mode, 'status' => TRUE,
  ]);
  $display->setStatus(TRUE);
  foreach (array_keys($display->getComponents()) as $name) {
    if (!isset($components[$name])) {
      $display->removeComponent($name);
    }
  }
  $weight = 0;
  foreach ($components as $name => $component) {
    $display->setComponent($name, $component + ['weight' => $weight++, 'region' => 'content']);
  }
  $display->save();
}

/**
 * Chapter 8: Hike's Default, Teaser and Card displays, the Day, date and time format, and News's Teaser.
 */
function replay_ch08_displays(): void {
  if (!\Drupal\Core\Datetime\Entity\DateFormat::load('day_date_and_time')) {
    \Drupal\Core\Datetime\Entity\DateFormat::create([
      'id' => 'day_date_and_time', 'label' => 'Day, date and time', 'pattern' => 'l, j F Y \a\t H:i',
    ])->save();
  }
  $date = ['type' => 'datetime_default', 'label' => 'inline', 'settings' => ['timezone_override' => '', 'format_type' => 'day_date_and_time']];
  $distance = ['type' => 'number_decimal', 'label' => 'inline', 'settings' => ['thousand_separator' => '', 'decimal_separator' => '.', 'scale' => 1, 'prefix_suffix' => TRUE]];
  $difficulty = ['type' => 'list_default', 'label' => 'inline', 'settings' => []];
  replay_display('hike', 'default', [
    'content_moderation_control' => [],
    'field_date' => $date,
    'field_meeting_place' => ['type' => 'string', 'label' => 'inline', 'settings' => ['link_to_entity' => FALSE]],
    'field_distance' => $distance,
    'field_difficulty' => $difficulty,
    'field_hike_leader' => ['type' => 'entity_reference_label', 'label' => 'inline', 'settings' => ['link' => FALSE]],
    'field_content' => ['type' => 'text_default', 'label' => 'hidden', 'settings' => []],
  ]);
  replay_display('hike', 'teaser', [
    'content_moderation_control' => [],
    'links' => [],
    'field_date' => $date,
    'field_distance' => $distance,
    'field_difficulty' => $difficulty,
    'field_content' => ['type' => 'text_trimmed', 'label' => 'hidden', 'settings' => ['trim_length' => 200]],
  ]);
  replay_display('hike', 'card', [
    'content_moderation_control' => [],
    'field_date' => ['label' => 'hidden'] + $date,
    'field_difficulty' => ['label' => 'hidden'] + $difficulty,
  ]);
  replay_display('news', 'teaser', [
    'content_moderation_control' => [],
    'links' => [],
    'field_content' => ['type' => 'text_trimmed', 'label' => 'hidden', 'settings' => ['trim_length' => 300]],
  ]);
}

/**
 * Chapter 9: the credit fields on Image media, on both of its forms.
 */
function replay_ch09_credits(): void {
  replay_field('media', 'image', 'field_photographer', 'string', 'Photographer',
    ['description' => "The photographer's name, as they want to be credited."]);
  replay_field('media', 'image', 'field_license', 'list_string', 'License',
    ['description' => "The license the photo is published under. Use only photos you're allowed to publish.", 'required' => TRUE],
    ['settings' => ['allowed_values' => [
      'cc_by_sa_4_0' => 'CC BY-SA 4.0',
      'cc_by_sa_2_0' => 'CC BY-SA 2.0',
      'cc_by_4_0' => 'CC BY 4.0',
      'cc0' => 'CC0',
      'all_rights_reserved_used_with_permission' => 'All rights reserved, used with permission',
    ]]]);
  replay_field('media', 'image', 'field_source', 'link', 'Source',
    ['description' => 'Where the photo comes from, such as its page on Wikimedia Commons.', 'settings' => ['title' => 1, 'link_type' => 16]]);
  // Both forms: the name under the image, then the credits.
  foreach (['default', 'media_library'] as $mode) {
    $form = EntityFormDisplay::load("media.image.$mode");
    $image = $form->getComponent('field_media_image')['weight'] ?? 0;
    $form->setComponent('name', ['type' => 'string_textfield', 'weight' => $image + 1, 'settings' => ['size' => 60, 'placeholder' => '']]);
    foreach (['field_photographer' => 'string_textfield', 'field_license' => 'options_select', 'field_source' => 'link_default'] as $i => $widget) {
      $form->setComponent($i, ['type' => $widget, 'weight' => $image + 2 + array_search($i, ['field_photographer', 'field_license', 'field_source'])]);
    }
    $form->save();
  }
}

/**
 * The club's photos, from examples/photos (copied into the site by tools/screenshots.py, see cms_replay).
 */
const REPLAY_PHOTOS = [
  'turnhouse-hill-glencorse.jpg' => ['Turnhouse Hill across Glencorse Reservoir', 'Turnhouse Hill seen across Glencorse Reservoir, with a rowing boat at the landing stage', 'dave souza', 'cc_by_sa_4_0', 'https://commons.wikimedia.org/wiki/File:Glencorse_Reservoir,_Turnhouse_Hill.jpg'],
  'edinburgh-skyline.jpg' => ["Edinburgh's Old Town from Calton Hill", "Edinburgh's Old Town and the castle seen from Calton Hill, with trees in front", 'Jim Barton', 'cc_by_sa_2_0', 'https://commons.wikimedia.org/wiki/File:Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg'],
  'carnethy-from-turnhouse.jpg' => ['Carnethy Hill from Turnhouse Hill', 'The path down from Turnhouse Hill, with Carnethy Hill rising behind it', 'Jim Barton', 'cc_by_sa_2_0', 'https://commons.wikimedia.org/wiki/File:Carnethy_Hill_from_Turnhouse_Hill_-_geograph.org.uk_-_6273248.jpg'],
  'carnethy-hill-views.jpg' => ['The view from Carnethy Hill', 'Rolling green hills under a cloudy sky, seen from the stony top of Carnethy Hill', "Alan O'Dowd", 'cc_by_sa_2_0', 'https://commons.wikimedia.org/wiki/File:Carnethy_Hill_views_-_geograph.org.uk_-_4185120.jpg'],
  'glencorse-reservoir-portrait.jpg' => ['Glencorse Reservoir from the hillside', 'Glencorse Reservoir between the hills, seen from a grassy slope with two trees', 'Jaroslaw Musialkowski', 'cc_by_sa_4_0', 'https://commons.wikimedia.org/wiki/File:Pentland_Hills_-_Glencorse_Reservoir.jpg'],
  'pentland-hills-winter.jpg' => ['A burn in the Pentland Hills in winter', 'A stream running through a snowy valley in the Pentland Hills', 'Bops92', 'cc_by_sa_4_0', 'https://commons.wikimedia.org/wiki/File:Pentland_hills_winter.jpg'],
];

/**
 * A photo as a media item, made once (found again by its name).
 */
function replay_photo(string $file): int {
  [$name, $alt, $photographer, $license, $source] = REPLAY_PHOTOS[$file];
  $storage = \Drupal::entityTypeManager()->getStorage('media');
  if ($found = $storage->loadByProperties(['bundle' => 'image', 'name' => $name])) {
    return (int) reset($found)->id();
  }
  $directory = 'public://' . date('Y-m');
  \Drupal::service('file_system')->prepareDirectory($directory, \Drupal\Core\File\FileSystemInterface::CREATE_DIRECTORY);
  $uri = \Drupal::service('file_system')->copy(DRUPAL_ROOT . "/cms-replay-photos/$file", "$directory/$file", \Drupal\Core\File\FileExists::Rename);
  $file_entity = \Drupal\file\Entity\File::create(['uri' => $uri, 'uid' => 1, 'status' => 1]);
  $file_entity->save();
  $media = $storage->create([
    'bundle' => 'image',
    'name' => $name,
    'uid' => 1,
    'field_media_image' => ['target_id' => $file_entity->id(), 'alt' => $alt],
    'field_photographer' => $photographer,
    'field_license' => $license,
    'field_source' => ['uri' => $source, 'title' => 'Wikimedia Commons'],
  ]);
  $media->save();
  return (int) $media->id();
}

/**
 * The credits, inline, on a media view display (after the image).
 */
function replay_credits_on(string $mode): void {
  $display = EntityViewDisplay::load("media.image.$mode");
  $weight = ($display->getComponent('field_media_image')['weight'] ?? 0) + 1;
  $display->setComponent('field_photographer', ['type' => 'string', 'label' => 'inline', 'settings' => ['link_to_entity' => FALSE], 'weight' => $weight++]);
  $display->setComponent('field_license', ['type' => 'list_default', 'label' => 'inline', 'settings' => [], 'weight' => $weight++]);
  $display->setComponent('field_source', ['type' => 'link', 'label' => 'inline', 'settings' => ['trim_length' => 80, 'url_only' => FALSE, 'url_plain' => FALSE, 'rel' => '', 'target' => ''], 'weight' => $weight++]);
  $display->save();
}

/**
 * Chapter 9: the first photo, a Photo field on Hike (and News), shown with Drupal CMS's 16:9 Wide view mode.
 */
function replay_ch09_photo_field(): void {
  $settings = ['handler' => 'default:media', 'handler_settings' => [
    'target_bundles' => ['image' => 'image'], 'sort' => ['field' => '_none', 'direction' => 'ASC'], 'auto_create' => FALSE, 'auto_create_bundle' => '',
  ]];
  foreach (['hike', 'news'] as $bundle) {
    replay_field('node', $bundle, 'field_photo', 'entity_reference', 'Photo',
      ['description' => $bundle == 'hike' ? "A photo of the hike's area, shown at the top of the hike." : '', 'settings' => $settings],
      ['settings' => ['target_type' => 'media']], 'media_library_widget', 'entity_reference_entity_view');
    $display = EntityViewDisplay::load("node.$bundle.default");
    $display->setComponent('field_photo', ['type' => 'entity_reference_entity_view', 'label' => 'hidden', 'settings' => ['view_mode' => '16_9_wide', 'link' => FALSE], 'weight' => -10]);
    $display->save();
  }
  replay_credits_on('16_9_wide');
  $nodes = \Drupal::entityTypeManager()->getStorage('node');
  foreach (['Turnhouse Hill and Carnethy Hill' => 'turnhouse-hill-glencorse.jpg', 'The club has a website' => 'edinburgh-skyline.jpg'] as $title => $file) {
    $node = current($nodes->loadByProperties(['title' => $title]));
    if ($node->get('field_photo')->isEmpty()) {
      $node->set('field_photo', replay_photo($file));
      $node->setNewRevision();
      $node->setRevisionLogMessage('Added a photo.');
      $node->save();
    }
  }
}

/**
 * Chapter 9: the Album view mode of Image media, the Gallery content type, and the first album.
 */
function replay_ch09_gallery(): void {
  if (!\Drupal\Core\Entity\Entity\EntityViewMode::load('media.album')) {
    \Drupal\Core\Entity\Entity\EntityViewMode::create(['id' => 'media.album', 'label' => 'Album', 'targetEntityType' => 'media', 'cache' => TRUE])->save();
  }
  $album = EntityViewDisplay::load('media.image.album') ?? EntityViewDisplay::create([
    'targetEntityType' => 'media', 'bundle' => 'image', 'mode' => 'album', 'status' => TRUE,
  ]);
  foreach (array_keys($album->getComponents()) as $name) {
    $album->removeComponent($name);
  }
  $album->setComponent('field_media_image', ['type' => 'responsive_image', 'label' => 'hidden', 'settings' => ['responsive_image_style' => 'uncropped_large', 'image_link' => '', 'image_loading' => ['attribute' => 'lazy']], 'weight' => 0]);
  $album->save();
  replay_credits_on('album');

  replay_node_type('gallery', 'Gallery', "A photo album from one of the club's hikes or photo evenings.", FALSE);
  replay_field('node', 'gallery', 'field_content', 'text_long', 'Description', [
    'description' => 'What the album is about: where and when, and anything worth knowing.',
  ] + replay_field_settings_from('node', 'page', 'field_content'));
  replay_field('node', 'gallery', 'field_photos', 'entity_reference', 'Photos',
    ['description' => 'Upload several photos at once: select them all in the file window.', 'required' => TRUE, 'settings' => ['handler' => 'default:media', 'handler_settings' => [
      'target_bundles' => ['image' => 'image'], 'sort' => ['field' => '_none', 'direction' => 'ASC'], 'auto_create' => FALSE, 'auto_create_bundle' => '',
    ]]],
    ['settings' => ['target_type' => 'media'], 'cardinality' => -1], 'media_library_widget', 'entity_reference_entity_view');
  replay_field('node', 'gallery', 'field_hike', 'entity_reference', 'Hike',
    ['description' => "The hike the photos are from, if they're from one.", 'settings' => ['handler' => 'default:node', 'handler_settings' => [
      'target_bundles' => ['hike' => 'hike'], 'sort' => ['field' => '_none', 'direction' => 'ASC'], 'auto_create' => FALSE, 'auto_create_bundle' => '',
    ]]],
    ['settings' => ['target_type' => 'node']]);
  replay_display('gallery', 'default', [
    'content_moderation_control' => [],
    'field_hike' => ['type' => 'entity_reference_label', 'label' => 'inline', 'settings' => ['link' => TRUE]],
    'field_content' => ['type' => 'text_default', 'label' => 'hidden', 'settings' => []],
    'field_photos' => ['type' => 'entity_reference_entity_view', 'label' => 'hidden', 'settings' => ['view_mode' => 'album', 'link' => FALSE]],
  ]);
  replay_workflow_add('gallery');

  $nodes = \Drupal::entityTypeManager()->getStorage('node');
  if (!$nodes->loadByProperties(['title' => 'Pentlands, 21 November'])) {
    $hike = current($nodes->loadByProperties(['title' => 'Turnhouse Hill and Carnethy Hill']));
    $photos = array_map('replay_photo', ['carnethy-from-turnhouse.jpg', 'carnethy-hill-views.jpg', 'glencorse-reservoir-portrait.jpg', 'pentland-hills-winter.jpg']);
    Node::create([
      'type' => 'gallery',
      'title' => 'Pentlands, 21 November',
      'uid' => 1,
      'field_content' => ['value' => '<p>Our first hike with the new website: Turnhouse Hill and Carnethy Hill, in sun, wind and, near the top, a little snow.</p>', 'format' => 'content_format'],
      'field_hike' => $hike->id(),
      'field_photos' => $photos,
      'moderation_state' => 'published',
    ])->save();
  }
}

$steps = $extra ?? [];
if (!$steps) {
  throw new \InvalidArgumentException('Name one or more steps, such as ch07_hike_type.');
}
foreach ($steps as $step) {
  $function = "replay_$step";
  if (!function_exists($function)) {
    throw new \InvalidArgumentException("No step called $step.");
  }
  $function();
  echo "Done: $step\n";
}
