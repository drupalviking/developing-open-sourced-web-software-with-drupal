# Media Entity Spotify - Drupal 11 Refactoring Summary  
  
## Overview  
  
The `media_entity_spotify` module was originally created for Drupal 8 when Media was still a contributed module called "Media Entity". This refactoring updates the module to work with Drupal 11 and core's Media module using modern PHP 8 attributes.  
  
---  
  
## Major Changes  
  
### 1. Converted from MediaType to MediaSource Plugin  
  
**Old Architecture (Drupal 8 contrib):**  
- Namespace: `Drupal\media_entity_spotify\Plugin\MediaEntity\Type\Spotify`  
- Extended: `MediaTypeBase` from contrib `media_entity` module  
- Used: `@MediaType` annotation  
  
**New Architecture (Drupal 11 core):**  
- Namespace: `Drupal\media_entity_spotify\Plugin\media\Source\Spotify`  
- Extends: `MediaSourceBase` from core `media` module  
- Uses: `#[MediaSource]` PHP 8 attribute  
  
**File:** `src/Plugin/media/Source/Spotify.php`  
  
#### Key Implementation Details:  
  
```php  
#[MediaSource(  
  id: "spotify",  label: new TranslatableMarkup("Spotify"),  description: new TranslatableMarkup("Provides business logic and metadata for Spotify."),  allowed_field_types: ["string", "string_long", "link"],  default_thumbnail_filename: "spotify.png",)]  
class Spotify extends MediaSourceBase {  
  // Implementation}  
```  
  
**New Methods Implemented:**  
- `getMetadataAttributes()` - Defines available metadata fields  
- `getMetadata()` - Retrieves metadata for a media item  
- `getSpotifyUri()` - Converts Spotify URLs to URIs  
- `getLocalThumbnailUri()` - Downloads and caches thumbnails  
- `oEmbed()` - Fetches oEmbed data from Spotify  
  
**Deprecated Methods Replaced:**  
- Old: `providedFields()` → New: `getMetadataAttributes()`  
- Old: `getField()` → New: `getMetadata()`  
- Old: `thumbnail()` → New: Handled by `getMetadata('thumbnail_uri')`  
  
---  
  
### 2. Updated Field Formatter  
  
**File:** `src/Plugin/Field/FieldFormatter/SpotifyEmbedFormatter.php`  
  
#### Changes:  
  
**a) Converted Annotation to Attribute:**  
```php  
// OLD:  
/**  
 * @FieldFormatter( *   id = "spotify_embed", *   label = @Translation("Spotify embed"), *   field_types = { *     "link", "string", "string_long" *   } * ) */  
// NEW:  
#[FieldFormatter(  
  id: "spotify_embed",  label: new TranslatableMarkup("Spotify embed"),  field_types: [    "link",    "string",    "string_long",  ],)]  
```  
  
**b) Updated viewElements() Method:**  
```php  
// OLD approach:  
$media_type = $media_entity->getType();  
if ($media_type instanceof Spotify) {  
  $uri = $media_type->getField($media_entity, 'uri');}  
  
// NEW approach:  
$media_source = $media_entity->getSource();  
if ($media_source instanceof Spotify) {  
  $uri = $media_source->getMetadata($media_entity, 'uri');}  
```  
  
---  
  
### 3. Fixed Install Hook with Deprecated Functions  
  
**File:** `media_entity_spotify.install`  
  
#### Deprecated Functions Replaced:  
  
**a) `drupal_get_path()` → Extension List Service:**  
```php  
// OLD (Deprecated in Drupal 9, removed in Drupal 10):  
$source = drupal_get_path('module', 'media_entity_spotify') . '/images/icons';  
  
// NEW:  
$source = \Drupal::service('extension.list.module')->getPath('media_entity_spotify') . '/images/icons';  
```  
  
**b) `media_entity_copy_icons()` → FileSystemInterface:**  
```php  
// OLD (Function from contrib media_entity module):  
media_entity_copy_icons($source, $destination);  
  
// NEW (Using core FileSystemInterface):  
$file_system = \Drupal::service('file_system');  
$file_system->prepareDirectory($destination, FileSystemInterface::CREATE_DIRECTORY);  
$file_system->copy($file->uri, $destination . '/' . $file->filename);  
```  
  
**c) Updated Icon Destination:**  
```php  
// OLD (media_entity contrib config):  
$destination = \Drupal::config('media_entity.settings')->get('icon_base');  
  
// NEW (core Media standard location):  
$destination = 'public://media-icons/generic';  
```  
  
---  
  
### 4. Updated Configuration Schema  
  
**File:** `config/schema/media_entity_spotify.schema.yml`  
  
