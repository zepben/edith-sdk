# Zepben Powerfactory Exporter changelog
## [0.2.0] - UNRELEASED
### New Features
- Added `line_weakener`, which creates a mutator that reduces the amp rating of lines via a catalogue of line types.
- Added `transformer_weakener`, which creates a mutator that reduces the VA rating of transformers via a catalogue of
  transformer models.
### Breaking Changes
- The `seed` parameter has been moved to the usage point allocator creator.
- The `create_synthetic_feeder` method now returns the set of mRIDs of the modified network objects.

## [0.1.0] - 2022-10-04
### Initial release
- Added create_synthetic_feeder which replaces a proportion of NMIs on an existing feeder with a given set of NMIs
