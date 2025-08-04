#include <mitsuba/core/properties.h>
#include <mitsuba/core/warp.h>
#include <mitsuba/render/phase.h>

NAMESPACE_BEGIN(mitsuba)

template <typename Float, typename Spectrum>
class MiePhaseFunction final : public PhaseFunction<Float, Spectrum> {
public:
    MI_IMPORT_BASE(PhaseFunction, m_flags)
    MI_IMPORT_TYPES(PhaseFunctionContext)

    MiePhaseFunction(const Properties &props) : Base(props) {
        m_radius = props.get<ScalarFloat>("radius", 500e-9f);
        m_ior = props.get<ScalarFloat>("ior", 1.33f);
        
        if (m_radius <= 0.f)
            Throw("Particle radius must be positive!");
        if (m_ior <= 0.f)
            Throw("Refractive index must be positive!");

        m_flags = +PhaseFunctionFlags::Anisotropic;
    }

    void traverse(TraversalCallback *callback) override {
        callback->put_parameter("radius", m_radius, ParamFlags::Differentiable);
        callback->put_parameter("ior", m_ior, ParamFlags::Differentiable);
    }

    // Simplified Rayleigh-like behavior for now
    MI_INLINE Float eval_mie_phase(Float cos_theta) const {
        return (3.f / 16.f) * dr::InvPi<Float> * (1.f + dr::square(cos_theta));
    }

    std::tuple<Vector3f, Spectrum, Float> sample(const PhaseFunctionContext & /* ctx */,
                                                 const MediumInteraction3f &mi,
                                                 Float /* sample1 */,
                                                 const Point2f &sample,
                                                 Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::PhaseFunctionSample, active);

        Float z   = 2.f * (2.f * sample.x() - 1.f);
        Float tmp = dr::sqrt(dr::square(z) + 1.f);
        Float A   = dr::cbrt(z + tmp);
        Float B   = dr::cbrt(z - tmp);
        Float cos_theta = A + B;
        Float sin_theta = dr::safe_sqrt(1.0f - dr::square(cos_theta));
        auto [sin_phi, cos_phi] = dr::sincos(dr::TwoPi<Float> * sample.y());

        auto wo = Vector3f{ sin_theta * cos_phi, sin_theta * sin_phi, cos_theta };

        wo = mi.to_world(wo);
        Float pdf = eval_mie_phase(-cos_theta);
        return { wo, 1.f, pdf };
    }

    std::pair<Spectrum, Float> eval_pdf(const PhaseFunctionContext & /* ctx */,
                                        const MediumInteraction3f & mi,
                                        const Vector3f &wo,
                                        Mask active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::PhaseFunctionEvaluate, active);
        Float cos_theta = dr::dot(wo, mi.wi);
        Float pdf = eval_mie_phase(cos_theta);
        return { pdf, pdf };
    }

    std::string to_string() const override { 
        return "MiePhaseFunction[]";
    }

    MI_DECLARE_CLASS()
private:
    ScalarFloat m_radius;
    ScalarFloat m_ior;
};

MI_IMPLEMENT_CLASS_VARIANT(MiePhaseFunction, PhaseFunction)
MI_EXPORT_PLUGIN(MiePhaseFunction, "Mie scattering phase function")
NAMESPACE_END(mitsuba)