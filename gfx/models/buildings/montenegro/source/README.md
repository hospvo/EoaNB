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
OBJ dimensions are approximate metres, with Y as up. Native mesh export uses
0.045 map units per metre. The OBJ, recipe and source textures are not loaded by
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

Validation: binary mesh round-trip, finite vectors and indices, normal/tangent
normalization, UV bounds, full DDS mip chains and isolated software renders.
An isolated vanilla boot loaded the model definitions without a Biljarda mesh or
material error. It revealed a missing spawn-marker entity; the matching entity
has been added. The test instance was stopped to avoid interrupting another mod.
The corrected placement, runtime visibility, terrain seating and map scale still
require an in-game check in EoaNB.