#### Changed Schema Key:  
```yaml  
# OLD (media_entity contrib):  
media_entity.bundle.type.spotify:  
  type: mapping  label: 'Spotify type configuration'  mapping:    source_url_field:      type: string  
# NEW (core Media):  
media.source.spotify:  
  type: media_source  label: 'Spotify media source configuration'  mapping:    source_field:      type: string  
```  
  
---  
  
### 5. Fixed Property Redeclaration Issue  
  
**File:** `src/Plugin/media/Source/Spotify.php`  
  
#### Issue:  
Fatal error due to redeclaring `$configFactory` property that already exists in parent `MediaSourceBase` class.  
  
#### Solution:  
Removed duplicate property declarations that exist in parent class:  
- ✅ Removed: `protected ConfigFactoryInterface $configFactory;`  
- ✅ Kept only unique properties: `$httpClient`, `$fileSystem`, `$spotify`  
  
The `$configFactory` property is still accessible via inheritance from `MediaSourceBase`.  
  
---  
  
### 6. Fixed Spotify URL Parsing for Modern URLs  
  
**File:** `src/Plugin/media/Source/Spotify.php` - `getSpotifyUri()` method  
  
#### Problem:  
Playlist URLs weren't working because Spotify changed their URL format.  
  
**Old playlist URL format:**  
```  
https://open.spotify.com/user/{user_id}/playlist/{playlist_id}  
```  
  
**New playlist URL format:**  
```  
https://open.spotify.com/playlist/{playlist_id}  
```  
  
#### Solution:  
Updated regex patterns to support both formats and added more content types:  
  
```php  
// New playlist format (without user)  
if (preg_match('/^https?:\/\/(?:open|play)\.spotify\.com\/playlist\/([\w\d]+)(?:\?.*)?$/i', $url, $matches)) {  
  return 'spotify:playlist:' . $matches[1];}  
  
// Old playlist format (with user) - still supported  
if (preg_match('/^https?:\/\/(?:open|play)\.spotify\.com\/user\/([\w\d]+)\/playlist\/([\w\d]+)(?:\?.*)?$/i', $url, $matches)) {  
  return 'spotify:user:' . $matches[1] . ':playlist:' . $matches[2];}  
```  
  
**Additional Improvements:**  
- Added query parameter support (`(?:\?.*)?`) for URLs with tracking parameters like `?si=xxx`  
- Added support for more Spotify content types:  
  - ✅ Tracks: `spotify:track:{id}`  
  - ✅ Albums: `spotify:album:{id}`  
  - ✅ Playlists (new): `spotify:playlist:{id}`  
  - ✅ Playlists (old): `spotify:user:{user}:playlist:{id}`  
  - ✅ Artists: `spotify:artist:{id}`  
  - ✅ Shows/Podcasts: `spotify:show:{id}`  
  - ✅ Episodes: `spotify:episode:{id}`  
  
---  
  
### 7. Cleaned Up Deprecated Files  
  
**Removed:**  
- `src/Plugin/MediaEntity/Type/Spotify.php` (old MediaType plugin)  
- `src/Plugin/MediaEntity/Type/` (empty directory)  
- `src/Plugin/MediaEntity/` (empty directory)  
  
**Updated:**  
- `media_entity_spotify.info.yml` - Updated description to reflect core Media module usage  
  
---  
  
### 8. Fixed Critical Thumbnail Bugs  
  
**File:** `src/Plugin/media/Source/Spotify.php`  
  
#### Issue 1: Malformed Thumbnail Filenames  
  
**Problem:**  
Thumbnails were being saved with concatenated filenames without proper extensions, causing files like:  
```  
ab67616d00001e02529dacec9e3b0968db79f028ab67616d00001e029596eb219c1cc09b181dece5...  
```  
  
**Root Cause:**  
Using `pathinfo($thumbnail_url, PATHINFO_BASENAME)` directly on URLs doesn't properly extract filenames, especially when URLs contain query parameters.  
  
**Solution:**  
```php  
// OLD (incorrect):  
$local_uri = $destination . '/' . pathinfo($thumbnail_url, PATHINFO_BASENAME);  
  
// NEW (correct):  
$parsed_url = parse_url($thumbnail_url);  
$path_parts = pathinfo($parsed_url['path'] ?? '');  
$filename = $path_parts['filename'] ?? 'thumbnail';  
$extension = $path_parts['extension'] ?? 'jpg';  
$local_filename = $filename . '.' . $extension;  
$local_uri = $destination . '/' . $local_filename;  
```  
  
Now thumbnails are saved with proper filenames like: `ab67616d00001e02529dacec.jpg`  
  
#### Issue 2: Stream Wrapper File Existence Check  
  
**Problem:**  
Using `file_exists($local_uri)` doesn't work reliably with Drupal stream wrappers like `public://`.  
  
