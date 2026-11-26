// render.cpp - process a WAV file through a native QMaster build.
//
// Loads the VST2 plugin exactly like the MPC host, renders offline, and
// compensates the reported latency so input and output stay aligned.
//
//   render <plugin.so> <in.wav> <out.wav> [--program N] [--set Name=norm]...
//
// --set takes the NORMALISED value (0..1), the same range the host uses.
// Use --program to pick a factory preset; parameters can be overridden after.
//
// SPDX-License-Identifier: MIT

#include "mpc_vst2_abi.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#if defined(_WIN32)
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace
{

struct Wav
{
    int sampleRate = 44100;
    int channels = 2;
    std::vector<float> left, right;
};

std::uint32_t rd32 (const unsigned char* p)
{
    return (std::uint32_t) p[0] | ((std::uint32_t) p[1] << 8)
         | ((std::uint32_t) p[2] << 16) | ((std::uint32_t) p[3] << 24);
}

std::uint16_t rd16 (const unsigned char* p)
{
    return (std::uint16_t) ((std::uint16_t) p[0] | ((std::uint16_t) p[1] << 8));
}

bool readWav (const char* path, Wav& wav, std::string& err)
{
    FILE* f = std::fopen (path, "rb");
    if (!f) { err = "cannot open input"; return false; }
    std::fseek (f, 0, SEEK_END);
    const long size = std::ftell (f);
    std::fseek (f, 0, SEEK_SET);
    std::vector<unsigned char> data ((size_t) std::max (0L, size));
    if (std::fread (data.data(), 1, data.size(), f) != data.size())
    { std::fclose (f); err = "cannot read input"; return false; }
    std::fclose (f);

    if (data.size() < 44 || std::memcmp (data.data(), "RIFF", 4) != 0
        || std::memcmp (data.data() + 8, "WAVE", 4) != 0)
    { err = "not a RIFF/WAVE file"; return false; }

    int format = 0, bits = 0, channels = 0, rate = 0;
    const unsigned char* pcm = nullptr;
    size_t pcmBytes = 0;

    size_t pos = 12;
    while (pos + 8 <= data.size())
    {
        const unsigned char* id = data.data() + pos;
        const std::uint32_t len = rd32 (data.data() + pos + 4);
        const size_t body = pos + 8;
        if (body + len > data.size())
            break;
        if (std::memcmp (id, "fmt ", 4) == 0 && len >= 16)
        {
            format = rd16 (data.data() + body);
            channels = rd16 (data.data() + body + 2);
            rate = (int) rd32 (data.data() + body + 4);
            bits = rd16 (data.data() + body + 14);
        }
        else if (std::memcmp (id, "data", 4) == 0)
        {
            pcm = data.data() + body;
            pcmBytes = len;
        }
        pos = body + len + (len & 1);
    }

    if (! pcm || channels < 1 || rate <= 0 || bits <= 0)
    { err = "missing fmt/data chunk"; return false; }
    if (format != 1 && format != 3)
    { err = "only PCM or float WAV is supported"; return false; }

    const int bytesPerSample = bits / 8;
    if (bytesPerSample <= 0)
    { err = "invalid sample width"; return false; }
    const size_t frames = pcmBytes / (size_t) (bytesPerSample * channels);

    wav.sampleRate = rate;
    wav.channels = channels;
    wav.left.resize (frames);
    wav.right.resize (frames);

    for (size_t i = 0; i < frames; ++i)
    {
        float ch[2] = { 0.0f, 0.0f };
        for (int c = 0; c < std::min (channels, 2); ++c)
        {
            const unsigned char* s = pcm + (i * (size_t) channels + (size_t) c) * (size_t) bytesPerSample;
            float v = 0.0f;
            if (format == 3 && bits == 32)
            {
                std::uint32_t u = rd32 (s);
                float fv;
                std::memcpy (&fv, &u, 4);
                v = fv;
            }
            else if (bits == 16)
            {
                v = (float) (std::int16_t) rd16 (s) / 32768.0f;
            }
            else if (bits == 24)
            {
                std::int32_t u = (std::int32_t) ((std::uint32_t) s[0] << 8
                              | (std::uint32_t) s[1] << 16 | (std::uint32_t) s[2] << 24);
                v = (float) (u >> 8) / 8388608.0f;
            }
            else if (bits == 32)
            {
                v = (float) (std::int32_t) rd32 (s) / 2147483648.0f;
            }
            else
            { err = "unsupported bit depth"; return false; }
            ch[c] = v;
        }
        wav.left[i] = ch[0];
        wav.right[i] = channels > 1 ? ch[1] : ch[0];
    }
    return true;
}

bool writeWav24 (const char* path, const Wav& wav, std::string& err)
{
    FILE* f = std::fopen (path, "wb");
    if (!f) { err = "cannot open output"; return false; }

    const std::uint32_t frames = (std::uint32_t) wav.left.size();
    const std::uint32_t dataBytes = frames * 6;
    auto u32 = [&](std::uint32_t v) { for (int i = 0; i < 4; ++i) std::fputc ((v >> (8 * i)) & 0xff, f); };
    auto u16 = [&](std::uint16_t v) { for (int i = 0; i < 2; ++i) std::fputc ((v >> (8 * i)) & 0xff, f); };

    std::fwrite ("RIFF", 1, 4, f); u32 (36 + dataBytes); std::fwrite ("WAVE", 1, 4, f);
    std::fwrite ("fmt ", 1, 4, f); u32 (16); u16 (1); u16 (2);
    u32 ((std::uint32_t) wav.sampleRate);
    u32 ((std::uint32_t) wav.sampleRate * 6); u16 (6); u16 (24);
    std::fwrite ("data", 1, 4, f); u32 (dataBytes);

    for (std::uint32_t i = 0; i < frames; ++i)
    {
        const float v[2] = { wav.left[i], wav.right[i] };
        for (int c = 0; c < 2; ++c)
        {
            float x = std::isfinite (v[c]) ? v[c] : 0.0f;
            x = std::max (-1.0f, std::min (1.0f, x));
            const std::int32_t s = (std::int32_t) std::lround (x * 8388607.0f);
            const std::uint32_t u = (std::uint32_t) s;
            std::fputc (u & 0xff, f);
            std::fputc ((u >> 8) & 0xff, f);
            std::fputc ((u >> 16) & 0xff, f);
        }
    }
    std::fclose (f);
    return true;
}

// ---------------------------------------------------------------------------
// Minimal VST2 host
// ---------------------------------------------------------------------------
struct Host
{
    double sampleRate = 44100.0;
    int blockSize = 128;
    AEffect* effect = nullptr;
};

Host g;

VstIntPtr hostCallback (AEffect*, VstInt32 opcode, VstInt32, VstIntPtr, void*, float)
{
    switch (opcode)
    {
        case audioMasterVersion: return 2400;
        case audioMasterGetSampleRate: return (VstIntPtr) g.sampleRate;
        case audioMasterGetBlockSize: return g.blockSize;
        case audioMasterGetCurrentProcessLevel: return 0;
        case audioMasterCanDo: return 1;
        case audioMasterIOChanged:
            if (g.effect) g.effect->initialDelay = g.effect->initialDelay;
            return 0;
        default: return 0;
    }
}

VstIntPtr disp (AEffect* e, VstInt32 op, VstInt32 index = 0, VstIntPtr value = 0, void* ptr = nullptr, float opt = 0.0f)
{
    return e->dispatcher (e, op, index, value, ptr, opt);
}

std::string paramName (AEffect* e, int i)
{
    char buf[256] = {};
    disp (e, effGetParamName, i, 0, buf, 0.0f);
    return std::string (buf);
}

int findParam (AEffect* e, const std::string& name)
{
    for (int i = 0; i < e->numParams; ++i)
        if (paramName (e, i) == name)
            return i;
    return -1;
}

} // namespace

