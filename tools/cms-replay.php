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
    // The same, for entities of this bundle made later in the same request.
    \Drupal::service('entity_field.manager')->clearCachedFieldDefinitions();
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

/**
 * A vocabulary, with its terms: [name => [parent name or '', weight, description]].
 */
function replay_vocabulary(string $vid, string $name, string $description, array $terms): void {
  if (!\Drupal\taxonomy\Entity\Vocabulary::load($vid)) {
    \Drupal\taxonomy\Entity\Vocabulary::create(['vid' => $vid, 'name' => $name, 'description' => $description, 'new_revision' => FALSE])->save();
  }
  $storage = \Drupal::entityTypeManager()->getStorage('taxonomy_term');
  foreach ($terms as $term => [$parent, $weight, $text]) {
    if ($storage->loadByProperties(['vid' => $vid, 'name' => $term])) {
      continue;
    }
    $parent_id = $parent ? (int) current($storage->loadByProperties(['vid' => $vid, 'name' => $parent]))->id() : 0;
    $storage->create([
      'vid' => $vid, 'name' => $term, 'weight' => $weight, 'parent' => $parent_id,
      'description' => $text ? ['value' => "<p>$text</p>", 'format' => 'content_format'] : NULL,
    ])->save();
  }
}

function replay_term(string $vid, string $name): int {
  return (int) current(\Drupal::entityTypeManager()->getStorage('taxonomy_term')->loadByProperties(['vid' => $vid, 'name' => $name]))->id();
}

/**
 * Chapter 10: the Areas vocabulary, with a Photo field on its terms.
 */
function replay_ch10_areas(): void {
  replay_vocabulary('areas', 'Areas', 'Regions, and the hills and places in them.', [
    'Pentland Hills' => ['', 0, "A range of hills south-west of Edinburgh, most of it a regional park. The club's favourite: a bus from the city centre takes you to the foot of the hills."],
    'Carnethy Hill' => ['Pentland Hills', 0, ''],
    'Glencorse Reservoir' => ['Pentland Hills', 1, ''],
    'Turnhouse Hill' => ['Pentland Hills', 2, ''],
    'East Lothian' => ['', 2, 'The coast and hills east of Edinburgh.'],
    'North Berwick Law' => ['East Lothian', 0, ''],
    'Edinburgh' => ['', 4, 'Hills, beaches and viewpoints inside the city: walks you can do in an afternoon.'],
    "Arthur's Seat" => ['Edinburgh', 0, ''],
    'Calton Hill' => ['Edinburgh', 1, ''],
    'Portobello' => ['Edinburgh', 2, ''],
  ]);
  replay_field('taxonomy_term', 'areas', 'field_photo', 'entity_reference', 'Photo',
    ['description' => 'A photo of the area, shown at the top of its page.', 'settings' => ['handler' => 'default:media', 'handler_settings' => [
      'target_bundles' => ['image' => 'image'], 'sort' => ['field' => '_none', 'direction' => 'ASC'], 'auto_create' => FALSE, 'auto_create_bundle' => '',
    ]]],
    ['settings' => ['target_type' => 'media']], 'media_library_widget', 'entity_reference_entity_view');
  $display = EntityViewDisplay::load('taxonomy_term.areas.default');
  $display->setComponent('field_photo', ['type' => 'entity_reference_entity_view', 'label' => 'hidden', 'settings' => ['view_mode' => '16_9_wide', 'link' => FALSE], 'weight' => -10]);
  $display->save();
  // The terms were made above, before the field: load them again, with it.
  \Drupal::entityTypeManager()->getStorage('taxonomy_term')->resetCache();
  $term = \Drupal\taxonomy\Entity\Term::load(replay_term('areas', 'Pentland Hills'));
  $term->set('field_photo', replay_photo('carnethy-hill-views.jpg'))->save();
}

/**
 * Chapter 10: an Area field on Hike and Gallery, and Gallery's Teaser.
 */
