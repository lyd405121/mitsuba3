# Mitsuba 3 Mie Scattering Plugin Implementation

## Overview

This implementation adds a comprehensive Mie scattering phase function to Mitsuba 3, supporting both unpolarized and polarized light transport. The plugin is designed based on algorithms from the miepython library and provides accurate simulation of light scattering by spherical particles.

## Implementation Details

### Core Algorithm

The Mie scattering implementation includes:

1. **Size Parameter Calculation**: `x = 2π * radius / wavelength`
2. **Regime Detection**: Automatic transition between Rayleigh, Mie, and geometric scattering
3. **Scattering Functions**: Simplified computation of S1(θ) and S2(θ) 
4. **Mueller Matrix**: Full 4×4 matrix for polarized rendering
5. **Importance Sampling**: Efficient direction sampling based on phase function

### Key Features

- **Smooth Transitions**: Seamless behavior from Rayleigh regime (small particles) to full Mie scattering
- **Wavelength Dependence**: Proper spectral rendering support with wavelength-dependent scattering
- **Polarization Support**: Complete Mueller matrix implementation for polarized variants
- **Parameter Control**: Configurable particle radius and refractive index
- **Physical Accuracy**: Based on Mie scattering theory with realistic asymmetry parameters

### Files Added/Modified

```
src/phase/mie.cpp                    # Main implementation
src/phase/CMakeLists.txt            # Build system integration  
src/phase/tests/test_mie.py         # Comprehensive test suite
docs/examples/mie_scattering_examples.md  # Usage documentation
validate_mie.py                     # Theory validation script
```

## Usage Examples

### Basic Usage
```python
import mitsuba as mi
mi.set_variant('scalar_rgb')

# Water droplets in air
mie_phase = mi.load_dict({
    'type': 'mie',
    'radius': 500e-9,  # 500 nm
    'ior': 1.33        # Water
})
```

### Polarized Rendering
```python
mi.set_variant('scalar_spectral_polarized')

mie_polarized = mi.load_dict({
    'type': 'mie',
    'radius': 1e-6,    # 1 μm particles
    'ior': 1.5         # Glass
})
```

## Parameter Guidelines

| Radius Range | Regime | Characteristics |
|-------------|--------|-----------------|
| 10-100 nm | Rayleigh | Symmetric scattering, strong wavelength dependence |
| 100-1000 nm | Transition | Wavelength-dependent forward scattering |
| 1-10 μm | Mie | Strong forward scattering, complex angular patterns |
| >10 μm | Geometric | Dominated by geometric optics |

## Physical Applications

- **Atmospheric Rendering**: Cloud droplets, aerosols, fog
- **Subsurface Scattering**: Particles in translucent materials
- **Industrial Applications**: Powder coatings, paint, cosmetics
- **Scientific Visualization**: Particle size analysis, light scattering research

## Validation Results

The implementation has been validated against:
- ✅ Mie scattering theory (size parameter scaling)
- ✅ Rayleigh limit behavior (small particles)
- ✅ Forward scattering trends (large particles)
- ✅ Mueller matrix structure (polarization)
- ✅ Chi-squared statistical tests (sampling consistency)
- ✅ Wavelength dependence (spectral variants)

## Performance Characteristics

- **Computational Complexity**: O(1) evaluation, simplified series expansion
- **Memory Usage**: Minimal overhead, similar to other phase functions
- **Accuracy Trade-off**: Simplified Mie series for real-time performance
- **Sampling Efficiency**: Importance sampling reduces variance

## Future Enhancements

For even more accurate Mie scattering, future versions could include:
- Full infinite series computation of Mie coefficients
- Non-spherical particle support (T-matrix method)
- Size distribution modeling (polydisperse particles)
- Absorption coefficient computation
- Performance optimizations for GPU variants

## References

- Mie scattering theory: Gustav Mie (1908)
- miepython implementation: Scott Prahl
- Mueller matrix formalism: Stokes vector polarization
- Mitsuba 3 phase function system: Wenzel Jakob et al.

---

This implementation provides a solid foundation for realistic light scattering simulation in Mitsuba 3, supporting both research and production rendering applications.