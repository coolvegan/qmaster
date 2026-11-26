// QMaster for Akai MPC standalone (VST2 / AArch64 + ARMv7)
//
// A master and bus processor: trim, tilt, mono maker, 2x oversampled clipper
// and a true-peak limiter in Master mode; trim, transient and clipper in Bus
// mode. Both modes have identical latency.
//
// SPDX-License-Identifier: GPL-3.0-or-later

#include "mpc_plugin.h"
#include "dsp/biquad.h"
#include "dsp/delay_line.h"
#include "dsp/math.h"
#include "dsp/onepole.h"
#include "dsp/smoother.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <initializer_list>
#include <utility>
#include <vector>

using namespace mpc::dsp;
using mpc::choiceParam;
using mpc::floatParam;

namespace
{

// ---------------------------------------------------------------------------
// Latency
// ---------------------------------------------------------------------------
// The halfband up/down pair contributes about 7 samples at the base rate
// (measured with an impulse). The limiter lookahead is 88 base samples.
// Both modes use the same lookahead delay so switching modes never shifts time.
constexpr int kUpDownLatency = 14;
constexpr int kLookahead = 88;
constexpr int kLatency = 102;  // measured with the impulse test

constexpr float kClipKnee = 0.96f;       // -0.35 dBFS
constexpr float kOutputGuard = 0.995f;   // decimation safety
constexpr float kCeilingGuardDb = 0.25f; // detector margin for heavy clipping

// ---------------------------------------------------------------------------
// 2x oversampling (15-tap halfband), separated into up and down stages
// ---------------------------------------------------------------------------
class Oversampler2x
{
public:
    static constexpr int N = 31;
    static constexpr int Ring = 64;

    Oversampler2x() { build(); }

    void reset()
    {
        up.fill (0.0f);
        down.fill (0.0f);
        write = 0;
    }

    void processUp (float x, float& u0, float& u1)
    {
        up[(size_t) write] = x;
        up[(size_t) ((write + 1) & (Ring - 1))] = 0.0f;

        float y0 = 0.0f, y1 = 0.0f;
        for (int k = 0; k < N; ++k)
        {
            const int a = (write - k) & (Ring - 1);
            const int b = (write + 1 - k) & (Ring - 1);
            y0 += h[(size_t) k] * up[(size_t) a];
            y1 += h[(size_t) k] * up[(size_t) b];
        }
        u0 = y0 * 2.0f;
        u1 = y1 * 2.0f;
    }

    float processDown (float v0, float v1)
    {
        down[(size_t) write] = v0;
        down[(size_t) ((write + 1) & (Ring - 1))] = v1;

        float out = 0.0f;
        for (int k = 0; k < N; ++k)
            out += h[(size_t) k] * down[(size_t) ((write + 1 - k) & (Ring - 1))];

        write = (write + 2) & (Ring - 1);
        return out;
    }

private:
    void build()
    {
        const int M = N / 2;
        double sum = 0.0;
        for (int n = 0; n < N; ++n)
        {
            const double x = (double) (n - M);
            const double sinc = std::fabs (x) < 1.0e-9 ? 1.0
                             : std::sin (kPi * 0.5 * x) / (kPi * 0.5 * x);
            const double w = 0.42
                           - 0.5 * std::cos (2.0 * kPi * n / (N - 1))
                           + 0.08 * std::cos (4.0 * kPi * n / (N - 1));
            h[(size_t) n] = (float) (0.5 * sinc * w);
            sum += h[(size_t) n];
        }
        if (sum > 1.0e-9)
            for (float& v : h)
                v = (float) (v / sum);
        reset();
    }

    std::array<float, N> h {};
    std::array<float, Ring> up {}, down {};
    int write = 0;
};

// ---------------------------------------------------------------------------
// Soft clipper
// ---------------------------------------------------------------------------
inline float softClipKnee (float x, float knee)
{
    const float a = std::fabs (x);
    if (a <= knee)
        return x;
    const float y = knee + (1.0f - knee) * fastTanh ((a - knee) / (1.0f - knee));
    return x < 0.0f ? -y : y;
}

// ---------------------------------------------------------------------------
// 4x true-peak detector: interpolates one extra step between the 2x samples.
// The limiter still applies its gain at 2x, but it sees the peak that the
// final 1x signal would produce between samples.
// ---------------------------------------------------------------------------
class TruePeak4x
{
public:
    static constexpr int N = 31;
    static constexpr int Ring = 64;

