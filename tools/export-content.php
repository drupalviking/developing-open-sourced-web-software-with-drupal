<?php

/**
 * @file
 * Exports a site's content with core's default content exporter, keeping IDs.
 *
 * Run by tools/export-sites.sh inside the site:
 *
 *   ddev drush php:script ../path/to/export-content.php -- <dir> <type>...
 *
 * Core's content:export command leaves out entity IDs (and creation dates), so
 * imported content gets new IDs. That breaks everything that refers to content
 * by ID: the front page setting (/node/3), menu links (entity:node/3),
 * redirects, Layout Builder blocks. A listener on the exporter's event puts
 * the IDs, and the created and changed dates (the club's lists sort by them),
 * back into the export. The importer then creates each entity with its old ID.
 *
 * Path aliases: each path field keeps its Pathauto setting, and the aliases
 * that belong to no entity (a view page's Spanish alias) are exported as
 * path_alias entities; pass path_alias as one of the types.
 */

declare(strict_types=1);

use Drupal\Core\DefaultContent\Exporter;
use Drupal\Core\DefaultContent\PreExportEvent;
use Drupal\Core\Entity\ContentEntityInterface;

// $extra holds the arguments after "--".
[$dir, $types] = [array_shift($extra), $extra];
if (!$dir || !$types) {
  throw new \InvalidArgumentException('Usage: drush php:script export-content.php -- <dir> <entity type>...');
}

\Drupal::service('event_dispatcher')->addListener(PreExportEvent::class, function (PreExportEvent $event): void {
  $entity = $event->entity;
  // Path aliases get new IDs: the aliases of imported content are created
  // during the import, and could take an exported alias's ID first.
  if ($entity->getEntityType()->hasIntegerId() && $entity->getEntityTypeId() !== 'path_alias') {
    $event->setEntityKeyExportable('id');
  }
  // With Pathauto, a path field also says whether the alias is generated
  // ("pathauto": 1) or typed by hand (0). Without it, Pathauto treats imported
  // content as new and generates an alias, replacing hand-made ones.
  $event->setCallback('field_item:path', function ($item): array {
    $values = ['alias' => $item->alias, 'langcode' => $item->langcode];
    if (isset($item->getProperties(TRUE)['pathauto'])) {
      $values['pathauto'] = (int) $item->pathauto;
    }
    return $values;
  });
  // Scheduler's moderation states (Drupal CMS) mean something only where a
  // workflow applies. Book 1's tags have stale values from before, which the
  // importer's validation rejects, so leave them out of unmoderated content.
  if ($entity->hasField('publish_state') && \Drupal::hasService('content_moderation.moderation_information')
    && !\Drupal::service('content_moderation.moderation_information')->isModeratedEntity($entity)) {
    $event->setExportable('publish_state', FALSE);
    $event->setExportable('unpublish_state', FALSE);
  }
  foreach ($entity->getFieldDefinitions() as $name => $definition) {
    if (in_array($definition->getType(), ['changed', 'created'], TRUE)) {
      $event->setExportable($name);
    }
  }
}, -100);

$exporter = \Drupal::service(Exporter::class);
$entity_type_manager = \Drupal::entityTypeManager();

// A pattern matching the paths of content entities (/node/3, /page/2/edit...),
// from each entity type's canonical link template (/node/{node}).
$prefixes = [];
foreach ($entity_type_manager->getDefinitions() as $definition) {
  if ($definition->entityClassImplements(ContentEntityInterface::class) && $definition->hasLinkTemplate('canonical')) {
    $template = $definition->getLinkTemplate('canonical');
    $prefixes[] = str_replace('\\{' . $definition->id() . '\\}', '\\d+', preg_quote($template, '@'));
  }
}
$entity_paths = '@^(' . implode('|', $prefixes) . ')(/|$)@';
foreach ($types as $type) {
  if (!$entity_type_manager->hasDefinition($type)) {
    continue;
  }
  $count = 0;
  // loadByProperties(), as core's content:export does: it leaves out broken
  // entities that have no row in their default language (Devel Generate made
  // a few on the Drupal CMS site), which can't be imported.
  foreach ($entity_type_manager->getStorage($type)->loadByProperties() as $entity) {
    // Only the aliases that belong to no entity, such as a view page's
    // Spanish alias: the others come with their content's path field.
    if ($type === 'path_alias' && preg_match($entity_paths, $entity->getPath())) {
      continue;
    }
    assert($entity instanceof ContentEntityInterface);
    $exporter->exportToFile($entity, $dir);
    $count++;
  }
  echo "$type: $count\n";
}

// Focal Point (Drupal CMS) keeps each image's focal point in a crop entity,
// and makes a crop itself (at the default point) whenever an image is saved,
// so exported crops would collide with the ones it makes on import. Instead,
// write the focal points to a file next to the content: the rebuilt site's
// after-import.php (tools/after-import.php) puts them back.
if (\Drupal::hasService('focal_point.manager')) {
  $crop_type = \Drupal::config('focal_point.settings')->get('crop_type');
  $points = [];
  foreach ($entity_type_manager->getStorage('crop')->loadByProperties(['type' => $crop_type, 'entity_type' => 'file']) as $crop) {
    $file = $entity_type_manager->getStorage('file')->load($crop->get('entity_id')->value);
    if ($file && !$crop->get('x')->isEmpty()) {
      $points[$file->uuid()] = ['x' => (int) $crop->get('x')->value, 'y' => (int) $crop->get('y')->value];
    }
  }
  file_put_contents(dirname($dir) . '/focal-points.json', json_encode($points, JSON_PRETTY_PRINT) . "\n");
  echo 'focal points: ' . count($points) . "\n";
}
