# Mie Scattering Phase Function Examples

This document provides examples of using the Mie scattering phase function plugin in Mitsuba 3.

## Basic Usage

### Python API

```python
import mitsuba as mi
mi.set_variant('scalar_rgb')

# Create a Mie phase function for water droplets in air
mie_phase = mi.load_dict({
    'type': 'mie',
    'radius': 500e-9,  # 500 nm radius particles
    'ior': 1.33        # Water droplets in air
})

# For smaller particles (Rayleigh regime)
small_particles = mi.load_dict({
    'type': 'mie',
    'radius': 50e-9,   # 50 nm radius (approaches Rayleigh scattering)
    'ior': 1.33
})

# For larger particles (stronger forward scattering)
large_particles = mi.load_dict({
    'type': 'mie',
    'radius': 5e-6,    # 5 μm radius particles 
    'ior': 1.33
})
```

### XML Scene Description

```xml
<scene version="3.0.0">
    <medium type="homogeneous">
        <rgb name="albedo" value="0.9, 0.9, 0.9"/>
        <phase type="mie">
            <float name="radius" value="500e-9"/>
            <float name="ior" value="1.33"/>
        </phase>
    </medium>
    
    <!-- Rest of scene description -->
</scene>
```

## Polarized Rendering

For polarized light transport, use one of the polarized variants:

```python
import mitsuba as mi
mi.set_variant('scalar_spectral_polarized')

# Mie scattering with full Mueller matrix support
mie_polarized = mi.load_dict({
    'type': 'mie',
    'radius': 1e-6,    # 1 μm particles
    'ior': 1.5         # Glass particles
})
```

## Parameter Guidelines

### Particle Radius
- **50-100 nm**: Rayleigh regime, similar to molecular scattering
- **200-800 nm**: Transition regime, strong wavelength dependence  
- **1-10 μm**: Mie regime, pronounced forward scattering
- **>10 μm**: Geometric scattering regime

### Refractive Index
- **1.33**: Water droplets in air (clouds, fog)
- **1.4-1.6**: Glass or plastic particles
- **2.0+**: High-index materials (diamond, some crystals)

## Physical Applications

### Atmospheric Scattering
```python
# Blue sky (molecular Rayleigh scattering)
atmosphere = mi.load_dict({
    'type': 'mie',
    'radius': 30e-9,   # Effective molecular size
    'ior': 1.0003      # Air molecules
})

# Cloud droplets
cloud = mi.load_dict({
    'type': 'mie', 
    'radius': 10e-6,   # 10 μm water droplets
    'ior': 1.33
})
```

### Industrial Applications
```python
# Powder coating particles
powder = mi.load_dict({
    'type': 'mie',
    'radius': 30e-6,   # 30 μm polymer particles
    'ior': 1.55
})

# Aerosol particles
aerosol = mi.load_dict({
    'type': 'mie',
    'radius': 200e-9,  # 200 nm particles
    'ior': 1.4
})
```

## Implementation Notes

This implementation provides:
- Smooth transition between Rayleigh and Mie regimes based on size parameter
- Full Mueller matrix support for polarized rendering
- Wavelength-dependent scattering for spectral variants
- Proper importance sampling for efficient rendering

The algorithm is based on Mie scattering theory with simplified series computation 
suitable for real-time rendering applications.