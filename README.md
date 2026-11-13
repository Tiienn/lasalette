# Arvin Raggoo Villa – 3D walkthrough

Ground-floor walkthrough built from the floor plan screenshot. Same pipeline idea as Orchard S12,
rebuilt from scratch (the original folder was not reachable when this was made).

## Pipeline

| Step | File | What it does |
|---|---|---|
| 1 | `src/build.py` | House shell from the plan: walls, openings, floors, stair, terrace, pool, site → `build/shell.blend` |
| 2 | `src/fitout.py` | Furniture, kitchen, bathroom, planting, light fittings → `build/house.blend` |
| – | `src/nodes.json` | Viewpoints, links between them, room labels/areas, mini-map extents |
| 3 | `src/render.py` | Cycles renders: 360° cube panoramas (2048 px faces, 128 samples), plan view, flat test views |
| 4 | `src/grade.py` | Colour grade, JPEG faces, thumbnails, mini map, `web/tour.json` |
| – | `web/index.html` | Three.js viewer: views list, mini map with room areas, Day/Dusk switch, full screen, phone layout |

`src/common.py` holds the shared geometry helpers and procedural materials (no image textures needed).

## Run on the Mac

Needs Blender 4.2 or newer and `pip3 install pillow numpy`.

```bash
./run.sh test     # model + plan view + 3 quick check views
./run.sh          # everything: 11 views x 6 faces x 2 lighting variants = 132 renders
```

The panorama render can be stopped and restarted; finished faces are skipped (`--force` re-renders).
Render only some views: `blender -b -P src/render.py -- --mode pano --nodes living,pool --variant day`.

Preview: `cd web && python3 -m http.server 8000`, open http://localhost:8000.
Deploy: `cd web && npx vercel --prod --name lasalette`.

## Dimensions used (metres)

Origin = outer south-west corner of the house, +X east, +Y north (pool side). Ceiling 2.7.

| Space | Size | Area m² |
|---|---|---|
| Living / dining / kitchen | 9.65 × 5.50 | 53.1 |
| Bedroom (incl. wardrobe) | 3.60 × 3.60 | 13.0 |
| Bath / toilet | 1.65 × 2.58 | 4.3 |
| Store | 0.805 × 1.28 | 1.0 |
| Stair and hall | ~3.6 × 3.5 | ~12 |
| Covered terrace | 8.67 × 3.52 | 30.5 |
| Pool | 6.0 × 3.0 | 18.0 |

## Assumptions to confirm

- Upper storey is a plain placeholder volume (no upper plan yet); the tour stays on the ground floor.
- Sun is in the northern sky (north = pool side), about 52° high for the Day variant.
- Entry is the 2.18 m glazed unit on the front wall: glazed door leaf on the west, fixed sidelight on the east.
- Store door faces north into the hall.
- Window sill and head heights, joinery, furniture styles and colours are design choices, not from the plan.