function replay_ch10_area_fields(): void {
  $settings = ['handler' => 'default:taxonomy_term', 'handler_settings' => [
    'target_bundles' => ['areas' => 'areas'], 'sort' => ['field' => 'name', 'direction' => 'asc'], 'auto_create' => FALSE, 'auto_create_bundle' => '',
  ]];
  $help = ['hike' => 'Where the hike is. Choose the hill or place; choose the region only if no place fits.', 'gallery' => 'Where the photos were taken.'];
  foreach ($help as $bundle => $description) {
    replay_field('node', $bundle, 'field_area', 'entity_reference', 'Area', ['description' => $description, 'settings' => $settings],
      ['settings' => ['target_type' => 'taxonomy_term']], 'options_select', 'entity_reference_label');
  }
  // The form: after Meeting place on Hike, after the title on Gallery. The display: inline, after Meeting place
  // (Hike) or first (Gallery).
  $form = EntityFormDisplay::load('node.hike.default');
  $order = ['title', 'field_date', 'field_meeting_place', 'field_area', 'field_distance', 'field_difficulty', 'field_hike_leader', 'field_content'];
  foreach ($order as $weight => $name) {
    $form->setComponent($name, ['weight' => $weight] + $form->getComponent($name));
  }
  $form->save();
  $form = EntityFormDisplay::load('node.gallery.default');
  $form->setComponent('field_area', ['weight' => ($form->getComponent('title')['weight'] ?? 0) + 1] + $form->getComponent('field_area'));
  $form->save();
  $area = ['type' => 'entity_reference_label', 'label' => 'inline', 'settings' => ['link' => TRUE]];
  $display = EntityViewDisplay::load('node.hike.default');
  $order = ['field_photo', 'content_moderation_control', 'field_date', 'field_meeting_place', 'field_area', 'field_distance', 'field_difficulty', 'field_hike_leader', 'field_content'];
  foreach ($order as $weight => $name) {
    $display->setComponent($name, ['weight' => $weight] + ($display->getComponent($name) ?: $area));
  }
  $display->save();
  $display = EntityViewDisplay::load('node.gallery.default');
  $display->setComponent('field_area', ['weight' => -1] + $area)->save();
  // The Teaser as on core, and the same on Card: Drupal CMS's term pages list content as cards.
  foreach (['teaser', 'card'] as $mode) {
    replay_display('gallery', $mode, [
      'content_moderation_control' => [],
    ] + ($mode == 'teaser' ? ['links' => []] : []) + [
      'field_area' => $area,
      'field_content' => ['type' => 'text_trimmed', 'label' => 'hidden', 'settings' => ['trim_length' => 200]],
    ]);
  }
  $nodes = \Drupal::entityTypeManager()->getStorage('node');
  foreach (['Turnhouse Hill and Carnethy Hill', 'Pentlands, 21 November'] as $title) {
    $node = current($nodes->loadByProperties(['title' => $title]));
    if ($node->get('field_area')->isEmpty()) {
      $node->set('field_area', replay_term('areas', 'Turnhouse Hill'));
      $node->setNewRevision();
      $node->setRevisionLogMessage('Added the area.');
      $node->save();
    }
  }
}

/**
 * Chapter 10: Photo themes, free tagging on Image media, with Drupal CMS's Tagify widget.
 */
function replay_ch10_themes(): void {
  replay_vocabulary('photo_themes', 'Photo themes', 'What a photo shows. Anyone who uploads a photo can add a theme.', [
    'City' => ['', 0, ''], 'Hills' => ['', 0, ''], 'Landscape' => ['', 0, ''], 'Water' => ['', 0, ''], 'Winter' => ['', 0, ''],
  ]);
  replay_field('media', 'image', 'field_themes', 'entity_reference', 'Themes',
    ['description' => 'What the photo shows, such as Landscape or Winter. A new theme is added to the list.', 'settings' => ['handler' => 'default:taxonomy_term', 'handler_settings' => [
      'target_bundles' => ['photo_themes' => 'photo_themes'], 'sort' => ['field' => 'name', 'direction' => 'asc'], 'auto_create' => TRUE, 'auto_create_bundle' => '',
    ]]],
    ['settings' => ['target_type' => 'taxonomy_term'], 'cardinality' => -1], 'tagify_entity_reference_autocomplete_widget', 'entity_reference_label');
  $widget = ['type' => 'tagify_entity_reference_autocomplete_widget', 'settings' => [
    'match_operator' => 'CONTAINS', 'match_limit' => 10, 'placeholder' => '', 'suggestions_dropdown' => 1, 'show_entity_id' => 0, 'show_info_label' => 0, 'info_label' => '',
  ]];
  foreach (['default', 'media_library'] as $mode) {
    $form = EntityFormDisplay::load("media.image.$mode");
    $form->setComponent('field_themes', $widget + ['weight' => replay_last_weight($form) + 1])->save();
  }
  $media = \Drupal\media\Entity\Media::load(replay_photo('turnhouse-hill-glencorse.jpg'));
  if ($media->get('field_themes')->isEmpty()) {
    $media->set('field_themes', array_map(fn($t) => replay_term('photo_themes', $t), ['Landscape', 'Water', 'Hills']))->save();
  }
}

