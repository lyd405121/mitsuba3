#include <mitsuba/core/ray.h>
#include <mitsuba/core/properties.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/emitter.h>
#include <mitsuba/render/integrator.h>
#include <mitsuba/render/records.h>

NAMESPACE_BEGIN(mitsuba)

/**!

.. _integrator-bdpt:

Bidirectional path tracer (:monosp:`bdpt`)
-------------------------------------------

.. pluginparameters::

 * - max_depth
   - |int|
   - Specifies the longest path depth in the generated output image (where -1
     corresponds to :math:`\infty`). A value of 1 will only render directly
     visible light sources. 2 will lead to single-bounce (direct-only)
     illumination, and so on. (Default: -1)

 * - rr_depth
   - |int|
   - Specifies the path depth, at which the implementation will begin to use
     the *russian roulette* path termination criterion. (Default: 5)

 * - hide_emitters
   - |bool|
   - Hide directly visible emitters. (Default: no, i.e. |false|)

This integrator implements bidirectional path tracing (BDPT), which 
connects paths traced from both the sensor and light sources. BDPT can
be particularly effective for scenes with complex lighting conditions
and difficult light transport scenarios.

The algorithm traces paths from both endpoints (camera and lights) and
attempts to connect them at each possible vertex combination. Multiple 
importance sampling (MIS) is used to weight the contributions from
different connection strategies.

.. note:: This integrator does not handle participating media

.. tabs::
    .. code-tab::  xml
        :name: bdpt-integrator

        <integrator type="bdpt">
            <integer name="max_depth" value="8"/>
        </integrator>

    .. code-tab:: python

        'type': 'bdpt',
        'max_depth': 8

 */

template <typename Float, typename Spectrum>
class BDPTIntegrator : public MonteCarloIntegrator<Float, Spectrum> {
public:
    MI_IMPORT_BASE(MonteCarloIntegrator, m_max_depth, m_rr_depth, m_hide_emitters)
    MI_IMPORT_TYPES(Scene, Sampler, Medium, Emitter, EmitterPtr, BSDF, BSDFPtr)

    BDPTIntegrator(const Properties &props) : Base(props) { }

