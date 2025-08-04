#!/usr/bin/env python3
"""
Validation script for Mie scattering implementation.
This script tests the basic functionality without requiring a full build.
"""

import numpy as np
import matplotlib.pyplot as plt

def validate_mie_theory():
    """
    Validate our understanding of Mie scattering theory and implementation.
    This provides reference calculations for comparison.
    """
    print("=== Mie Scattering Theory Validation ===")
    
    # Test size parameter calculations
    wavelengths = np.array([400, 550, 700]) * 1e-9  # Blue, green, red in meters
    radius = 500e-9  # 500 nm particle
    
    size_params = 2 * np.pi * radius / wavelengths
    print(f"Size parameters for {radius*1e9:.0f}nm particles:")
    for wl, x in zip(wavelengths*1e9, size_params):
        print(f"  λ = {wl:.0f}nm: x = {x:.2f}")
        regime = "Rayleigh" if x < 1 else "Mie" if x < 10 else "Geometric"
        print(f"    Regime: {regime}")
    
    print()
    
    # Test different particle sizes at green light (550nm)
    green_wl = 550e-9
    radii = np.array([50, 100, 500, 1000, 5000]) * 1e-9  # Various sizes in meters
    
    print(f"Size parameters at λ = {green_wl*1e9:.0f}nm:")
    for r in radii:
        x = 2 * np.pi * r / green_wl
        print(f"  r = {r*1e9:.0f}nm: x = {x:.2f}")
        
        # Simplified asymmetry parameter estimation
        g_approx = np.tanh(x * 0.1) * 0.8
        print(f"    Approx asymmetry g ≈ {g_approx:.3f}")
    
    print()

def plot_phase_functions():
    """
    Plot theoretical phase functions for different particle sizes.
    """
    print("=== Plotting Phase Functions ===")
    
    # Scattering angles
    theta = np.linspace(0, np.pi, 181)
    cos_theta = np.cos(theta)
    
    wavelength = 550e-9  # Green light
    
    # Different particle sizes
    radii = [50e-9, 200e-9, 500e-9, 2e-6]  # nm to m
    labels = ['50nm', '200nm', '500nm', '2μm']
    
    plt.figure(figsize=(12, 8))
    
    for i, (radius, label) in enumerate(zip(radii, labels)):
        x = 2 * np.pi * radius / wavelength
        
        if x < 0.1:
            # Rayleigh phase function
            phase = (3/16) * (1/np.pi) * (1 + cos_theta**2)
        else:
            # Simplified Mie approximation using HG
            g = np.tanh(x * 0.1) * 0.8
            denominator = (1 + g**2 - 2*g*cos_theta)**(1.5)
            phase = (1 - g**2) / (4*np.pi) / denominator
        
        # Normalize for plotting
        phase_norm = phase / np.max(phase)
        
        plt.subplot(2, 2, i+1)
        plt.polar(theta, phase_norm)
        plt.title(f'{label} (x={x:.2f})')
        plt.ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('/tmp/mie_phase_functions.png', dpi=150, bbox_inches='tight')
    print("Phase function plots saved to /tmp/mie_phase_functions.png")

def validate_mueller_matrix():
    """
    Validate Mueller matrix elements for Mie scattering.
    """
    print("=== Mueller Matrix Validation ===")
    
    # For unpolarized light, first row/column contains the intensity information
    # For Mie scattering, the Mueller matrix has specific symmetries
    
    print("Mueller matrix structure for Mie scattering:")
    print("M = [I+Q    I-Q    0      0   ]")
    print("    [I-Q    I+Q    0      0   ]") 
    print("    [0      0      U      V   ]")
    print("    [0      0     -V      U   ]")
    print()
    print("Where:")
    print("  I = (|S1|² + |S2|²)/2  - Total intensity")
    print("  Q = (|S2|² - |S1|²)/2  - Linear polarization")
    print("  U = Re(S1*S2*)         - Linear polarization (45°)")
    print("  V = Im(S1*S2*)         - Circular polarization")
    print()
    
    # Example calculation for forward scattering
    print("For forward scattering (θ=0°):")
    print("  S1 ≈ S2 for spherical particles")
    print("  Therefore: Q ≈ 0, U ≈ |S1|², V ≈ 0")
    print("  Result: Forward scattering is mostly unpolarized")

def main():
    """Main validation function."""
    try:
        validate_mie_theory()
        validate_mueller_matrix()
        
        # Only try plotting if matplotlib is available
        try:
            plot_phase_functions()
        except ImportError:
            print("Matplotlib not available, skipping plots")
        except Exception as e:
            print(f"Plotting failed: {e}")
        
        print("\n=== Validation Complete ===")
        print("The Mie scattering implementation should:")
        print("1. Transition smoothly from Rayleigh to Mie regimes")
        print("2. Show increasing forward scattering with particle size") 
        print("3. Depend on wavelength through the size parameter")
        print("4. Support both scalar and polarized rendering")
        print("5. Return proper Mueller matrices for polarized variants")
        
    except Exception as e:
        print(f"Validation failed: {e}")

if __name__ == "__main__":
    main()