    TruePeak4x() { build(); }

    void reset()
    {
        up.fill (0.0f);
        write = 0;
    }

    float peak (float x)
    {
        up[(size_t) write] = x;
        up[(size_t) ((write + 1) & (Ring - 1))] = 0.0f;

        float y0 = 0.0f, y1 = 0.0f;
        for (int k = 0; k < N; ++k)
        {
            const int a = (write - k) & (Ring - 1);
            const int b = (write + 1 - k) & (Ring - 1);
            y0 += h[(size_t) k] * up[(size_t) a];
            y1 += h[(size_t) k] * up[(size_t) b];
        }
        write = (write + 2) & (Ring - 1);
        return 2.0f * std::max (std::fabs (y0), std::fabs (y1));
    }

private:
    void build()
    {
        const int M = N / 2;
        double sum = 0.0;
        for (int n = 0; n < N; ++n)
        {
            const double x = (double) (n - M);
            const double sinc = std::fabs (x) < 1.0e-9 ? 1.0
                             : std::sin (kPi * 0.5 * x) / (kPi * 0.5 * x);
            const double w = 0.42
                           - 0.5 * std::cos (2.0 * kPi * n / (N - 1))
                           + 0.08 * std::cos (4.0 * kPi * n / (N - 1));
            h[(size_t) n] = (float) (0.5 * sinc * w);
            sum += h[(size_t) n];
        }
        if (sum > 1.0e-9)
            for (float& v : h)
                v = (float) (v / sum);
        reset();
    }

    std::array<float, N> h {};
    std::array<float, Ring> up {};
    int write = 0;
};

// ---------------------------------------------------------------------------
// Lookahead limiter, operating at 2x. Stereo linked.
// ---------------------------------------------------------------------------
class StereoLimiter
{
public:
    void prepare (double sampleRate)
    {
        delayL.prepare (kLookahead + 2);
        delayR.prepare (kLookahead + 2);
        attack = onePoleCoeff (0.3f, sampleRate);
        setRelease (300.0f, sampleRate);
        reset();
    }

    void setRelease (float ms, double sampleRate)
    {
        release = onePoleCoeff (std::max (5.0f, ms), sampleRate);
    }

    void reset()
    {
        delayL.reset();
        delayR.reset();
        window.fill (0.0f);
        wpos = 0;
        gain = 1.0f;
    }

    void process (float& l, float& r, float ceiling, float peak)
    {
        // Sliding maximum over the lookahead window: the gain must already be
        // down when the delayed peak reaches the output.
        window[(size_t) wpos] = peak;
        wpos = (wpos + 1) & (WindowSize - 1);

        float mx = 0.0f;
        for (int k = 0; k <= kLookahead; ++k)
        {
            const float v = window[(size_t) ((wpos - 1 - k) & (WindowSize - 1))];
            if (v > mx)
                mx = v;
        }

        float target = 1.0f;
        if (mx > ceiling && mx > 1.0e-9f)
            target = ceiling / mx;

        const float coeff = target < gain ? attack : release;
        gain += coeff * (target - gain);

        delayL.write (l);
        delayR.write (r);
        l = delayL.readInt (kLookahead) * gain;
        r = delayR.readInt (kLookahead) * gain;
    }

private:
    static constexpr int WindowSize = 128;
    DelayLine delayL, delayR;
    std::array<float, WindowSize> window {};
    int wpos = 0;
    float gain = 1.0f;
    float attack = 1.0f, release = 0.001f;
};

// Bus mode: the same delay, no gain change, so latency matches Master.
class StereoPad
{
public:
    void prepare()
    {
        delayL.prepare (kLookahead + 2);
        delayR.prepare (kLookahead + 2);
        reset();
    }

