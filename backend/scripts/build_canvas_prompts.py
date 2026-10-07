"""Build the reviewed 500-prompt exhibition manifest without network calls."""
import json
from pathlib import Path

SUBJECTS = """a red panda repairing a tiny mechanical clock on a workbench
a transparent jellyfish drifting above a deep ocean vent
a ceramic teapot shaped like a sleeping badger on a linen table
a red tram crossing a rainy cobblestone intersection
a dancer balancing a long vermilion silk ribbon in an empty studio
a cross section of a pomegranate with seeds like polished rubies
a lighthouse built from stacked books on a floating stone
a satellite unfolding its solar wings above a cratered moon
a violin and bow resting against a burgundy velvet chair
a busy rooftop vegetable garden above a dense city
a horseshoe crab walking over patterned wet sand
a glassblower shaping a luminous orange vessel in a dark workshop
a chessboard whose pieces are tiny fantastical buildings
a steam locomotive emerging from a snow tunnel
a pair of kingfishers diving toward concentric water ripples
a spiraling staircase seen directly from underneath
a street market of handwoven baskets and woven rugs
a close view of frost crystals on a scarlet maple leaf
a deep sea research submersible beside a giant tube sponge
a small bakery with a round oven and freshly braided bread
a kinetic mobile of balanced copper rings and blue spheres
a camel caravan reflected in a salt flat under pink clouds
a chameleon gripping a striped branch with its curled tail
a hot air balloon shaped like a pear floating above patchwork farms
a collection of antique cameras arranged on mustard yellow fabric
a hillside amphitheater with concentric seats and one lone cellist
a cutaway of a beehive with hexagonal golden chambers
a cargo airship docking at a tower in a cloud city
a dragonfly resting on a purple iris beside a still pond
a blacksmith forging a horseshoe with sparks flying outward
a coral pink seashell seen as a mathematical spiral
a friendly robot tending mushrooms in a subterranean greenhouse
a pair of ballet shoes and scattered rehearsal notes on a wooden floor
a canyon of red basalt viewed from a narrow suspension bridge
a snow leopard sleeping on a dark granite ledge
a blue enamel coffee pot and three oranges on a white windowsill
a ringed planet rising behind an alien landscape of black spires
a potter's hands opening a bowl on a spinning wheel
a great horned owl reflected in the circular window of a barn
a vintage racing bicycle parked beside a climbing rose wall
a microscopic diatom with intricate radial silica patterns
a harbor crane lifting a bright red shipping container at dawn
a hummingbird approaching a hanging fuchsia blossom
a cathedral organ whose pipes resemble a silver forest
a desert camp with indigo tents beneath an enormous crescent moon
a collection of mineral specimens arranged like an exploded sculpture
a pianist playing a grand piano in a flooded mirrored room
a snail crossing the curved handle of a watering can
a festival parade of giant folded origami animals
a spherical underwater library lit by suspended lanterns
a toucan perched beside a split papaya in a tropical canopy
a close-up of a watch movement with ruby bearings and brass gears
a sail-powered vehicle crossing an ochre salt desert
a tailor's cutting table with scarlet cloth and golden scissors
a family of capybaras sheltering beneath an oversized lotus leaf
a terraced tea plantation seen through a circular stone doorway
a kaleidoscopic arrangement of stained glass shards on black velvet
a tiny astronaut planting a flag on a giant strawberry
a flamingo standing among geometric reflections in pale pink water
a wooden puppet theater with a miniature dragon on its stage
a cutaway of a nautilus submarine with cozy glowing cabins
a percussion ensemble of colorful drums in a sunlit plaza
a meteorite displayed in an obsidian chamber with a shaft of light
a library cat asleep inside an open atlas
a silver cable car passing over a steep hillside town
a sea turtle swimming through a cathedral of kelp fronds
a candlelit still life of figs, grapes and a pewter jug
a wind sculpture made from hundreds of suspended red feathers
a rowing team viewed from directly overhead on dark water
a fox curling its tail around a lantern in a snowy orchard
a futuristic railway station carved into a rose quartz cavern
a circular weaving loom threaded with vivid rainbow wool
a hermit crab wearing a shell like a miniature pagoda
a night flower market lit by violet lamps and paper moons
a flock of starlings forming a sweeping ribbon above a water tower
a delicate porcelain dragon coiled around a celadon vase
a split-level tree house wrapped around an immense baobab
a butterfly emerging from a translucent chrysalis on a reed
a solar-powered boat traveling through a maze of reed channels
a close portrait of a white horse with a braided black mane
a sculptural fountain of intersecting marble discs in a red courtyard
a shoemaker's bench with hand tools and a half-finished leather boot
a cutaway of an ant colony beneath a field of yellow flowers
a comet streaming across a sky above a radio telescope array
a playground built from gigantic musical instruments
a cluster of luminous mushrooms growing from a fallen chess king
a gecko walking across a cracked cobalt blue ceramic tile
a huge mobile planetarium inside an abandoned railway depot
a still life of violet artichokes beside a polished copper saucepan
a giraffe leaning down to inspect a tiny yellow umbrella
a hand-built wooden canoe hanging inside a boatbuilder's shed
a harp whose strings catch droplets from a passing rain shower
a magnified snowflake suspended against a deep plum background
a pedestrian bridge woven from living roots above a red river
a folded paper whale suspended in a minimalist gallery
a small orange octopus exploring a sunken brass astrolabe
a woman in a wide red hat observing a colossal abstract sculpture
a pair of puffins nesting in a cliff crevice over a gray sea
a copper espresso machine in a jewel-like midnight cafe
a terrarium containing a miniature volcanic island and a blue lake""".splitlines()

