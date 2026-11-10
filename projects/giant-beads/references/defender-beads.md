# Defender bead pair — references and decisions

## References

- Principal-supplied profile drawing.
- Principal-supplied side photo: `https://monarchdefender.com/_next/image?url=https%3A%2F%2Fimg.monarchdefender.com%2Fmedia%2F1772728604357-peutzg-dark-knight-side.webp.webp&w=828&q=75`
- Blueprint side view: `https://www.the-blueprints.com/blueprints-depot-restricted/cars/landrover/land_rover_defender_90_1990-83624.jpg`
- Four-view floorplan: `https://freecadfloorplans.com/wp-content/uploads/2023/05/land-rover-defender.jpg.webp`

## Decisions

- **Profile**: 120 mm vehicle length, 58 mm silhouette height, 30 mm bead
  thickness. Side outline is the body polygon unioned with the two tyre
  circles and the rear spare wheel. Steel wheels are etched, not raised.
- **Rear**: 120 mm vehicle width, 128 mm silhouette height, 30 mm bead
  thickness. Body is a chamfered box unioned with the two rear tyre
  circles; spare wheel and rear-door detail are etched.
- **Fillets**: default 4 mm quarter-round face/bottom fillet, compared
  with the letter bead's 10 mm; exposed in the app for calibration.
- **Etches**: 0.8 mm wide grooves, 0.6 mm deep by default, mirrored on the
  front and build-plate faces. `detail_relief` scales depth.
- **Hole**: plain 20 mm bore along X, leaving 5 mm above/below on the
  30 mm body.