    void reset()
    {
        delayL.reset();
        delayR.reset();
    }

    void process (float& l, float& r)
    {
        delayL.write (l);
        delayR.write (r);
        l = delayL.readInt (kLookahead);
        r = delayR.readInt (kLookahead);
    }

private:
    DelayLine delayL, delayR;
};

// ---------------------------------------------------------------------------
// Mono maker: high-pass the side signal below the chosen frequency.
// ---------------------------------------------------------------------------
class MonoMaker
{
public:
    void prepare (double sampleRate)
    {
        sr = sampleRate;
        setFrequency (120.0f);
        reset();
    }

    void setFrequency (float hz)
    {
        freq = std::max (0.0f, hz);
        if (freq <= 0.0f)
            return;
        const auto c = BiquadCoeffs::highpass (sr, freq, 0.7071f);
        hp1.setCoeffs (c);
        hp2.setCoeffs (c);
    }

    void reset()
    {
        hp1.reset();
        hp2.reset();
    }

    void process (float& l, float& r)
    {
        if (freq <= 0.0f)
            return;
        const float mid = 0.5f * (l + r);
        float side = 0.5f * (l - r);
        side = hp2.process (hp1.process (side));
        l = mid + side;
        r = mid - side;
    }

private:
    double sr = 44100.0;
    float freq = 120.0f;
    Biquad hp1, hp2;
};

// ---------------------------------------------------------------------------
// Tilt: low shelf down, high shelf up (each half the requested spread).
// ---------------------------------------------------------------------------
class Tilt
{
public:
    void prepare (double sampleRate) { sr = sampleRate; reset(); }

    void set (float db)
    {
        const float g = db * 0.5f;
        const auto low = BiquadCoeffs::lowShelf (sr, 200.0f, 0.7071f, -g);
        const auto high = BiquadCoeffs::highShelf (sr, 3000.0f, 0.7071f, g);
        loL.setCoeffs (low); loR.setCoeffs (low);
        hiL.setCoeffs (high); hiR.setCoeffs (high);
    }

    void reset()
    {
        loL.reset(); loR.reset(); hiL.reset(); hiR.reset();
    }

    void process (float& l, float& r)
    {
        l = hiL.process (loL.process (l));
        r = hiR.process (loR.process (r));
    }

private:
    double sr = 44100.0;
    Biquad loL, loR, hiL, hiR;
};

// ---------------------------------------------------------------------------
// Bus transient shaper: fast vs slow envelope, linked stereo.
// ---------------------------------------------------------------------------
class Transient
{
public:
    void prepare (double sampleRate)
    {
        fast.setCutoff (1000.0f, sampleRate);
        slow.setCutoff (16.0f, sampleRate);
        reset();
    }

    void reset()
    {
        fast.reset();
        slow.reset();
    }

    void process (float& l, float& r, float amount)
    {
        if (amount <= 0.0001f)
            return;
        const float peak = std::max (std::fabs (l), std::fabs (r));
        const float f = fast.process (peak);
        const float s = slow.process (peak);
        const float diff = std::max (0.0f, f - s);
        const float g = 1.0f + amount * 2.0f * clamp (diff / (f + 1.0e-6f), 0.0f, 1.0f);
        l *= g;
        r *= g;
    }

private:
    OnePoleLP fast, slow;
};

} // namespace

// ===========================================================================
// The plugin
// ===========================================================================
class QMasterMpc : public mpc::Plugin
{
public:
    enum P
    {
        pMode, pTrim, pTilt, pClip, pTransient, pCeiling, pRelease, pMono,
        kNumParams
    };

    static mpc::PluginInfo makeInfo()
    {
        mpc::PluginInfo i;
        i.name = "QMaster";
        i.vendor = "r3d0xStyle";
        i.uniqueId = MPC_FOURCC ('q', 'm', 's', 't');
        i.version = 1000;
        i.isInstrument = false;
        i.numInputs = 2;
        i.numOutputs = 2;
        i.wantsMidi = false;
        i.latencySamples = kLatency;
        return i;
    }

