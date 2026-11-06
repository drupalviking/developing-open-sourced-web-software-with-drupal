<?php

/**
 * @file
 * Removes empty links from the Heading components in Canvas content templates.
 *
 * Drupal CMS's Basic page template stores its Heading's link as an empty text
 * ("url": ""), and Canvas Translate's dashboard stops with "Something went
 * wrong on our end" when it reads it. Removing the empty link changes nothing
 * on the page: the heading had no link.
 *
 * Run it from your project folder:
 *   ddev drush php:script remove-empty-heading-links.php
 */

$storage = \Drupal::entityTypeManager()->getStorage('content_template');
foreach ($storage->loadMultiple() as $template) {
  $tree = $template->get('component_tree');
  $changed = FALSE;
  foreach ($tree as &$item) {
    if ($item['component_id'] !== 'sdc.mercury.heading') {
      continue;
    }
    $inputs = is_string($item['inputs']) ? json_decode($item['inputs'], TRUE) : $item['inputs'];
    if (($inputs['url'] ?? NULL) === '') {
      unset($inputs['url']);
      $item['inputs'] = is_string($item['inputs']) ? json_encode($inputs) : $inputs;
      $changed = TRUE;
    }
  }
  unset($item);
  if ($changed) {
    $template->set('component_tree', $tree)->save();
    echo 'Removed an empty heading link from ' . $template->label() . "\n";
  }
}
