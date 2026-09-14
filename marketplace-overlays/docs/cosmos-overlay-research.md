# Living Cosmos overlay research

## Species reference

The overlay models *Cosmos bipinnatus*, an annual in the Asteraceae family. The visual target is an airy, branching group rather than a dense shrub.

- Smooth green stems may carry a reddish or burgundy cast. Tall, slender stems need flexible bending rather than rigid rotation.
- Leaves are opposite, deeply divided, and threadlike. Their fine silhouette is one of the clearest ways to distinguish cosmos from a generic daisy.
- Each apparent flower is a solitary capitulum on a long peduncle. Reference descriptions place heads around 3–6 cm across, with pink, reddish-pink, purple, or white rays and a yellow disc.
- The default flower uses eight broad ray florets with gently notched, irregular tips. The center is rendered as many small spiral-packed disc florets rather than one flat yellow circle.
- Narrow green involucral bracts remain visible behind the ray florets. Spent heads become brown seed structures rather than simply fading away.

Primary references:

- Royal Botanic Gardens, Kew, Plants of the World Online: *Cosmos bipinnatus* taxonomy, habit, capitulum size, peduncle length, ray colors, and fruit morphology.
- North Carolina Extension Gardener Plant Toolbox: opposite, pinnatisect, deeply cut threadlike leaves and smooth green to burgundy stems.
- Missouri Botanical Garden Plant Finder: upright 2–4 foot habit, airy finely cut foliage, 2–4 inch daisy-like heads, and continued flowering after spent heads are removed.

## Eight-hour overlay lifecycle

The eight-hour shift is an artistic time compression, not a claim that a real cosmos completes these events in eight hours.

1. The branching plant begins at 84% height and slowly extends through its first shift. Its shared skeleton stays in place as individual flower heads cycle.
2. Flower heads have deterministic phase offsets. Buds, open flowers, fading blooms, and seed heads therefore coexist naturally.
3. A replacement bud emerges from an upper node while the older head fades.
4. The old head loses saturation, droops, and becomes a seed head. The successor bud swells before the next cycle begins.
5. The start time is stored locally so closing, refreshing, or reopening the overlay does not reset the shift.

## Motion model

- The plant is rooted below the lower-right screen edge. All stems lean inward so flower heads remain inside the desktop.
- Ambient motion combines two low-amplitude frequencies to avoid a repetitive pendulum effect.
- There is one main stem. Paired side shoots emerge from leafy junctions, and further flower stalks fork from those shoots. The count controls the number of terminal flower sites, not separate stems rooted at the screen bottom.
- Each branch attaches to its parent's live curve. A damped spring controls the main stem; smaller branch springs inherit that movement and transmit part of a cursor impulse back into the parent plant.
- Thin stems bend more visibly at their tips while their bases remain fixed. Movement settles gradually without wobbling indefinitely.

## Rendering cues

- Front and rear stems are sorted by depth and vary slightly in scale and opacity.
- Petals use multi-stop color gradients, fine longitudinal veins, irregular tips, and small head tilts.
- Disc florets use a golden-angle spiral with several yellow and ochre values.
- Stem highlights, muted translucency, and subtle color variation prevent the plant from reading as a flat icon.
- Leaf strokes are batched to keep the transparent overlay responsive at the maximum stem count.
# Color refinement

The default patch mixes white, pale blush, shell pink, rose, deep magenta, and crimson-red flowers. This stays within the documented *Cosmos bipinnatus* range: North Carolina Extension lists maroon, pink, lavender, and white, while Missouri Botanical Garden describes red, pink, or white rays with yellow disc centers. Orange and yellow are excluded because those are characteristic of *Cosmos sulphureus* rather than this pink garden-cosmos study.

The selectable *Cosmos sulphureus* form couples its yellow, gold, orange, and scarlet-orange rays with the species' opposite pinnatifid leaves. The reference rendering uses a branching compound blade with many solid, pointed lanceolate lobes. They remain airy but are visibly broader than the hairlike bipinnate segments drawn for *C. bipinnatus*. Source: North Carolina Extension, `https://plants.ces.ncsu.edu/plants/cosmos-sulphureus/`, supplemented by the user's foliage photograph.

The user's white garden-cosmos photograph is the primary visual morphology reference for *C. bipinnatus*: eight broad ray florets with shallow lobed tips and fine longitudinal veins, dense yellow disc florets, rounded buds enclosed by long pointed green bracts, upright slender stems, and dense threadlike divisions in the foliage. Flower color remains independently variable within the documented species range.
