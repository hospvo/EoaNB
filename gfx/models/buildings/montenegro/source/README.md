# Biljarda, Cetinje

Original 3D game asset for EoaNB, representing the residence around 1857.
This is a map-scale reconstruction, not a measured architectural survey.

Features: two-storey limestone residence with deeper end pavilions, four round
corner towers, lead-sheet hipped roofs, enclosing walls and an open arched gate,
separate window surrounds, dark red-brown shutters, chimneys and two court wells.
The later relief-map pavilion, modern landscaping and museum additions are absent.
No national flag is baked into the model.

Historical references:
- Montenegro Academy of Sciences, dimensions and overall composition:
  https://leks.canu.ac.me/web/lcd.php?OID=4642
- National Museum of Montenegro, plan on the final page:
  https://narodnimuzej.me/wp-content/uploads/2020/09/Biljarda-CG.pdf
- Cultural Heritage Administration, lead roof and later alterations:
  https://www.gov.me/clanak/biljardi-potvrden-status-kulturnog-dobra-od-nacionalnog-znacaja

The enclosure proportions, smaller details and material tones are interpreted
for map readability. Modern reference photographs are used for masonry and
architectural details; they do not establish every detail of the 1857 appearance.

## Editing and rebuilding

Import `MNT_biljarda.obj` into Blender with its MTL and PNG to edit the geometry.
OBJ dimensions are approximate metres, with Y as up. Native map export uses
0.028 / 0.065 / 0.023 map units per metre on X / Y / Z: height is exaggerated and
the courts compressed for readability beside the game's generic buildings.
The OBJ, recipe and source textures are not loaded by
the game. Runtime uses only the parent directory's mesh and three DDS maps.

Rebuild with Python 3, numpy, Pillow and scipy:

    python build_biljarda.py

The original generated material atlas is `biljarda_materials.png`. Its generation
prompt is preserved in `material-prompt.txt`. Normal and specular maps, palette
swatches, mipmaps, geometry and UVs are derived by the build script.

## Game integration

`landmark_mnt_biljarda` is a non-buildable landmark with +3% political power gain
for a Montenegrin controller and no DLC requirement. Its modifier is displayed
in the building UI, with a dedicated two-frame map icon. A dedicated spawn point
is placed in province 9821 (Cetinje),
state 942. A separate startup hook adds one level once per save. The model stays
with the site when ownership changes. Existing building types are not overridden.

The heightmap-fitted retaining terrace and entry stairs are built for the fixed
site recorded in `map-placement.json`, currently X 3102.10, Y 14.24, Z 1371.50,
rotation zero. The level court sits above the sampled terrain maximum; its lower
foundation follows the slope. Moving or rotating it requires rebuilding the
foundation and updating the marker together. Nearby shared-industry visual slots
in state 942 are moved into province 13780 to leave a clear civic landmark.
No building levels or production statistics are changed by the marker moves.
The Cetinje supply-node visual marker is also separated from the landmark at
X 3099.10, Y 14.10, Z 1372.00, still in its original province 9821. Its supply
function and building level are unchanged. The residence now uses fewer facade
windows at map scale, softer material contrast and a side entry by its end wing.
These are deliberate visual simplifications rather than surveyed details.

Validation: binary mesh round-trip, finite vectors and indices, normal/tangent
normalization, UV bounds, full DDS mip chains and isolated software renders.
An isolated vanilla boot loaded the model definitions without a Biljarda mesh or
material error. It revealed a missing spawn-marker entity; the matching entity
has been added. The test instance was stopped to avoid interrupting another mod.
A subsequent in-game screenshot showed the initial flat court intersecting the
hillside. The revised model has been checked with software rendering against the
actual EoaNB heightmap, including the complete court and terrain-following base.
Its final appearance under the game's lighting still requires an in-game check.
