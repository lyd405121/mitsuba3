# BDPT Implementation for Mitsuba 3

## Overview

This implementation adds bidirectional path tracing (BDPT) to Mitsuba 3, providing a new integrator that can handle complex lighting scenarios more efficiently than standard path tracing.

## Implementation Details

### Core Features

1. **Bidirectional Path Generation**
   - Camera paths: Standard path tracing from the camera/sensor
   - Light paths: Paths traced from light sources using `scene->sample_emitter_ray()`

2. **Path Connection**
   - Direct connections between camera and light path vertices
   - Visibility testing with shadow rays
   - BSDF evaluation at connection points

3. **Multiple Importance Sampling (MIS)**
   - Power heuristic for weighting different sampling strategies
   - Proper handling of Dirac delta distributions

### Technical Implementation

- **Base Class**: Inherits from `MonteCarloIntegrator`
- **Registration**: Uses Mitsuba's plugin system with `MI_EXPORT_PLUGIN`
- **Compilation**: Added to CMakeLists.txt as a standard plugin
- **Configuration**: Supports standard parameters (max_depth, rr_depth, hide_emitters)

### Files Added/Modified

1. `src/integrators/bdpt.cpp` - Main BDPT implementation
2. `src/integrators/CMakeLists.txt` - Added bdpt plugin target
3. `src/integrators/tests/test_bdpt.py` - Test suite for BDPT
4. `mitsuba.conf` - Configuration for scalar_rgb variant

### Usage

```xml
<integrator type="bdpt">
    <integer name="max_depth" value="8"/>
    <integer name="rr_depth" value="5"/>
    <boolean name="hide_emitters" value="false"/>
</integrator>
```

```python
scene_dict['integrator'] = {
    'type': 'bdpt',
    'max_depth': 8
}
```

## Build Instructions

1. Configure with CMake:
```bash
mkdir build && cd build
cmake .. -DMI_ENABLE_EMBREE=OFF -DMI_ENABLE_CUDA=OFF
```

2. Build the BDPT plugin:
```bash
make bdpt -j4
```

3. Verify plugin creation:
```bash
ls plugins/bdpt.so
```

## Testing

The implementation includes comprehensive tests:

- Basic integrator registration and loading
- Comparison with path tracer output
- Multiple depth configurations
- Cornell box rendering validation

## Current Limitations

1. **Medium Support**: Currently limited to surface scattering (no participating media)
2. **Light Path Depth**: Currently implements single-bounce light paths
3. **MIS Optimization**: Basic MIS implementation, could be enhanced for more strategies

## Future Enhancements

1. **Full BDPT**: Implement multi-bounce light paths with full vertex connection matrix
2. **Volume Support**: Add participating media support
3. **Performance**: Optimize light path storage and connection algorithms
4. **Spectral**: Enhanced support for spectral and polarized variants

## Verification

The BDPT integrator has been successfully:
- ✓ Compiled and linked as a plugin
- ✓ Integrated with Mitsuba's plugin system
- ✓ Tested with Cornell box scenes
- ✓ Validated against path tracer baseline

## Performance Characteristics

BDPT is particularly effective for:
- Scenes with difficult lighting (caustics, indirect illumination)
- Complex geometry with occluded light sources
- SDS (Specular-Diffuse-Specular) paths
- Scenes where path tracing produces high variance