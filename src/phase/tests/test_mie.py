import pytest
import drjit as dr
import mitsuba as mi
import numpy as np

def test_create(variant_scalar_rgb):
    p = mi.load_dict({"type": "mie"})
    assert p is not None

def test_create_with_params(variant_scalar_rgb):
    p = mi.load_dict({
        "type": "mie",
        "radius": 1e-6,
        "ior": 1.4
    })
    assert p is not None

def test_invalid_parameters(variant_scalar_rgb):
    """Test that invalid parameters raise appropriate errors"""
    
    # Negative radius should fail
    with pytest.raises(RuntimeError):
        mi.load_dict({
            "type": "mie",
            "radius": -1e-6
        })
    
    # Zero or negative IOR should fail
    with pytest.raises(RuntimeError):
        mi.load_dict({
            "type": "mie",
            "ior": 0.0
        })

def test_chi2(variants_vec_backends_once_rgb):
    sample_func, pdf_func = mi.chi2.PhaseFunctionAdapter("mie", "")

    chi2 = mi.chi2.ChiSquareTest(
        domain=mi.chi2.SphericalDomain(),
        sample_func=sample_func,
        pdf_func=pdf_func,
        sample_dim=3,
    )

    assert chi2.run()

def test_different_sizes(variant_scalar_rgb):
    """Test Mie scattering with different particle sizes"""
    
    # Small particles (Rayleigh regime)
    small = mi.load_dict({
        "type": "mie", 
        "radius": 50e-9  # 50 nm
    })
    
    # Medium particles (transition regime)
    medium = mi.load_dict({
        "type": "mie",
        "radius": 500e-9  # 500 nm
    })
    
    # Large particles (Mie regime)
    large = mi.load_dict({
        "type": "mie",
        "radius": 5e-6   # 5 μm
    })
    
    assert small is not None
    assert medium is not None
    assert large is not None

def test_phase_function_normalization(variant_scalar_rgb):
    """Test that the phase function is properly normalized"""
    mi.set_variant('scalar_rgb')
    
    # Create a Mie phase function
    phase = mi.load_dict({
        "type": "mie",
        "radius": 500e-9,
        "ior": 1.33
    })
    
    # Create a medium interaction for testing
    ctx = mi.PhaseFunctionContext()
    
    # Test that the phase function integrates to 4π (for a phase function)
    # This is a simplified test - a full test would integrate over the sphere
    # Here we just test that sampling and evaluation work
    
    # Create a dummy medium interaction
    mi_test = dr.zeros(mi.MediumInteraction3f)
    mi_test.wi = mi.Vector3f(0, 0, 1)  # Incident direction
    mi_test.wavelengths = mi.Color3f(550.0)  # Green light wavelength
    
    # Test sampling
    sample = mi.Point2f(0.5, 0.5)
    wo, weight, pdf = phase.sample(ctx, mi_test, 0.5, sample)
    
    assert dr.all(dr.isfinite(wo))
    assert dr.all(dr.isfinite(weight))
    assert dr.all(dr.isfinite(pdf))
    assert pdf > 0

def test_size_parameter_effects(variant_scalar_rgb):
    """Test that size parameter affects scattering behavior"""
    mi.set_variant('scalar_rgb')
    
    # Small particles should behave more like Rayleigh scattering
    small_phase = mi.load_dict({
        "type": "mie",
        "radius": 50e-9,   # Small particles
        "ior": 1.33
    })
    
    # Large particles should show more forward scattering
    large_phase = mi.load_dict({
        "type": "mie", 
        "radius": 2e-6,    # Large particles
        "ior": 1.33
    })
    
    # Create medium interactions for forward and backward scattering
    ctx = mi.PhaseFunctionContext()
    mi_test = dr.zeros(mi.MediumInteraction3f)
    mi_test.wi = mi.Vector3f(0, 0, 1)
    mi_test.wavelengths = mi.Color3f(550.0)
    
    # Test forward scattering (cos_theta = 1)
    wo_forward = mi.Vector3f(0, 0, -1)  # Same direction as incident
    small_forward = small_phase.eval_pdf(ctx, mi_test, wo_forward)[1]
    large_forward = large_phase.eval_pdf(ctx, mi_test, wo_forward)[1]
    
    # Test backward scattering (cos_theta = -1)  
    wo_backward = mi.Vector3f(0, 0, 1)  # Opposite direction
    small_backward = small_phase.eval_pdf(ctx, mi_test, wo_backward)[1]
    large_backward = large_phase.eval_pdf(ctx, mi_test, wo_backward)[1]
    
    # Large particles should show more forward scattering relative to backward scattering
    small_ratio = small_forward / small_backward
    large_ratio = large_forward / large_backward
    
    # This is a heuristic test - large particles should be more forward-scattering
    assert large_ratio >= small_ratio

def test_polarized_variant():
    """Test Mie scattering with polarized variant"""
    mi.set_variant('scalar_spectral_polarized')
    
    p = mi.load_dict({
        "type": "mie",
        "radius": 500e-9,
        "ior": 1.33
    })
    
    assert p is not None
    
    # Test that Mueller matrix is returned for polarized variants
    ctx = mi.PhaseFunctionContext()
    mi_test = dr.zeros(mi.MediumInteraction3f)
    mi_test.wi = mi.Vector3f(0, 0, 1)
    mi_test.wavelengths = mi.Color4f(550.0, 550.0, 550.0, 550.0)
    
    wo = mi.Vector3f(0, 0, -1)
    mueller, pdf = p.eval_pdf(ctx, mi_test, wo)
    
    # Mueller matrix should be 4x4
    assert mueller.shape == (4, 4)
    assert dr.all(dr.isfinite(mueller))
    assert pdf > 0
    
    # Reset to RGB variant
    mi.set_variant('scalar_rgb')

def test_wavelength_dependence(variant_scalar_rgb):
    """Test that scattering depends on wavelength through size parameter"""
    mi.set_variant('scalar_spectral')
    
    phase = mi.load_dict({
        "type": "mie",
        "radius": 300e-9,  # 300 nm particles
        "ior": 1.33
    })
    
    ctx = mi.PhaseFunctionContext()
    mi_test = dr.zeros(mi.MediumInteraction3f)
    mi_test.wi = mi.Vector3f(0, 0, 1)
    
    # Test different wavelengths
    mi_test.wavelengths = mi.Color4f(400.0, 400.0, 400.0, 400.0)  # Blue light
    wo = mi.Vector3f(0, 0, -1)  # Forward scattering
    blue_result = phase.eval_pdf(ctx, mi_test, wo)[1]
    
    mi_test.wavelengths = mi.Color4f(700.0, 700.0, 700.0, 700.0)  # Red light  
    red_result = phase.eval_pdf(ctx, mi_test, wo)[1]
    
    # For particles around 300nm, blue light (smaller wavelength) should scatter differently than red
    # This tests that the size parameter x = 2π*r/λ is being used correctly
    assert blue_result != red_result
    
    # Reset to RGB variant
    mi.set_variant('scalar_rgb')