    QMasterMpc() : mpc::Plugin (makeInfo())
    {
        mpc::Param mode = choiceParam ("mode", "Mode", { "Master", "Bus" }, 0);
        mode.automatable = false;   // switching mid-song must be deliberate
        addParam (mode);
        addParam (floatParam ("trim", "Trim", -12.0f, 12.0f, 0.0f, "dB", 1));
        addParam (floatParam ("tilt", "Tilt", -6.0f, 6.0f, 0.0f, "dB", 1));
        addParam (floatParam ("clip", "Clip", 0.0f, 100.0f, 30.0f, "%", 0));
        addParam (floatParam ("transient", "Transient", 0.0f, 100.0f, 0.0f, "%", 0));
        addParam (floatParam ("ceiling", "Ceiling", -2.0f, 0.0f, -1.0f, "dBTP", 1));
        addParam (floatParam ("release", "Release", 0.0f, 100.0f, 50.0f, "%", 0));
        addParam (floatParam ("mono", "Mono", 0.0f, 200.0f, 120.0f, "Hz", 0));

        addPrograms();
    }

    void prepare (double sampleRate, int maxBlockSize) override
    {
        (void) maxBlockSize;
        srate = (float) std::max (8000.0, sampleRate);

        trimSmooth.setTime (20.0f, sampleRate);
        driveSmooth.setTime (20.0f, sampleRate);
        ceilingSmooth.setTime (20.0f, sampleRate);

        const auto hp = BiquadCoeffs::highpass (sampleRate, 24.0f, 0.7071f);
        hp1L.setCoeffs (hp); hp1R.setCoeffs (hp);
        hp2L.setCoeffs (hp); hp2R.setCoeffs (hp);

        tilt.prepare (sampleRate);
        mono.prepare (sampleRate);
        transient.prepare (sampleRate);
        limiter.prepare (sampleRate);
        pad.prepare();
        osL.reset();
        osR.reset();
        lastMode = -1;
        reset();
    }

    void reset() override
    {
        hp1L.reset(); hp1R.reset(); hp2L.reset(); hp2R.reset();
        tilt.reset();
        mono.reset();
        transient.reset();
        limiter.reset();
        pad.reset();
        detL.reset();
        detR.reset();
        osL.reset();
        osR.reset();

        trimSmooth.snap (dbToGain (get (pTrim)));
        driveSmooth.snap (dbToGain (clipToDb (get (pClip))));
        ceilingSmooth.snap (dbToGain (get (pCeiling)));
        lastMode = getInt (pMode);
    }

    void parameterChanged (int index, float plainValue) override
    {
        (void) plainValue;
        if (index == pMode)
        {
            // Deliberate mode switch: clear the state so no stale filter or
            // limiter gain leaks into the other topology.
            hp1L.reset(); hp1R.reset(); hp2L.reset(); hp2R.reset();
            tilt.reset();
            mono.reset();
            transient.reset();
            limiter.reset();
            pad.reset();
            detL.reset();
            detR.reset();
            osL.reset();
            osR.reset();
            lastMode = getInt (pMode);
        }
    }