**Solution:**  
```php  
// OLD (unreliable with stream wrappers):  
if (!file_exists($local_uri)) {  
  // Download file}  
  
// NEW (stream wrapper compatible):  
$real_path = $this->fileSystem->realpath($local_uri);  
if ($real_path && file_exists($real_path)) {  
  return $local_uri;}  
```  
  
#### Issue 3: oEmbed Caching Bug (CRITICAL)  
  
**Problem:**  
The `oEmbed()` method cached data in a single variable `$this->spotify`, causing **all media items to share the same thumbnail**. Once the first media item loaded, all subsequent items would use its cached oEmbed data.  
  
```php  
// OLD (broken - all items share same data):  
protected ?array $spotify = NULL;  
  
protected function oEmbed(string $url): ?array {  
  if ($this->spotify !== NULL) {    return $this->spotify;  // Returns SAME data for ALL URLs!  }  // ...  $this->spotify = json_decode((string) $response->getBody(), TRUE);  return $this->spotify;}  
```  
  
**Solution:**  
Cache data by URL as a key in an associative array:  
  
```php  
// NEW (correct - each URL gets its own cached data):  
protected array $spotify = [];  
  
protected function oEmbed(string $url): ?array {  
  // Return cached data if available for THIS specific URL  if (isset($this->spotify[$url])) {    return $this->spotify[$url];  }  
  try {    $oembed_url = 'https://embed.spotify.com/oembed/?url=' . urlencode($url);    $response = $this->httpClient->get($oembed_url);    $data = json_decode((string) $response->getBody(), TRUE);  
    // Cache the data for this specific URL    $this->spotify[$url] = $data;  
    return $data;  }  catch (GuzzleException $e) {    \Drupal::logger('media_entity_spotify')->error('Failed to fetch oEmbed data from Spotify: @error', [      '@error' => $e->getMessage(),    ]);    return NULL;  }}  
```  
  
#### Additional Improvements:  
  
**Error Logging:**  
Added proper error logging for thumbnail download failures:  
  
```php  
catch (\Exception $e) {  
  \Drupal::logger('media_entity_spotify')->error('Failed to download thumbnail from @url: @error', [    '@url' => $thumbnail_url,    '@error' => $e->getMessage(),  ]);  return NULL;}  
```  
  
**Return Saved URI:**  
Now properly returns the saved URI from `saveData()`:  
  
```php  
$saved_uri = $this->fileSystem->saveData($image, $local_uri, FileSystemInterface::EXISTS_REPLACE);  
if ($saved_uri) {  
  return $saved_uri;}  
```  
  
#### After Fixing:  
  
To regenerate thumbnails after these fixes:  
  
1. **Clear Drupal cache:**  
   ```bash  
   drush cr   ```  
2. **Resave media items** to regenerate thumbnails:  
   ```bash  
   drush php:eval "foreach (\Drupal::entityTypeManager()->getStorage('media')->loadByProperties(['bundle' => 'spotify']) as \$media) { \$media->save(); }"   ```  
Or manually edit and save each media item through the UI.  
  
---  
  
## File Structure (After Refactoring)  
  
```  
media_entity_spotify/  
├── config/  
│   ├── install/  
│   │   └── media_entity_spotify.settings.yml  
│   └── schema/  
│       └── media_entity_spotify.schema.yml  
├── images/  
│   └── icons/  
│       └── spotify.png  
├── src/  
│   └── Plugin/  
│       ├── Field/  
│       │   └── FieldFormatter/  
│       │       └── SpotifyEmbedFormatter.php  [UPDATED: Annotation → Attribute]  
│       └── media/  
│           └── Source/  
│               └── Spotify.php  [NEW: MediaSource plugin]  
├── templates/  
│   └── media-spotify-embed.html.twig  
├── media_entity_spotify.info.yml  [UPDATED]  
├── media_entity_spotify.install   [UPDATED: Fixed deprecated functions]  
├── media_entity_spotify.module  
└── media_entity_spotify.theme.inc  
```  
  
---  
  
## How to Use the Module  
  
### 1. Create a Media Type  
  
Navigate to: `/admin/structure/media/add`  
  
- **Name:** Spotify (or your choice)  
- **Media source:** Select "Spotify"  
- **Source field:** Choose which field will store the Spotify URL  
  - Can be: String, String (long), or Link field  
  
### 2. Configure Display  
  
Go to: Manage display for your media type  
  
- Select the source field  
- Choose formatter: **"Spotify embed"**  
- Configure settings:  
  - **Playlist/Album settings:** Theme, view type, width, height  
  - **Track settings:** Theme, view type, width, height  
  
### 3. Add Spotify Content  
  