/**
 * Chapter 11: a revision of the hike, to compare with Diff.
 */
function replay_ch11_head_torch(): void {
  $node = current(\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Turnhouse Hill and Carnethy Hill']));
  $text = $node->get('field_content')->value;
  if (!str_contains($text, 'head torch')) {
    $node->set('field_content', ['value' => str_replace('lunch, and your camera.', 'lunch, your camera, and a head torch: it gets dark before five in November.', $text), 'format' => $node->get('field_content')->format]);
    $node->setNewRevision();
    $node->setRevisionLogMessage('Added a head torch to the list.');
    $node->setRevisionCreationTime(\Drupal::time()->getRequestTime());
    $node->set('moderation_state', 'published');
    $node->save();
  }
}

/**
 * Chapter 11: the comment field from the Default comments recipe, re-used on Gallery, and the first comment.
 */
function replay_ch11_comments(): void {
  replay_field('node', 'gallery', 'comment', 'comment', 'Comments', [
    'default_value' => [['status' => 2, 'cid' => 0, 'last_comment_timestamp' => 0, 'last_comment_name' => NULL, 'last_comment_uid' => 0, 'comment_count' => 0]],
    'settings' => ['default_mode' => 1, 'per_page' => 50, 'anonymous' => 0, 'form_location' => TRUE, 'preview' => 1],
  ], [], 'comment_default', 'comment_default');
  $album = current(\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Pentlands, 21 November']));
  if ((int) $album->get('comment')->status !== 2) {
    // An album made before the field has no value in it yet: open its comments, as the form would.
    $album->set('comment', ['status' => 2]);
    $album->setNewRevision(FALSE);
    $album->setSyncing(TRUE);
    $album->save();
  }
  $comments = \Drupal::entityTypeManager()->getStorage('comment');
  if (!$comments->loadByProperties(['subject' => 'Snow on Carnethy'])) {
    $comments->create([
      'entity_type' => 'node', 'entity_id' => $album->id(), 'field_name' => 'comment', 'comment_type' => 'comment',
      'uid' => 1, 'subject' => 'Snow on Carnethy', 'status' => 1,
      'comment_body' => ['value' => '<p>The second photo is my favorite: you can see the snow line on Carnethy Hill.</p>', 'format' => filter_default_format(\Drupal\user\Entity\User::load(1))],
    ])->save();
  }
}

/**
 * Chapter 12: four more hikes, typed by the reader from the chapter's table, and a second album.
 */
function replay_ch12_hikes(): void {
  $nodes = \Drupal::entityTypeManager()->getStorage('node');
  $hikes = [
    // Title => [date (UTC), meeting place, distance, difficulty, area, photo, description].
    "Arthur's Seat at sunrise" => ['2026-10-24T05:30:00', 'Holyrood Palace car park', 5.5, 'moderate', "Arthur's Seat", NULL, 'An early start for the best light of the day: up Arthur\'s Seat by the Salisbury Crags path, in time for the sun to rise over the Firth of Forth. Bring a head torch for the way up.'],
    'North Berwick Law and the harbour' => ['2026-12-05T09:30:00', 'North Berwick railway station', 7, 'easy', 'North Berwick Law', NULL, 'A short climb up North Berwick Law, with the whalebone arch at the top and views to the Bass Rock, then down to the harbour for lunch. We take the train from Edinburgh Waverley at 8:55.'],
    'Glencorse Reservoir loop' => ['2026-12-19T09:30:00', 'Flotterstone car park', 9, 'easy', 'Glencorse Reservoir', 'glencorse-reservoir-portrait.jpg', 'A gentle walk along the reservoir and back over the lower slopes, good for winter light on the water. A good first hike with the club.'],
    'Pentland Hills ridge' => ['2027-01-02T09:00:00', 'Flotterstone car park', 16, 'hard', 'Pentland Hills', 'pentland-hills-winter.jpg', 'The whole ridge, from Turnhouse Hill over Carnethy, Scald Law and the Kips, and back through the glen. A long day, with a lot of climbing: bring plenty of food and water.'],
  ];
  foreach ($hikes as $title => [$date, $place, $distance, $difficulty, $area, $photo, $text]) {
    if ($nodes->loadByProperties(['title' => $title])) {
      continue;
    }
    $nodes->create([
      'type' => 'hike', 'title' => $title, 'uid' => 1,
      'field_date' => $date, 'field_meeting_place' => $place, 'field_distance' => $distance, 'field_difficulty' => $difficulty,
      'field_area' => replay_term('areas', $area),
      'field_photo' => $photo ? replay_photo($photo) : NULL,
      'field_content' => ['value' => "<p>$text</p>", 'format' => 'content_format'],
      'moderation_state' => 'published',
    ])->save();
  }
  if (!$nodes->loadByProperties(['title' => 'Edinburgh, 24 October'])) {
    $nodes->create([
      'type' => 'gallery', 'title' => 'Edinburgh, 24 October', 'uid' => 1,
      'field_area' => replay_term('areas', 'Edinburgh'),
      'field_content' => ['value' => '<p>Sunrise from Arthur\'s Seat, and the Old Town from Calton Hill on the way home.</p>', 'format' => 'content_format'],
      'field_hike' => current($nodes->loadByProperties(['title' => "Arthur's Seat at sunrise"]))->id(),
      'field_photos' => [replay_photo('edinburgh-skyline.jpg')],
      'comment' => ['status' => 2],
      'moderation_state' => 'published',
    ])->save();
  }
}

/**
 * Chapter 12: Drupal CMS's 16:9 Small media view mode, with the photographer, for the Newest photos grid.
 */
function replay_ch12_small(): void {
  $display = EntityViewDisplay::load('media.image.16_9_small');
  $weight = ($display->getComponent('field_media_image')['weight'] ?? 0) + 1;
  $display->setComponent('field_photographer', ['type' => 'string', 'label' => 'inline', 'settings' => ['link_to_entity' => FALSE], 'weight' => $weight]);
  $display->save();
}

/**
 * Chapter 13: term pages include the content of the term's children (depth), as on core.
 */
function replay_ch13_term_view(): void {
  $view = \Drupal\views\Entity\View::load('taxonomy_term');
  $display = &$view->getDisplay('default');
  $display['display_options']['arguments'] = ['term_node_tid_depth' => [
    'id' => 'term_node_tid_depth', 'table' => 'node_field_data', 'field' => 'term_node_tid_depth', 'relationship' => 'none',
    'group_type' => 'group', 'admin_label' => '', 'entity_type' => 'node', 'plugin_id' => 'taxonomy_index_tid_depth',
    'default_action' => 'not found',
    'exception' => ['value' => 'all', 'title_enable' => FALSE, 'title' => 'All'],
    'title_enable' => TRUE, 'title' => '{{ arguments.term_node_tid_depth }}',
    'default_argument_type' => 'fixed', 'default_argument_options' => ['argument' => ''],
    'summary_options' => ['base_path' => '', 'count' => TRUE, 'override' => FALSE, 'items_per_page' => 25],
    'summary' => ['sort_order' => 'asc', 'number_of_records' => 0, 'format' => 'default_summary'],
    'specify_validation' => TRUE,
    'validate' => ['type' => 'entity:taxonomy_term', 'fail' => 'not found'],
    'validate_options' => ['bundles' => [], 'access' => FALSE, 'operation' => 'view', 'multiple' => 0],
    'break_phrase' => FALSE, 'depth' => 2, 'use_taxonomy_term_path' => FALSE,
  ]];
  $display['display_options']['header']['entity_taxonomy_term']['target'] = '{{ raw_arguments.term_node_tid_depth }}';
  $view->save();
}

/**
 * Chapter 14: the main menu in the club's order, Hike archive under Hikes (Mercury shows one level only), the Privacy policy page
 * written and published, and the feed in the footer menu.
 */
function replay_ch14_menus(): void {
  $storage = \Drupal::entityTypeManager()->getStorage('menu_link_content');
  foreach (['About' => 3, 'Join us' => 4] as $title => $weight) {
    $link = current($storage->loadByProperties(['menu_name' => 'main', 'title' => $title]));
    $link->set('weight', $weight)->save();
  }
  $storage->create([
    'menu_name' => 'main', 'title' => 'Hike archive', 'link' => ['uri' => 'internal:/hikes/archive'],
    'parent' => 'views_view:views.hikes.page_1', 'weight' => 0,
  ])->save();

  $privacy = current(\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['type' => 'page', 'title' => 'Privacy policy']));
  $privacy->set('field_content', ['value' => '<p>Lens &amp; Trail keeps only what it needs to run the club: your name and email address if you join, and the photos you choose to share. We never sell or pass on your details.</p>', 'format' => 'content_format']);
  $privacy->set('moderation_state', 'published');
  $privacy->save();
  $storage->create([
    'menu_name' => 'footer', 'title' => 'Upcoming hikes (RSS)', 'link' => ['uri' => 'internal:/hikes/feed'], 'weight' => 1,
  ])->save();
}

/**
 * Chapter 15: the club's roles, between Authenticated user and Content editor, with core's permissions; Drupal CMS's
 * workflow is Basic editorial, with three transitions. Authenticated user loses Skip comment approval.
 */
function replay_ch15_roles(): void {
  $roles = [
    'member' => ['Member', ['skip comment approval', 'create gallery content', 'edit own gallery content', 'delete own gallery content',
      'create image media', 'edit own image media', 'access user profiles']],
    'hike_leader' => ['Hike leader', ['create hike content', 'edit own hike content', 'use basic_editorial transition create_new_draft',
      'view own unpublished content', 'view latest version', 'access content overview', 'access navigation', 'view the administration theme']],
    'secretary' => ['Secretary', ['create news content', 'edit any news content', 'delete own news content', 'edit any hike content',
      'edit any page content', 'edit any gallery content', 'use basic_editorial transition create_new_draft',
      'use basic_editorial transition publish', 'use basic_editorial transition unpublish', 'view any unpublished content',
      'view latest version', 'access content overview', 'administer comments', 'administer users', 'access navigation',
      'view the administration theme', 'access administration pages']],
  ];
  $weight = 2;
  foreach ($roles as $id => [$label, $permissions]) {
    $role = \Drupal\user\Entity\Role::load($id) ?? \Drupal\user\Entity\Role::create(['id' => $id, 'label' => $label]);
    foreach ($permissions as $permission) {
      $role->grantPermission($permission);
    }
    $role->setWeight($weight++)->save();
  }
  foreach (['content_editor', 'administrator'] as $id) {
    \Drupal\user\Entity\Role::load($id)->setWeight($weight++)->save();
  }
  \Drupal\user\Entity\Role::load('authenticated')->revokePermission('skip comment approval')->save();
}

/**
 * Chapter 15: Morag, Jordi and Ailsa (password 12345 on the test site), registration with approval, the user fields,
 * Jordi's profile, the Hike leader field for hike leaders only, and Jordi on the hikes admin led.
 */
function replay_ch15_users(): void {
  $users = \Drupal::entityTypeManager()->getStorage('user');
  foreach (['morag' => ['member', 'secretary'], 'jordi' => ['member', 'hike_leader'], 'ailsa' => ['member']] as $name => $roles) {
    if (!$users->loadByProperties(['name' => $name])) {
      $users->create(['name' => $name, 'mail' => "$name@example.com", 'pass' => '12345', 'status' => 1, 'roles' => $roles])->save();
    }
  }
  \Drupal::configFactory()->getEditable('user.settings')->set('register', 'visitors_admin_approval')->set('verify_mail', TRUE)->save();
  replay_field('user', 'user', 'field_camera', 'string', 'Camera');
  replay_field('user', 'user', 'field_about_me', 'string_long', 'About me');
  $jordi = current($users->loadByProperties(['name' => 'jordi']));
  $jordi->set('field_camera', 'Fujifilm X-T5, and a phone when it rains')
    ->set('field_about_me', "I moved to Edinburgh from Barcelona in 2019, and I've been leading hikes in the Pentlands ever since. Ask me about the best spots for sunrise.")
    ->save();
  $field = \Drupal\field\Entity\FieldConfig::loadByName('node', 'hike', 'field_hike_leader');
  $handler = $field->getSetting('handler_settings');
  $handler['filter'] = ['type' => 'role', 'role' => ['hike_leader' => 'hike_leader']];
  $field->setSetting('handler_settings', $handler)->save();
  // The Try it: the hikes with admin (or nobody) as their leader get Jordi.
  foreach (\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['type' => 'hike']) as $hike) {
    if (in_array($hike->get('field_hike_leader')->target_id, [NULL, '1', 1], TRUE)) {
      $hike->set('field_hike_leader', $jordi->id())->setNewRevision(TRUE);
      $hike->setRevisionLogMessage('Jordi leads this hike.');
      $hike->save();
    }
  }
}

