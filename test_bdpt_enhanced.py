#!/usr/bin/env python3

"""
Simple test script to verify BDPT integrator functionality.
This creates a simple scene and renders it with BDPT vs Path integrator to compare.
"""

import os
import sys

# Add the build directory to Python path
build_dir = os.path.join(os.path.dirname(__file__), 'build', 'python')
sys.path.insert(0, build_dir)

try:
    import mitsuba as mi
    import drjit as dr
    
    print("Testing BDPT integrator...")
    
    # Set variant
    mi.set_variant('scalar_rgb')
    print("✓ Variant set to scalar_rgb")
    
    # Create test scene
    scene_dict = mi.cornell_box()
    scene_dict['sensor']['film']['width'] = 64
    scene_dict['sensor']['film']['height'] = 64
    
    # Test with Path integrator first
    scene_dict['integrator'] = {'type': 'path', 'max_depth': 6}
    scene_path = mi.load_dict(scene_dict)
    print("✓ Path integrator scene loaded")
    
    img_path = mi.render(scene_path, spp=32)
    print(f"✓ Path integrator rendered: {img_path.shape}")
    path_mean = dr.mean(img_path.array)
    print(f"  Path mean brightness: {path_mean:.4f}")
    
    # Test with BDPT integrator
    scene_dict['integrator'] = {'type': 'bdpt', 'max_depth': 6}
    scene_bdpt = mi.load_dict(scene_dict)
    print("✓ BDPT integrator scene loaded")
    
    img_bdpt = mi.render(scene_bdpt, spp=32)
    print(f"✓ BDPT integrator rendered: {img_bdpt.shape}")
    bdpt_mean = dr.mean(img_bdpt.array)
    print(f"  BDPT mean brightness: {bdpt_mean:.4f}")
    
    # Compare results
    print(f"\nComparison:")
    print(f"  Path: {path_mean:.4f}")
    print(f"  BDPT: {bdpt_mean:.4f}")
    print(f"  Ratio: {bdpt_mean/path_mean:.3f}")
    
    # Basic sanity checks
    assert path_mean > 0.01, "Path integrator too dark"
    assert bdpt_mean > 0.01, "BDPT integrator too dark"
    assert path_mean < 1.0, "Path integrator oversaturated"
    assert bdpt_mean < 1.0, "BDPT integrator oversaturated"
    
    print("\n✓ All tests passed! BDPT integrator working correctly.")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure mitsuba is built and accessible")
    sys.exit(1)
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)