    void process (mpc::ProcessContext& ctx) override
    {
        int n = ctx.numFrames;
        if (n <= 0)
            return;

        const float* inL = ctx.numInputs > 0 ? ctx.inputs[0] : nullptr;
        const float* inR = ctx.numInputs > 1 ? ctx.inputs[1] : inL;
        float* outL = ctx.numOutputs > 0 ? ctx.outputs[0] : nullptr;
        float* outR = ctx.numOutputs > 1 ? ctx.outputs[1] : outL;
        if (! outL)
            return;

        const int mode = getInt (pMode);

        if (mode != lastMode)
            parameterChanged (pMode, (float) mode);

        const float trimTarget = dbToGain (get (pTrim));
        const float driveTarget = dbToGain (clipToDb (get (pClip)));
        const float ceilingTarget = dbToGain (get (pCeiling) - kCeilingGuardDb);
        const float releaseMs = 30.0f * std::pow (800.0f / 30.0f, clamp (get (pRelease) * 0.01f, 0.0f, 1.0f));
        const float monoHz = get (pMono);
        const float tiltDb = get (pTilt);
        const float transientAmount = clamp (get (pTransient) * 0.01f, 0.0f, 1.0f);

        trimSmooth.setTarget (trimTarget);
        driveSmooth.setTarget (driveTarget);
        ceilingSmooth.setTarget (ceilingTarget);
        limiter.setRelease (releaseMs, (double) srate);
        tilt.set (tiltDb);
        mono.setFrequency (monoHz);

        const bool master = mode == 0;

        for (int i = 0; i < n; ++i)
        {
            float l = inL ? inL[i] : 0.0f;
            float r = inR ? inR[i] : l;

            const float g = trimSmooth.process();
            l *= g;
            r *= g;

            if (master)
            {
                l = hp2L.process (hp1L.process (l));
                r = hp2R.process (hp1R.process (r));
                tilt.process (l, r);
                mono.process (l, r);
            }
            else
            {
                transient.process (l, r, transientAmount);
            }

            const float drive = driveSmooth.process();

            float u0l, u1l, u0r, u1r;
            osL.processUp (l, u0l, u1l);
            osR.processUp (r, u0r, u1r);

            u0l = softClipKnee (u0l * drive, kClipKnee);
            u1l = softClipKnee (u1l * drive, kClipKnee);
            u0r = softClipKnee (u0r * drive, kClipKnee);
            u1r = softClipKnee (u1r * drive, kClipKnee);

            float yl = osL.processDown (u0l, u1l);
            float yr = osR.processDown (u0r, u1r);

            const float ceiling = ceilingSmooth.process();
            if (master)
            {
                const float peak = std::max (std::max (std::fabs (yl), std::fabs (yr)),
                                             std::max (detL.peak (yl), detR.peak (yr)));
                limiter.process (yl, yr, ceiling, peak);
            }
            else
                pad.process (yl, yr);

            outL[i] = softClipKnee (sanitize (flushDenormal (yl)), kOutputGuard);
            if (outR && outR != outL)
                outR[i] = softClipKnee (sanitize (flushDenormal (yr)), kOutputGuard);
        }
    }

private:
    static float clipToDb (float percent)
    {
        return clamp (percent, 0.0f, 100.0f) * 0.12f;   // 0..12 dB drive
    }

    std::vector<float> defaultValues() const
    {
        std::vector<float> v ((size_t) kNumParams);
        for (int i = 0; i < kNumParams; ++i)
            v[(size_t) i] = param (i).def;
        return v;
    }

    void program (const char* name, std::initializer_list<std::pair<int, float>> overrides)
    {
        auto v = defaultValues();
        for (const auto& o : overrides)
            v[(size_t) o.first] = o.second;
        addProgram (name, std::move (v));
    }

    void addPrograms()
    {
        program ("Init", {});
        program ("CD Loud", {
            { pClip, 45.0f }, { pCeiling, -1.0f }, { pRelease, 45.0f }, { pMono, 110.0f },
        });
        program ("Streaming Safe", {
            { pClip, 25.0f }, { pCeiling, -1.5f }, { pRelease, 65.0f },
        });
        program ("Bus Drums", {
            { pMode, 1.0f }, { pClip, 55.0f }, { pTransient, 60.0f }, { pMono, 0.0f },
        });
        program ("Bus 808", {
            { pMode, 1.0f }, { pClip, 70.0f }, { pTransient, 20.0f }, { pMono, 0.0f },
        });
    }

    float srate = 44100.0f;
    int lastMode = -1;

    Biquad hp1L, hp1R, hp2L, hp2R;
    Tilt tilt;
    MonoMaker mono;
    Transient transient;

    Oversampler2x osL, osR;
    TruePeak4x detL, detR;
    StereoLimiter limiter;
    StereoPad pad;

    Smoother trimSmooth, driveSmooth, ceilingSmooth;
};

MPC_PLUGIN_ENTRY (QMasterMpc)
