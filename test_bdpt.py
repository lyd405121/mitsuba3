import pytest
import drjit as dr
import mitsuba as mi

def test_bdpt_integrator_basic():
    """Basic test to ensure BDPT integrator loads and can render a simple scene"""
    mi.set_variant('scalar_rgb')
    
    # Create a simple scene with BDPT integrator
    scene_description = mi.cornell_box()
    scene_description['integrator'] = {
        'type': 'bdpt',
        'max_depth': 8
    }
    
    # Load the scene 
    scene = mi.load_dict(scene_description)
    
    # Check that the integrator is properly loaded
    assert scene.integrator() is not None
    assert 'bdpt' in str(scene.integrator()).lower()

def test_bdpt_integrator_render():
    """Test that BDPT integrator can render an image"""
    mi.set_variant('scalar_rgb')
    
    # Create a scene with minimal resolution for fast testing
    scene_description = mi.cornell_box()
    scene_description['integrator'] = {
        'type': 'bdpt',
        'max_depth': 4
    }
    scene_description['sensor']['film']['width'] = 32
    scene_description['sensor']['film']['height'] = 32
    
    scene = mi.load_dict(scene_description)
    
    # Render the scene - should not crash
    img = mi.render(scene, spp=16)
    
    # Basic checks on the rendered image
    assert img is not None
    assert img.shape == (32, 32, 3)
    
    # Check that we got some non-zero values (scene is not completely black)
    assert dr.any(dr.neq(img.array, 0.0))

if __name__ == "__main__":
    test_bdpt_integrator_basic()
    test_bdpt_integrator_render()
    print("All BDPT tests passed!")