# Zepben Powerfactory Exporter changelog
## [0.4.0] - UNRELEASED
### Breaking Changes
* None.

### New Features
* None.

### Enhancements
* None.

### Fixes
* None.

### Notes
* None.

## [0.3.0] - 2023-10-10
### Breaking Changes
* None.

### New Features
* Added support for SDK 0.35.0

### Enhancements
* None.

### Fixes
* None.

### Notes
* None.

## [0.2.1] - 2022-11-09
### Fixes
* `create_synthetic_feeder` will now throw an exception if the gRPC call failed.


## [0.2.0] - 2022-10-25
### New Features
- Added `line_weakener`, which creates a mutator that reduces the amp rating of lines via a catalogue of line types.
- Added `transformer_weakener`, which creates a mutator that reduces the VA rating of transformers via a catalogue of
  transformer models.

### Breaking Changes
- The `seed` parameter has been moved to the usage point allocator creator.
- The `create_synthetic_feeder` method no longer returns anything. Each mutator function creator takes a callback to use
  on a collection of information about the modified objects. The structure of this collection may vary between each
  mutator.
- `create_synthetic_feeder` now takes multiple mutator functions in the `mutators` parameter.

## [0.1.0] - 2022-10-04
### Initial release
- Added create_synthetic_feeder which replaces a proportion of NMIs on an existing feeder with a given set of NMIs