int main (int argc, char** argv)
{
    if (argc < 4)
    {
        std::fprintf (stderr, "usage: %s <plugin.so> <in.wav> <out.wav> "
                              "[--program N] [--set Name=norm]...\n", argv[0]);
        return 2;
    }

    Wav input;
    std::string err;
    if (! readWav (argv[2], input, err))
    { std::fprintf (stderr, "render: %s\n", err.c_str()); return 1; }
    if (input.channels < 2)
    { std::fprintf (stderr, "render: stereo input required\n"); return 1; }

    void* handle = nullptr;
#if defined(_WIN32)
    handle = (void*) LoadLibraryA (argv[1]);
#else
    handle = dlopen (argv[1], RTLD_NOW | RTLD_LOCAL);
#endif
    if (! handle)
    { std::fprintf (stderr, "render: cannot load plugin\n"); return 1; }

#if defined(_WIN32)
    auto entry = (AEffect* (*) (audioMasterCallback)) GetProcAddress ((HMODULE) handle, "VSTPluginMain");
#else
    auto entry = (AEffect* (*) (audioMasterCallback)) dlsym (handle, "VSTPluginMain");
#endif
    if (! entry)
    { std::fprintf (stderr, "render: no VSTPluginMain\n"); return 1; }

    AEffect* e = entry (&hostCallback);
    if (! e) { std::fprintf (stderr, "render: plugin refused to load\n"); return 1; }
    g.effect = e;

    g.sampleRate = input.sampleRate;
    g.blockSize = 128;
    disp (e, effSetSampleRate, 0, 0, nullptr, (float) input.sampleRate);
    disp (e, effSetBlockSize, 0, g.blockSize);
    disp (e, effOpen);
    disp (e, effMainsChanged, 0, 1);
    disp (e, effStartProcess);

    for (int i = 4; i < argc; ++i)
    {
        const std::string arg = argv[i];
        if (arg == "--program" && i + 1 < argc)
        {
            disp (e, effSetProgram, 0, std::atoi (argv[++i]));
        }
        else if (arg == "--set" && i + 1 < argc)
        {
            const std::string kv = argv[++i];
            const size_t eq = kv.find ('=');
            if (eq == std::string::npos)
            { std::fprintf (stderr, "render: --set needs Name=value\n"); return 2; }
            const std::string name = kv.substr (0, eq);
            const float value = (float) std::atof (kv.c_str() + eq + 1);
            const int index = findParam (e, name);
            if (index < 0)
            { std::fprintf (stderr, "render: no parameter \"%s\"\n", name.c_str()); return 2; }
            e->setParameter (e, index, std::max (0.0f, std::min (1.0f, value)));
        }
        else
        { std::fprintf (stderr, "render: unknown argument %s\n", arg.c_str()); return 2; }
    }

    const int latency = std::max (0, (int) e->initialDelay);
    const size_t frames = input.left.size();

    std::vector<float> outL (frames + (size_t) latency, 0.0f);
    std::vector<float> outR (frames + (size_t) latency, 0.0f);

    std::vector<float> bufL ((size_t) g.blockSize), bufR ((size_t) g.blockSize);
    std::vector<float> dstL ((size_t) g.blockSize), dstR ((size_t) g.blockSize);
    float* ins[2] = { bufL.data(), bufR.data() };
    float* outs[2] = { dstL.data(), dstR.data() };

    size_t pos = 0;
    while (pos < frames)
    {
        const int n = (int) std::min<size_t> ((size_t) g.blockSize, frames - pos);
        for (int i = 0; i < n; ++i)
        {
            bufL[(size_t) i] = input.left[pos + (size_t) i];
            bufR[(size_t) i] = input.right[pos + (size_t) i];
        }
        for (int i = n; i < g.blockSize; ++i)
            bufL[(size_t) i] = bufR[(size_t) i] = 0.0f;

        e->processReplacing (e, ins, outs, n);

        for (int i = 0; i < n; ++i)
        {
            outL[pos + (size_t) i + (size_t) latency] = outs[0][i];
            outR[pos + (size_t) i + (size_t) latency] = outs[1][i];
        }
        pos += (size_t) n;
    }

    Wav output;
    output.sampleRate = input.sampleRate;
    output.channels = 2;
    output.left = std::move (outL);
    output.right = std::move (outR);

    if (! writeWav24 (argv[3], output, err))
    { std::fprintf (stderr, "render: %s\n", err.c_str()); return 1; }

    std::printf ("render: %zu frames, %d Hz, latency compensated: %d samples\n",
                 frames, input.sampleRate, latency);

    disp (e, effStopProcess);
    disp (e, effMainsChanged, 0, 0);
    disp (e, effClose);
#if ! defined(_WIN32)
    dlclose (handle);
#endif
    return 0;
}
