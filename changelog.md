# Zepben Powerfactory Exporter changelog
## [0.2.0] - UNRELEASED
### New Features
- Added `line_weakener`, which creates a mutator that reduces the amp rating of lines via a catalogue of line types.
- Added `transformer_weakener`, which creates a mutator that reduces the VA rating of transformers via a catalogue of
  transformer models.
- Added `composite_mutator`, which combines multiple mutator functions together in sequence to form a new mutator.
### Breaking Changes
- The `seed` parameter has been moved to the usage point allocator creator.

## [0.1.0] - 2022-10-04
### Initial release
- Added create_synthetic_feeder which replaces a proportion of NMIs on an existing feeder with a given set of NMIs
