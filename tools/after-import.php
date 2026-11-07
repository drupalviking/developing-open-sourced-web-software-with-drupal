<?php

/**
 * @file
 * Finishes a site rebuilt from sites/<name>/ (see tools/export-sites.sh).
 *
 * Run inside the rebuilt site, after its content recipe:
 *
 *   ddev drush php:script <export folder>/after-import.php -- <export folder>
 *
 * Puts back what the content import can't bring: Focal Point's crops, from
 * focal-points.json (absolute x and y on each image, by the file's UUID).
 */

declare(strict_types=1);

$dir = array_shift($extra) ?? '';
$points_file = "$dir/focal-points.json";
if (is_file($points_file) && \Drupal::hasService('focal_point.manager')) {
  $crop_type = \Drupal::config('focal_point.settings')->get('crop_type');
  $manager = \Drupal::service('focal_point.manager');
  $files = \Drupal::entityTypeManager()->getStorage('file');
  $count = 0;
  foreach (json_decode(file_get_contents($points_file), TRUE) as $uuid => $point) {
    $file = $files->loadByProperties(['uuid' => $uuid]);
    if ($file = reset($file)) {
      $crop = $manager->getCropEntity($file, $crop_type);
      $crop->set('x', $point['x']);
      $crop->set('y', $point['y']);
      $crop->save();
      $count++;
    }
  }
  echo "Focal points: $count\n";
}
