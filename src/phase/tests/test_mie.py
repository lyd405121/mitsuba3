import pytest
import drjit as dr
import mitsuba as mi

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
    
    # Large particles 
    large = mi.load_dict({
        "type": "mie",
        "radius": 5e-6   # 5 μm
    })
    
    assert small is not None
    assert large is not None

def test_polarized_variant():
    """Test Mie scattering with polarized variant"""
    mi.set_variant('scalar_spectral_polarized')
    
    p = mi.load_dict({
        "type": "mie",
        "radius": 500e-9,
        "ior": 1.33
    })
    
    assert p is not None
    
    # Reset to RGB variant
    mi.set_variant('scalar_rgb')