Create media items with Spotify URLs:  
- **Track:** `https://open.spotify.com/track/4tozzHVS3vnc8xks2PekDr`  
- **Playlist:** `https://open.spotify.com/playlist/0bXZMCsiOoESIuMBXU45gX`  
- **Album:** `https://open.spotify.com/album/{id}`  
- **Artist:** `https://open.spotify.com/artist/{id}`  
- **Show:** `https://open.spotify.com/show/{id}`  
- **Episode:** `https://open.spotify.com/episode/{id}`  
  
---  
  
## Technical Improvements  
  
### Modern PHP 8 Features  
- ✅ PHP 8 Attributes instead of annotations  
- ✅ Typed properties  
- ✅ Constructor property promotion (where appropriate)  
- ✅ Null coalescing and null-safe operators  
  
### API Modernization  
- ✅ Replaced deprecated `file_unmanaged_save_data()` with `FileSystemInterface::saveData()`  
- ✅ Replaced deprecated `drupal_get_path()` with Extension List service  
- ✅ Updated to use core Media module APIs  
- ✅ Proper dependency injection in plugin constructor  
  
### Code Quality  
- ✅ Added proper type hints throughout  
- ✅ Improved error handling with try-catch blocks  
- ✅ Added logging for file operation failures  
- ✅ Better documentation in docblocks  
  
---  
  
## Testing Checklist  
  
After refactoring, verify:  
  
- [ ] Module installs without errors  
- [ ] Icons are copied to `public://media-icons/generic/`  
- [ ] Can create a "Spotify" media type  
- [ ] Can configure source field on media type  
- [ ] Can add media items with Spotify URLs  
- [ ] Track URLs render correctly  
- [ ] Playlist URLs render correctly (both old and new formats)  
- [ ] Album URLs render correctly  
- [ ] Thumbnails are downloaded and cached  
- [ ] Formatter settings work (theme, view, width, height)  
- [ ] Different view modes work (list vs cover art)  
- [ ] Query parameters in URLs are handled (e.g., `?si=xxx`)  
  
---  
  
## Configuration Schema Reference  
  
### Module Settings  
```yaml  
media_entity_spotify.settings:  
  thumbnail_destination: 'public://spotify'  
```  
  
### Media Source Configuration  
```yaml  
media.source.spotify:  
  source_field: 'field_media_spotify_url'  # Machine name of your source field  
```  
  
### Formatter Settings  
```yaml  
field.formatter.settings.spotify_embed:  
  playlist:    theme: 'dark'      # Options: 'dark', 'white'    view: 'list'       # Options: 'list', 'coverart'    width: '300px'    height: '380px'  track:    theme: 'dark'    view: 'list'    width: '300px'    height: '80px'     # Fixed at 80px for list view  
```  
  
---  
  
## Known Spotify URI Formats  
  
The module now supports these Spotify URI formats:  
  
| Content Type | URL Format | Spotify URI |  
|-------------|------------|-------------|  
| Track | `/track/{id}` | `spotify:track:{id}` |  
| Album | `/album/{id}` | `spotify:album:{id}` |  
| Playlist (new) | `/playlist/{id}` | `spotify:playlist:{id}` |  
| Playlist (old) | `/user/{user}/playlist/{id}` | `spotify:user:{user}:playlist:{id}` |  
| Artist | `/artist/{id}` | `spotify:artist:{id}` |  
| Show/Podcast | `/show/{id}` | `spotify:show:{id}` |  
| Episode | `/episode/{id}` | `spotify:episode:{id}` |  
  
---  
  
## Dependencies  
  
```yaml  
dependencies:  
  - media  # Core Media module (included in Drupal core since 8.4)  
```  
  
**No contrib modules required!** The module now works entirely with Drupal core.  
  
---  
  
## Compatibility  
  
- ✅ **Drupal:** 11.x  
- ✅ **PHP:** 8.1+  
- ✅ **Media module:** Core (8.4+)  
  
---  
  
## Migration Notes  
  
If upgrading from the old Drupal 8 version:  
  
1. **Backup your database** before updating  
2. Existing media items should continue to work  
3. The old MediaType plugin is no longer used - the new MediaSource plugin will handle all requests  
4. Configuration keys have changed but media entities themselves are compatible  
5. Clear all caches after updating: `drush cr`  
  
---  
  
## Summary  
  
This refactoring successfully modernizes the `media_entity_spotify` module for Drupal 11 by:  
  
1. Converting from contrib `media_entity` to core `media` module  
2. Updating to PHP 8 attributes  
3. Fixing deprecated function calls  
4. Supporting modern Spotify URL formats  
5. Improving error handling and code quality  
6. Maintaining backward compatibility where possible  
  
The module is now fully compatible with Drupal 11 and uses modern best practices!  
  
---  
  
**Refactoring completed:** December 3, 2025  
**Drupal version:** 11.x  
**PHP version:** 8.1+