/**
 * Chapter 15: CAPTCHA (downloaded with Composer first), with the image challenge on registration and the password reset.
 */
function replay_ch15_captcha(): void {
  \Drupal::service('module_installer')->install(['captcha', 'image_captcha']);
  \Drupal::configFactory()->getEditable('captcha.settings')->set('default_challenge', 'image_captcha/Image')->save();
  foreach (['user_register_form', 'user_pass'] as $form) {
    \Drupal\captcha\Entity\CaptchaPoint::load($form)->enable()->save();
  }
}

/**
 * Chapter 15: Lucía applied, was approved and made a member; her comment on the Pentlands album, approved.
 */
function replay_ch15_lucia(): void {
  $users = \Drupal::entityTypeManager()->getStorage('user');
  $lucia = current($users->loadByProperties(['name' => 'lucia']));
  if (!$lucia) {
    $lucia = $users->create(['name' => 'lucia', 'mail' => 'lucia@example.com', 'pass' => '12345', 'status' => 1, 'roles' => ['member']]);
    $lucia->save();
  }
  $album = current(\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Pentlands, 21 November']));
  \Drupal\comment\Entity\Comment::create([
    'entity_type' => 'node', 'entity_id' => $album->id(), 'field_name' => 'comment', 'comment_type' => 'comment',
    'uid' => $lucia->id(), 'subject' => 'Lovely light on the Turnhouse photo!', 'status' => 1,
    'comment_body' => ['value' => '<p>Lovely light on the Turnhouse photo! Which lens was that?</p>', 'format' => filter_default_format($lucia)],
  ])->save();
}

/**
 * Chapter 17: the Trash emptied before the bulk update (Summer barbecue from Chapter 6 and the pages Devel Generate
 * made in Chapter 11, which keep their aliases while they're in the Trash), and the tags Devel Generate made.
 */
function replay_ch17_cleanup(): void {
  \Drupal::service('trash.manager')->executeInTrashContext('inactive', function () {
    $nodes = \Drupal::entityTypeManager()->getStorage('node');
    $trashed = $nodes->getQuery()->accessCheck(FALSE)->exists('deleted')->execute();
    $nodes->delete($nodes->loadMultiple($trashed));
  });
  // The club tags nothing (Chapter 10's Tags Try it is for News), so every tag is one Devel Generate made.
  if (!\Drupal::database()->query("SELECT COUNT(*) FROM {node__field_tags}")->fetchField()) {
    // One at a time: deleting a term deletes its children too, and a list loaded before would hold them.
    $terms = \Drupal::entityTypeManager()->getStorage('taxonomy_term');
    // From the table: loadByProperties() leaves out some of the generated terms (some are unpublished).
    foreach (\Drupal::database()->query("SELECT DISTINCT tid FROM {taxonomy_term_field_data} WHERE vid = 'tags'")->fetchCol() as $tid) {
      $terms->resetCache([$tid]);
      $terms->load($tid)?->delete();
    }
  }
}

/**
 * Chapter 17: core's Pathauto patterns, above Drupal CMS's Menu Path, and the aliases updated.
 */
function replay_ch17_patterns(): void {
  $patterns = [
    'hikes' => ['Hikes', 'canonical_entities:node', '/hikes/[node:title]', 'node', 'hike'],
    'albums' => ['Albums', 'canonical_entities:node', '/galleries/[node:title]', 'node', 'gallery'],
    'news' => ['News', 'canonical_entities:node', '/news/[node:title]', 'node', 'news'],
    'areas' => ['Areas', 'canonical_entities:taxonomy_term', '/areas/[term:parents:join-path]/[term:name]', 'taxonomy_term', 'areas'],
    'photo_themes' => ['Photo themes', 'canonical_entities:taxonomy_term', '/photo-themes/[term:name]', 'taxonomy_term', 'photo_themes'],
  ];
  $weight = -10;
  foreach ($patterns as $id => [$label, $type, $pattern, $entity_type, $bundle]) {
    if (\Drupal\pathauto\Entity\PathautoPattern::load($id)) {
      continue;
    }
    $p = \Drupal\pathauto\Entity\PathautoPattern::create(['id' => $id, 'label' => $label, 'type' => $type, 'pattern' => $pattern, 'weight' => $weight++]);
    $p->addSelectionCondition([
      'id' => 'entity_bundle:' . $entity_type,
      'bundles' => [$bundle => $bundle],
      'negate' => FALSE,
      'context_mapping' => [$entity_type => $entity_type],
    ]);
    $p->save();
  }
  // Bulk generate, "Update the URL alias for paths having an old URL alias": on Drupal CMS, everything has an alias
  // from Menu Path already. Content whose automatic alias is off (About, How to join, the Turnhouse hike since
  // Chapters 6 and 7) keeps its own.
  $generator = \Drupal::service('pathauto.generator');
  foreach (['node', 'taxonomy_term'] as $entity_type) {
    foreach (\Drupal::entityTypeManager()->getStorage($entity_type)->loadMultiple() as $entity) {
      $generator->updateEntityAlias($entity, 'bulkupdate');
    }
  }
}

/**
 * Chapter 17: Glencorse Reservoir loop becomes the winter loop; Pathauto makes the new alias and a redirect from the
 * old one. Two addresses that don't exist are visited, for Redirect 404's list.
 */
function replay_ch17_rename(): void {
  $node = current(\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Glencorse Reservoir loop']));
  if ($node) {
    $node->setTitle('Glencorse Reservoir winter loop');
    $node->setNewRevision(TRUE);
    $node->setRevisionLogMessage('Renamed: the winter route.');
    $node->save();
  }
}

/**
 * Chapter 18: what can be translated, as on core. All four content types (the text fields; Hike also Meeting place),
 * both vocabularies, Image media (alt and title, not the file) and custom menu links; the fields that aren't words are
 * shared between the languages, and hidden on the translation form. Canvas pages are done in the form.
 */
function replay_ch18_translatable(): void {
  $translatable = [
    'node' => [
      'hike' => ['field_content', 'field_meeting_place'],
      'gallery' => ['field_content'],
      'news' => ['field_content'],
      'page' => ['field_content', 'field_description', 'field_seo_title', 'field_seo_description'],
    ],
    'taxonomy_term' => ['areas' => [], 'photo_themes' => []],
    'media' => ['image' => ['field_media_image']],
    'menu_link_content' => ['menu_link_content' => []],
  ];
  $manager = \Drupal::service('content_translation.manager');
  foreach ($translatable as $entity_type => $bundles) {
    foreach ($bundles as $bundle => $fields) {
      $settings = \Drupal\language\Entity\ContentLanguageSettings::loadByEntityTypeBundle($entity_type, $bundle);
      $settings->setLanguageAlterable(TRUE)->setDefaultLangcode('site_default')->save();
      $manager->setEnabled($entity_type, $bundle, TRUE);
      $manager->setBundleTranslationSettings($entity_type, $bundle, ['untranslatable_fields_hide' => '1']);
      foreach (\Drupal::service('entity_field.manager')->getFieldDefinitions($entity_type, $bundle) as $name => $definition) {
        if ($definition instanceof \Drupal\field\Entity\FieldConfig) {
          $definition->setTranslatable(in_array($name, $fields, TRUE));
          if ($name === 'field_media_image') {
            $definition->setThirdPartySetting('content_translation', 'translation_sync', ['alt' => 'alt', 'title' => 'title', 'file' => '0']);
          }
          $definition->save();
        }
      }
    }
  }
  \Drupal::service('entity_field.manager')->clearCachedFieldDefinitions();
  \Drupal::service('router.builder')->rebuild();
}

/**
 * Chapter 18: the Spanish Pathauto patterns, above the English ones.
 */
function replay_ch18_patterns(): void {
  $patterns = [
    ['excursiones', 'Excursiones', 'node', '/excursiones/[node:title]', 'hike'],
    ['albums_es', 'Álbumes', 'node', '/albumes/[node:title]', 'gallery'],
    ['news_es', 'Noticias', 'node', '/noticias/[node:title]', 'news'],
    ['areas_es', 'Zonas', 'taxonomy_term', '/zonas/[term:parents:join-path]/[term:name]', 'areas'],
    ['photo_themes_es', 'Temas fotográficos', 'taxonomy_term', '/temas-fotograficos/[term:name]', 'photo_themes'],
  ];
  foreach ($patterns as [$id, $label, $entity, $pattern, $bundle]) {
    $p = \Drupal\pathauto\Entity\PathautoPattern::load($id);
    if (!$p) {
      $p = \Drupal\pathauto\Entity\PathautoPattern::create(['id' => $id, 'label' => $label, 'type' => 'canonical_entities:' . $entity, 'pattern' => $pattern]);
      $p->addSelectionCondition(['id' => 'entity_bundle:' . $entity, 'bundles' => [$bundle => $bundle], 'negate' => FALSE, 'context_mapping' => [$entity => $entity]]);
      $p->addSelectionCondition(['id' => 'language', 'langcodes' => ['es' => 'es'], 'negate' => FALSE, 'context_mapping' => ['language' => $entity . ':langcode:language']]);
      $p->addRelationship($entity . ':langcode:language', 'Language');
    }
    $p->set('weight', -20)->save();
  }
  // View pages have no pattern: their Spanish aliases by hand.
  $aliases = \Drupal::entityTypeManager()->getStorage('path_alias');
  foreach (['/hikes' => '/excursiones', '/hikes/archive' => '/excursiones/archivo', '/galleries' => '/albumes'] as $path => $alias) {
    if (!$aliases->loadByProperties(['path' => $path, 'langcode' => 'es'])) {
      $aliases->create(['path' => $path, 'alias' => $alias, 'langcode' => 'es'])->save();
    }
  }
}

/**
 * Chapter 18: a Translator role for Lucía.
 */
function replay_ch18_translator(): void {
  $role = \Drupal\user\Entity\Role::load('translator') ?? \Drupal\user\Entity\Role::create(['id' => 'translator', 'label' => 'Translator']);
  foreach (['create content translations', 'update content translations', 'translate hike node', 'translate page node',
    'translate news node', 'translate gallery node', 'use basic_editorial transition publish', 'view latest version',
    'view the administration theme', 'access navigation'] as $permission) {
    $role->grantPermission($permission);
  }
  $role->save();
  $lucia = current(\Drupal::entityTypeManager()->getStorage('user')->loadByProperties(['name' => 'lucia']));
  $lucia->addRole('translator');
  $lucia->save();
}

/**
 * Chapter 21: the Elevation gain field on Hike, as core does: right after Distance on the form and on every
 * display that shows Distance, with Distance's label setting.
 */
function replay_ch21_elevation(): void {
  replay_field('node', 'hike', 'field_elevation_gain', 'integer', 'Elevation gain', ['settings' => ['min' => 0, 'suffix' => ' m']]);
  $displays = array_merge(
    \Drupal::entityTypeManager()->getStorage('entity_form_display')->loadByProperties(['targetEntityType' => 'node', 'bundle' => 'hike']),
    \Drupal::entityTypeManager()->getStorage('entity_view_display')->loadByProperties(['targetEntityType' => 'node', 'bundle' => 'hike'])
  );
  foreach ($displays as $display) {
    $distance = $display->getComponent('field_distance');
    if (!$distance) {
      $display->removeComponent('field_elevation_gain')->save();
      continue;
    }
    $after = $distance['weight'];
    foreach ($display->getComponents() as $name => $component) {
      if ($name !== 'field_elevation_gain' && ($component['weight'] ?? 0) > $after) {
        $component['weight']++;
        $display->setComponent($name, $component);
      }
    }
    $form = $display instanceof EntityFormDisplay;
    $display->setComponent('field_elevation_gain', [
      'type' => $form ? 'number' : 'number_integer',
      'weight' => $after + 1,
      'region' => 'content',
    ] + ($form ? [] : ['label' => $distance['label'] ?? 'above', 'settings' => ['thousand_separator' => '', 'prefix_suffix' => TRUE]]))->save();
  }
}

/**
 * Chapter 23: Hike's Teaser tidied for Mercury: the title linked, no labels on Date, Distance, Elevation gain and
 * Difficulty, no Links.
 */
function replay_ch23_teaser(): void {
  $display = EntityViewDisplay::load('node.hike.teaser');
  foreach (['field_date', 'field_distance', 'field_elevation_gain', 'field_difficulty'] as $name) {
    if ($component = $display->getComponent($name)) {
      $display->setComponent($name, ['label' => 'hidden'] + $component);
    }
  }
  if ($title = $display->getComponent('title')) {
    $title['settings']['link_to_entity'] = TRUE;
    $display->setComponent('title', $title);
  }
  $display->removeComponent('links')->save();
}

/**
 * Chapter 23: Find a hike in the main menu, its Spanish title, and the Spanish redirect to /buscar-excursion.
 */
function replay_ch23_menu(): void {
  $storage = \Drupal::entityTypeManager()->getStorage('menu_link_content');
  $link = current($storage->loadByProperties(['title' => 'Find a hike'])) ?: $storage->create([
    'title' => 'Find a hike', 'link' => ['uri' => 'internal:/find-a-hike'], 'menu_name' => 'main', 'weight' => 5,
  ]);
  $link->save();
  if (!$link->hasTranslation('es')) {
    $link->addTranslation('es', ['title' => 'Buscar excursión', 'link' => $link->get('link')->getValue(), 'menu_name' => 'main'])->save();
  }
  $redirects = \Drupal::entityTypeManager()->getStorage('redirect');
  if (!$redirects->loadByProperties(['redirect_source__path' => 'find-a-hike', 'language' => 'es'])) {
    $redirects->create([
      'redirect_source' => ['path' => 'find-a-hike', 'query' => []],
      'redirect_redirect' => ['uri' => 'internal:/buscar-excursion'],
      'language' => 'es',
      'status_code' => 301,
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