STYLES = [
    "a precise colored-pencil drawing on textured ivory paper",
    "a bold woodcut print with strongly carved shapes",
    "a playful stop-motion clay scene with tactile handmade surfaces",
    "a luminous editorial photograph with realistic materials",
    "a graphic gouache painting with flat forms and expressive brushwork",
    "a delicate ink wash with large areas of negative space",
    "a richly detailed wool tapestry with visible woven threads",
    "a sculptural layered-paper diorama with deep cast shadows",
    "a dramatic oil painting with thick impasto highlights",
    "a stained-glass mosaic with sharp tessellated contours",
]
PALETTES = ["crimson, charcoal and ivory", "cobalt, lemon and white", "violet, copper and cream",
            "forest green, coral and pale pink", "black, silver and electric blue",
            "terracotta, sage and warm white", "magenta, midnight blue and orange",
            "ochre, plum and pearl", "indigo, vermilion and pale gray", "lime, aubergine and sand"]
COMPOSITIONS = ["asymmetric composition with the subject on the left", "low viewpoint and a strong diagonal composition",
                "intimate close framing with a clear focal point", "wide composition with generous negative space",
                "high viewpoint with rhythmic geometric shapes"]


def manifest():
    assert len(SUBJECTS) == len(set(SUBJECTS)) == 100
    prompts = []
    for variant in range(5):
        for index, subject in enumerate(SUBJECTS):
            style = STYLES[(index + variant * 3) % len(STYLES)]
            palette = PALETTES[(index * 3 + variant) % len(PALETTES)]
            composition = COMPOSITIONS[(index + variant) % len(COMPOSITIONS)]
            prompts.append(f"Create {style} depicting {subject}. Use {composition}. "
                           f"A deliberate palette of {palette}; distinctive lighting and clear silhouettes. "
                           "One coherent square artwork, not a collage or a grid. "
                           "No text, captions, logos, signatures or watermarks.")
    assert len(prompts) == len(set(prompts)) == 500
    return {"batch": "canvas-diversity-500-20261007", "target": 500, "quality": "low",
            "size": "1024x1024", "prompts": prompts}


if __name__ == "__main__":
    output = Path(__file__).with_name("canvas_prompts_500.json")
    output.write_text(json.dumps(manifest(), ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote 500 unique prompts to {output}")