    std::pair<Spectrum, Bool> sample(const Scene *scene,
                                     Sampler *sampler,
                                     const RayDifferential3f &ray_,
                                     const Medium * /* medium */,
                                     Float * /* aovs */,
                                     Bool active) const override {
        MI_MASKED_FUNCTION(ProfilerPhase::SamplingIntegratorSample, active);

        if (unlikely(m_max_depth == 0))
            return { 0.f, false };

        // For now, implement a simplified path tracer as a starting point
        // This will be enhanced with full bidirectional functionality later

        // --------------------- Configure loop state ----------------------

        Ray3f ray                     = Ray3f(ray_);
        Spectrum throughput           = 1.f;
        Spectrum result               = 0.f;
        Float eta                     = 1.f;
        UInt32 depth                  = 0;

        // If m_hide_emitters == false, the environment emitter will be visible
        Mask valid_ray = !m_hide_emitters && (scene->environment() != nullptr);

        // Variables caching information from the previous bounce
        Interaction3f prev_si         = dr::zeros<Interaction3f>();
        Float         prev_bsdf_pdf   = 1.f;
        Bool          prev_bsdf_delta = true;
        BSDFContext   bsdf_ctx;

        /* Set up a Dr.Jit loop for camera path generation */
        struct LoopState {
            Ray3f ray;
            Spectrum throughput;
            Spectrum result;
            Float eta;
            UInt32 depth;
            Mask valid_ray;
            Interaction3f prev_si;
            Float prev_bsdf_pdf;
            Bool prev_bsdf_delta;
            Bool active;
            Sampler* sampler;

            DRJIT_STRUCT(LoopState, ray, throughput, result, eta, depth, 
                valid_ray, prev_si, prev_bsdf_pdf, prev_bsdf_delta,
                active, sampler)
        } ls = {
            ray,
            throughput,
            result,
            eta,
            depth,
            valid_ray,
            prev_si,
            prev_bsdf_pdf,
            prev_bsdf_delta,
            active,
            sampler
        };

        dr::tie(ls) = dr::while_loop(dr::make_tuple(ls),
            [](const LoopState& ls) { return ls.active; },
            [this, scene, bsdf_ctx](LoopState& ls) {

            SurfaceInteraction3f si =
                scene->ray_intersect(ls.ray,
                                     /* ray_flags = */ +RayFlags::All,
                                     /* coherent = */ ls.depth == 0u);

            // ---------------------- Direct emission ----------------------

            if (dr::any_or<true>(si.emitter(scene) != nullptr)) {
                DirectionSample3f ds(scene, si, ls.prev_si);
                Float em_pdf = 0.f;

                if (dr::any_or<true>(!ls.prev_bsdf_delta))
                    em_pdf = scene->pdf_emitter_direction(ls.prev_si, ds,
                                                          !ls.prev_bsdf_delta);

                // Compute MIS weight for emitter sample from previous bounce
                Float mis_bsdf = mis_weight(ls.prev_bsdf_pdf, em_pdf);

                // Accumulate, being careful with polarization
                ls.result = spec_fma(
                    ls.throughput,
                    ds.emitter->eval(si, ls.prev_bsdf_pdf > 0.f) * mis_bsdf,
                    ls.result);
            }

            // Continue tracing the path at this point?
            Bool active_next = (ls.depth + 1 < m_max_depth) && si.is_valid();

            if (dr::none_or<false>(active_next)) {
                ls.active = active_next;
                ls.valid_ray |= (si.emitter(scene) != nullptr) && !m_hide_emitters;
                return;
            }

            BSDFPtr bsdf = si.bsdf(ls.ray);

            // ---------------------- Emitter sampling ----------------------

            // Perform emitter sampling?
            Mask active_em = active_next && has_flag(bsdf->flags(), BSDFFlags::Smooth);

            DirectionSample3f ds = dr::zeros<DirectionSample3f>();
            Spectrum em_weight = dr::zeros<Spectrum>();
            Vector3f wo = dr::zeros<Vector3f>();

            if (dr::any_or<true>(active_em)) {
                // Sample the emitter
                std::tie(ds, em_weight) = scene->sample_emitter_direction(
                    si, ls.sampler->next_2d(), true, active_em);
                active_em &= (ds.pdf != 0.f);

                wo = si.to_local(ds.d);
            }

            // ------ Evaluate BSDF * cos(theta) and sample direction -------

            Float sample_1 = ls.sampler->next_1d();
            Point2f sample_2 = ls.sampler->next_2d();

            auto [bsdf_val, bsdf_pdf, bsdf_sample, bsdf_weight]
                = bsdf->eval_pdf_sample(bsdf_ctx, si, wo, sample_1, sample_2);

            // --------------- Emitter sampling contribution ----------------

            if (dr::any_or<true>(active_em)) {
                bsdf_val = si.to_world_mueller(bsdf_val, -wo, si.wi);

                // Compute the MIS weight
                Float mis_em =
                    dr::select(ds.delta, 1.f, mis_weight(ds.pdf, bsdf_pdf));

                // Accumulate, being careful with polarization
                ls.result[active_em] = spec_fma(
                    ls.throughput, bsdf_val * em_weight * mis_em, ls.result);
            }

            // ---------------------- BSDF sampling ----------------------

            bsdf_weight = si.to_world_mueller(bsdf_weight, -bsdf_sample.wo, si.wi);
            ls.ray = si.spawn_ray(si.to_world(bsdf_sample.wo));

            // ------ Update loop variables based on current interaction ------

            ls.throughput *= bsdf_weight;
            ls.eta *= bsdf_sample.eta;
            ls.valid_ray |= ls.active && si.is_valid() &&
                         !has_flag(bsdf_sample.sampled_type, BSDFFlags::Null);

            // Information about the current vertex needed by the next iteration
            ls.prev_si = si;
            ls.prev_bsdf_pdf = bsdf_sample.pdf;
            ls.prev_bsdf_delta = has_flag(bsdf_sample.sampled_type, BSDFFlags::Delta);

            // -------------------- Stopping criterion ---------------------

            dr::masked(ls.depth, si.is_valid()) += 1;

            Float throughput_max = dr::max(unpolarized_spectrum(ls.throughput));

            Float rr_prob = dr::minimum(throughput_max * dr::square(ls.eta), .95f);
            Mask rr_active = ls.depth >= m_rr_depth,
                 rr_continue = ls.sampler->next_1d() < rr_prob;

            ls.throughput[rr_active] *= dr::rcp(dr::detach(rr_prob));

            ls.active = active_next && rr_continue && dr::any(ls.throughput != 0.f);
        });

        return { ls.result, ls.valid_ray && dr::any(ls.result != 0.f) };
    }

    //! @}
    // =============================================================

    /**
     * \brief Compute the multiple importance sampling weight given the densities
     * of two sampling techniques according to the power heuristic.
     */
    Float mis_weight(Float pdf_a, Float pdf_b) const {
        pdf_a *= pdf_a;
        pdf_b *= pdf_b;
        Float w = pdf_a / (pdf_a + pdf_b);
        return dr::detach<true>(dr::select(dr::isfinite(w), w, 0.f));
    }

    /**
     * \brief Spectral FMADD operations that handles color+polarization combinations
     */
    template <typename Value_>
    Value_ spec_fma(const Value_ &a, const Value_ &b, const Value_ &c) const {
        if constexpr (is_monochromatic_v<Spectrum> && is_polarized_v<Spectrum>)
            return dr::fmadd(a, b, c);
        else if constexpr (is_polarized_v<Spectrum>)
            /* Don't fuse the multiplication for polarized light to ensure
               that it is computed using the polarized form */
            return a * b + c;
        else
            return dr::fmadd(a, b, c);
    }

    MI_DECLARE_CLASS()
};

MI_IMPLEMENT_CLASS_VARIANT(BDPTIntegrator, MonteCarloIntegrator)
MI_EXPORT_PLUGIN(BDPTIntegrator, "Bidirectional Path Tracer integrator");
NAMESPACE_END(mitsuba)