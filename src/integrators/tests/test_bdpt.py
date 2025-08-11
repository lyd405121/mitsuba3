import pytest
import drjit as dr
import mitsuba as mi

def test_bdpt_integrator_registration():
    """Test that BDPT integrator is properly registered"""
    mi.set_variant('scalar_rgb')
    
    # Test that we can create the integrator
    integrator = mi.load_dict({'type': 'bdpt', 'max_depth': 8})
    assert integrator is not None

def test_bdpt_vs_path_integrator():
    """Compare BDPT output with path integrator on a simple scene"""
    mi.set_variant('scalar_rgb')
    
    # Create a simple scene
    scene_description = mi.cornell_box()
    scene_description['sensor']['film']['width'] = 32
    scene_description['sensor']['film']['height'] = 32
    
    # Test with path integrator
    scene_description['integrator'] = {'type': 'path', 'max_depth': 4}
    scene_path = mi.load_dict(scene_description)
    img_path = mi.render(scene_path, spp=16)
    
    # Test with BDPT integrator
    scene_description['integrator'] = {'type': 'bdpt', 'max_depth': 4}
    scene_bdpt = mi.load_dict(scene_description)
    img_bdpt = mi.render(scene_bdpt, spp=16)
    
    # Both should produce some light
    assert dr.any(dr.neq(img_path.array, 0.0))
    assert dr.any(dr.neq(img_bdpt.array, 0.0))
    
    # The images should be somewhat similar (basic sanity check)
    # We just check they're both reasonable and non-zero
    path_mean = dr.mean(img_path.array)
    bdpt_mean = dr.mean(img_bdpt.array)
    
    # Basic checks that both are in reasonable range
    assert path_mean > 0.01  # Not too dark
    assert bdpt_mean > 0.01  # Not too dark
    assert path_mean < 1.0   # Not oversaturated
    assert bdpt_mean < 1.0   # Not oversaturated