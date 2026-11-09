#if __RESHADE__ < 50900
#error FlexAgX requires ReShade 5.9.0 or newer (storage images with tex2Dfetch reads).
#endif

#if __RENDERER__ < 0xb000 || (__RENDERER__ >= 0x10000 && __RENDERER__ < 0x14300)
#error FlexAgX requires D3D11, D3D12, OpenGL 4.3 or Vulkan.
#endif

texture2D FA_BackBuffer : COLOR;

#ifndef BUFFER_COLOR_SPACE
#define BUFFER_COLOR_SPACE 1
#endif

#if BUFFER_COLOR_SPACE == 2 || BUFFER_COLOR_SPACE == 3 || BUFFER_COLOR_SPACE == 4
    #define FA_HDR_BYPASS 1
#endif

sampler2D FA_BackBufferSampler
{
    Texture = FA_BackBuffer;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
    SRGBTexture = false;
};

void FA_FullscreenVS(uint id : SV_VertexID, out float4 position : SV_Position, out float2 texcoord : TEXCOORD0)
{
    texcoord.x = (id == 2) ? 2.0 : 0.0;
    texcoord.y = (id == 1) ? 2.0 : 0.0;
    position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
}

#ifdef FA_HDR_BYPASS

float4 FA_PassThroughPS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    return tex2D(FA_BackBufferSampler, texcoord);
}

technique FlexAgX
{
    pass FlexAgX_PassThroughPass
    {
        VertexShader = FA_FullscreenVS;
        PixelShader = FA_PassThroughPS;
        VertexCount = 3;
    }
}

#else

uniform int InputEncoding <
    ui_category = "Main";
    ui_label = "Game Colour Curve";
    ui_type = "combo";
    ui_items = "sRGB\0Gamma 2.2\0";
    ui_tooltip = "The brightness curve your game uses. Most games use sRGB. Auto White Balance statistics assume this is set correctly; picking the wrong curve skews its colour estimate slightly.";
> = 0;

uniform int OutputEncoding <
    ui_category = "Main";
    ui_label = "Monitor Colour Curve";
    ui_type = "combo";
    ui_items = "sRGB\0Gamma 2.2\0";
    ui_tooltip = "The brightness curve your monitor uses. Leave on sRGB unless you know it differs.";
> = 0;

uniform float OverallStrength <
    ui_category = "Main";
    ui_label = "Strength";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_units = "%";
    ui_tooltip = "How strongly the effect is applied. 0% turns it off.";
> = 100.0;

uniform bool Dithering <
    ui_category = "Main";
    ui_label = "Dithering";
    ui_tooltip = "Adds faint noise to smooth gradients to prevent colour banding.";
> = true;

uniform float ExposureOffset <
    ui_category = "Brightness";
    ui_label = "Brightness";
    ui_type = "slider";
    ui_min = -2.0; ui_max = 2.0; ui_step = 0.1;
    ui_units = " EV";
    ui_tooltip = "Makes the whole image brighter or darker.";
> = 0.0;

uniform float AutoExposureStrength <
    ui_category = "Brightness";
    ui_label = "Auto Brightness";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_units = "%";
    ui_tooltip = "Automatically adjusts brightness to suit the scene. 0% turns it off.";
> = 30.0;

uniform bool FreezeExposure <
    ui_category = "Brightness";
    ui_label = "Hold Brightness";
    ui_tooltip = "Freezes auto brightness and the highlight point where they are.";
> = false;

uniform bool AutoHighlightKnee <
    ui_category = "Highlights and Shadows";
    ui_label = "Auto Highlights";
    ui_tooltip = "Automatically picks where bright areas start to soften, based on the scene.";
> = true;

uniform float HighlightKnee <
    ui_category = "Highlights and Shadows";
    ui_label = "Highlight Start";
    ui_type = "slider";
    ui_min = 0.40; ui_max = 0.55; ui_step = 0.01;
    ui_tooltip = "Where bright areas start softening toward white. Lower affects more of the bright range. Only used when Auto Highlights is off.";
> = 0.50;

uniform float ShadowPreservation <
    ui_category = "Highlights and Shadows";
    ui_label = "Shadow Detail";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_units = "%";
    ui_tooltip = "Keeps dark areas from turning flat black. 0% turns it off.";
> = 50.0;

uniform float HueRestoration <
    ui_category = "Colour";
    ui_label = "Hue Stability";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_units = "%";
    ui_tooltip = "Stops colours from shifting to a different hue, including muted ones. 0% turns it off.";
> = 100.0;

uniform float GamutRolloffStart <
    ui_category = "Colour";
    ui_label = "Vivid Colour Softening";
    ui_type = "slider";
    ui_min = 0.60; ui_max = 0.95; ui_step = 0.01;
    ui_tooltip = "How early very vivid colours get toned down to fit the screen. Lower softens more.";
> = 0.80;

uniform float ColorTemp <
    ui_category = "Colour";
    ui_label = "Colour Temperature";
    ui_type = "slider";
    ui_min = 2000.0; ui_max = 12000.0; ui_step = 50.0;
    ui_units = " K";
    ui_tooltip = "Warms or cools the image. 6500 K is neutral. Lower is warmer, higher is cooler. Fully disabled while Auto White Balance is enabled.";
> = 6500.0;

uniform bool AutoWhiteBalance <
    ui_category = "Colour";
    ui_label = "Auto White Balance";
    ui_tooltip = "Automatically removes the colour tint from the scene's lighting. Disables the Colour Temperature slider while on.";
> = false;

uniform float AutoWhiteBalanceStrength <
    ui_category = "Colour";
    ui_label = "Auto White Balance Strength";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_units = "%";
    ui_tooltip = "How strongly the auto white balance correction is applied. Only works when Auto White Balance is on.";
> = 100.0;

uniform float frametime < source = "frametime"; >;

static const float BrightenSpeed = 0.60;
static const float DarkenSpeed = 0.75;
static const float MaxChangeRate = 3.0;
static const float SceneChangeSensitivity = 0.35;
static const float ClipGuard = 2.0;

#define _FA_LOG_MIN (-12.47393)
#define _FA_LOG_MAX (4.026069)
#define _FA_LOG_RANGE (16.499999)
#define _FA_DISPLAY_GAMMA (2.4)
#define _FA_EGREY_SRGB (-2.538048)
#define _FA_EGREY_GAMMA22 (-2.786040)
#define _FA_KNEE_MIN (0.40)
#define _FA_KNEE_MAX (0.55)
#define _FA_KNEE_TAU (0.6)
#define _FA_KNEE_TAIL_MAX_EV (2.0)

#define _FA_KNEE_E90_LO (-6.0)
#define _FA_KNEE_E90_HI (0.0)
#define _FA_U_B (0.05126)
#define _FA_LUT_SIZE (1024)
#define _FA_LUT_DOMAIN (1.0)
#define _FA_GAIN_LIMIT (2.0)
#define _FA_AUTO_GAIN_LIMIT (3.0)
#define _FA_HIST_BINS (256)
#define _FA_HIST_SHIFT (32)
#define _FA_HIST_WEIGHT_SCALE (64.0)
#define _FA_HIST_WEIGHT_FALLOFF (0.85)
#define _FA_LAG_CAP (0.25)
#define _FA_EXCURSION_DECAY (0.5)
#define _FA_SHOULDER_MAX_CODE_SLOPE (2.0)
#define _FA_SHOULDER_MIN_JOIN (0.10)
#define _FA_SHOULDER_SLOPE_SAMPLES (256)
#define _FA_SHOULDER_JOIN_SEARCH_STEPS (10)
#define _FA_WB_CHROMA_MAX (0.20)
#define _FA_WB_CHROMA_EXCESS (0.3)
#define _FA_DEADBAND_EV (0.04)
#define _FA_CUT_SNAP_EV (0.5 * MaxChangeRate)
#define _FA_FULLRAMP_GUARD_MULT (3.0)
#define _FA_FULLRAMP_MIN_REF (0.5)
#define _FA_FULLRAMP_MIN_REF_CODE (4.0)
#define _FA_SCENE_CUT_SECONDS (0.10)
#define _FA_WHITE_THRESHOLD (0.98)
#if BUFFER_COLOR_BIT_DEPTH == 8
#define _FA_VALIDATION_CODES (256)
#else
#define _FA_VALIDATION_CODES (1024)
#endif
#define _FA_WARMUP_SECONDS (0.5)
#define _FA_PI (3.14159265358979323846)
#define _FA_TWO_PI (6.28318530717958647692)
#define _FA_LN2 (0.6931471805599453)

#define _FA_EPS_LUMA (1.0e-4)
#define _FA_EPS_RATIO (1.0e-6)

#define _FA_AWB_GX (((BUFFER_WIDTH) + 127) / 128)
#define _FA_AWB_GY (((BUFFER_HEIGHT) + 127) / 128)
#define _FA_AWB_TILE (8)
#define _FA_AWB_RED_FLOATS (5 * 256)
#define _FA_AWB_DARK_MIN (0.0015)
#define _FA_AWB_BRIGHT_MIN (0.50)
#define _FA_AWB_CLIP_MAX (0.985)
#define _FA_AWB_GAIN_LIMIT_LOG (0.3364722366212129)
#define _FA_AWB_CONF_ENTER (0.35)
#define _FA_AWB_CONF_EXIT (0.20)
#define _FA_AWB_CUT_CHROMA (0.12)
#define _FA_AWB_TAU (1.2)
#define _FA_AWB_MAX_RATE (0.25)
#define _FA_AWB_CUT_TAU (0.45)
#define _FA_AWB_CUT_RATE (0.35)
#define _FA_AWB_UNCERTAIN_HOLD (3.0)
#define _FA_AWB_RELAX_RATE (0.12)
#define _FA_AWB_AGREEMENT_SIGMA (0.15)
#define _FA_AWB_TARGET_TAU (0.3)
#define _FA_AWB_STRENGTH_TAU (0.25)
#define _FA_AWB_E1_CAP (0.5)
#define _FA_AWB_EDGE_MIN (0.02)
#define _FA_AWB_PLAUS_CHROMA_LO (0.45)
#define _FA_AWB_PLAUS_CHROMA_HI (0.80)

static const float3 FA_LUMA = float3(0.2126, 0.7152, 0.0722);

texture2D FA_Hist
{
    Width = _FA_HIST_BINS + 3; Height = 1; Format = R32U;
};
storage2D<uint> FA_HistStorage { Texture = FA_Hist; };

texture2D FA_HistPrev
{
    Width = _FA_HIST_BINS + 1; Height = 1; Format = R32F;
};
storage2D FA_HistPrevStorage { Texture = FA_HistPrev; };

texture2D FA_State
{
    Width = 3; Height = 1; Format = RGBA32F;
};
storage2D FA_StateStorage { Texture = FA_State; };

texture2D FA_LUT
{
    Width = _FA_LUT_SIZE; Height = 1; Format = R32F;
};
storage2D FA_LUTStorage { Texture = FA_LUT; };

sampler2D FA_LUTSampler
{
    Texture = FA_LUT;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_WB
{
    Width = 1; Height = 1; Format = RGBA32F;
};
storage2D FA_WBStorage { Texture = FA_WB; };
sampler2D FA_WBSampler
{
    Texture = FA_WB;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_AwbGroups
{
    Width = _FA_AWB_GX * 5; Height = _FA_AWB_GY; Format = RGBA32F;
};
storage2D FA_AwbGroupsStorage { Texture = FA_AwbGroups; };

texture2D FA_AwbState
{
    Width = 4; Height = 1; Format = RGBA32F;
};
storage2D FA_AwbStateStorage { Texture = FA_AwbState; };

texture2D FA_B
{
    Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RGBA16F;
};
sampler2D FA_BSampler
{
    Texture = FA_B;
    MinFilter = LINEAR; MagFilter = LINEAR; MipFilter = LINEAR;
    AddressU = CLAMP; AddressV = CLAMP;
};
storage2D FA_BStorage { Texture = FA_B; };

groupshared uint  FA_HistSh[_FA_HIST_BINS];
groupshared float FA_PrevSh[_FA_HIST_BINS];
groupshared float FA_CurSh[_FA_HIST_BINS];
groupshared uint  FA_T;
groupshared float FA_LutSh[_FA_LUT_SIZE];
groupshared float FA_LutNat[_FA_LUT_SIZE];
groupshared int   FA_StateFail;
groupshared float FA_StateGain;
groupshared float FA_StateJoin;

groupshared uint FA_P1Bins[_FA_HIST_BINS];
groupshared uint FA_P1Valid;
groupshared uint FA_P1White;
groupshared uint FA_P1Samples;
groupshared int  FA_UpdateHistRef;
groupshared float4 FA_AwbRed[_FA_AWB_RED_FLOATS];

float FA_SRGBDecode1(float c)
{
    c = max(c, 0.0);
    return (c <= 0.04045) ? (c / 12.92) : pow((c + 0.055) / 1.055, 2.4);
}

float FA_SRGBEncode1(float l)
{
    return (l <= 0.0031308) ? (12.92 * l) : (1.055 * pow(max(l, 0.0), 1.0 / 2.4) - 0.055);
}

float FA_GammaDecode1(float c) { return pow(max(c, 0.0), 2.2); }
float FA_GammaEncode1(float l) { return pow(max(l, 0.0), 1.0 / 2.2); }

float FA_InputDecode1(float c)  { return (InputEncoding == 0) ? FA_SRGBDecode1(c) : FA_GammaDecode1(c); }
float FA_InputEncode1(float l)  { return (InputEncoding == 0) ? FA_SRGBEncode1(l) : FA_GammaEncode1(l); }
float FA_OutputEncode1(float l) { return (OutputEncoding == 0) ? FA_SRGBEncode1(l) : FA_GammaEncode1(l); }

float3 FA_Decode(float3 c)
{
    return float3(FA_InputDecode1(c.r), FA_InputDecode1(c.g), FA_InputDecode1(c.b));
}

float3 FA_Encode(float3 c)
{
    return float3(FA_OutputEncode1(c.r), FA_OutputEncode1(c.g), FA_OutputEncode1(c.b));
}

float3 FA_Sanitize(float3 c)
{
    return max(c, 0.0);
}

bool FA_Finite1(float v)
{
    return (v > -1.0e30) && (v < 1.0e30);
}

float FA_AgxPolynomial(float x)
{
    float x2 = x * x;
    float x3 = x2 * x;
    float x4 = x3 * x;
    float x5 = x4 * x;
    float x6 = x5 * x;
    return 15.5 * x6 - 40.14 * x5 + 31.96 * x4 - 6.868 * x3 + 0.4298 * x2 + 0.1191 * x - 0.00232;
}

float FA_DisplayGamma()
{
    return (OutputEncoding == 0) ? _FA_DISPLAY_GAMMA : 2.2;
}

float FA_NW()
{
    return pow(max(FA_AgxPolynomial(1.0), 0.0), FA_DisplayGamma());
}

float FA_Dn(float s)
{
    if (s <= 0.0) return 0.0;
    float xs = clamp((log2(s) - _FA_LOG_MIN) / _FA_LOG_RANGE, 0.0, 1.0);
    return pow(max(FA_AgxPolynomial(xs), 0.0), FA_DisplayGamma()) / FA_NW();
}

float FA_Native(float u, float gain)
{
    if (u <= 0.0) return 0.0;
    return FA_Dn(gain * u);
}

float FA_PolyDeriv(float x)
{
    float x2 = x * x;
    float x3 = x2 * x;
    float x4 = x3 * x;
    float x5 = x4 * x;
    return 93.0 * x5 - 200.7 * x4 + 127.84 * x3 - 20.604 * x2 + 0.8596 * x + 0.1191;
}

float FA_DnDeriv(float s)
{
    if (s <= exp2(_FA_LOG_MIN) || s >= exp2(_FA_LOG_MAX)) return 0.0;
    float xs = (log2(s) - _FA_LOG_MIN) / _FA_LOG_RANGE;
    float p = max(FA_AgxPolynomial(xs), 0.0);
    float g = FA_DisplayGamma();
    return (g * pow(p, g - 1.0) * FA_PolyDeriv(xs))
         / (s * _FA_LN2 * _FA_LOG_RANGE * FA_NW());
}

float FA_NativeSlope(float u, float gain)
{
    if (u <= 0.0) return 0.0;
    return gain * FA_DnDeriv(gain * u);
}

float FA_Hermite(float x, float x0, float x1, float y0, float y1, float m0, float m1)
{
    float dx = x1 - x0;
    float t = (x - x0) / dx;
    float t2 = t * t;
    float t3 = t2 * t;
    return (2.0 * t3 - 3.0 * t2 + 1.0) * y0
         + (t3 - 2.0 * t2 + t) * dx * m0
         + (-2.0 * t3 + 3.0 * t2) * y1
         + (t3 - t2) * dx * m1;
}

float FA_HermiteDeriv(float x, float x0, float x1, float y0, float y1, float m0, float m1)
{
    float dx = x1 - x0;
    float t = (x - x0) / dx;
    float t2 = t * t;
    return ((6.0 * t2 - 6.0 * t) * y0
         + (3.0 * t2 - 4.0 * t + 1.0) * dx * m0
         + (-6.0 * t2 + 6.0 * t) * y1
         + (3.0 * t2 - 2.0 * t) * dx * m1) / dx;
}

float FA_BaseCurve(float u, float gain)
{
    float n = FA_Native(u, gain);
    if (u < _FA_U_B)
    {
        float nb = FA_Native(_FA_U_B, gain);
        float secant = nb / _FA_U_B;
        float db = FA_NativeSlope(_FA_U_B, gain);

        float m0 = min(1.0, 3.0 * secant);
        float m1 = min(db, 3.0 * secant);
        float toe = FA_Hermite(u, 0.0, _FA_U_B, 0.0, nb, m0, m1);
        n = lerp(n, toe, ShadowPreservation / 100.0);
    }
    return n;
}

float FA_BaseCurveSlope(float u, float gain)
{
    if (u <= 0.0) return 0.0;
    float alpha = ShadowPreservation / 100.0;
    if (alpha <= 0.0 || u >= _FA_U_B) return FA_NativeSlope(u, gain);

    float nb = FA_Native(_FA_U_B, gain);
    float secant = nb / _FA_U_B;
    float db = FA_NativeSlope(_FA_U_B, gain);
    float m0 = min(1.0, 3.0 * secant);
    float m1 = min(db, 3.0 * secant);
    float nativeDeriv = FA_NativeSlope(u, gain);
    float toeDeriv = FA_HermiteDeriv(u, 0.0, _FA_U_B, 0.0, nb, m0, m1);
    return lerp(nativeDeriv, toeDeriv, alpha);
}

float FA_ResolveKneeJoin(float uK, float gain)
{
    uK = min(uK, 0.85);
    float y0 = FA_BaseCurve(uK, gain);
    float slope0 = FA_BaseCurveSlope(uK, gain);
    float secantH = (1.0 - y0) / max(1.0 - uK, _FA_EPS_RATIO);
    if (slope0 > 3.0 * secantH && uK < 0.85)
    {
        float lo = uK;
        float hi = 0.85;
        for (int joinIter = 0; joinIter < 24; ++joinIter)
        {
            float mid = 0.5 * (lo + hi);
            float ym = FA_BaseCurve(mid, gain);
            float sm = FA_BaseCurveSlope(mid, gain);
            float sc = (1.0 - ym) / max(1.0 - mid, _FA_EPS_RATIO);
            if (sm > 3.0 * sc) lo = mid; else hi = mid;
        }
        uK = hi;
    }
    return uK;
}

void FA_ShoulderTangents(float gain, float uK, out float y0, out float m0)
{
    y0 = FA_BaseCurve(uK, gain);
    float slope0 = FA_BaseCurveSlope(uK, gain);
    float secantH = (1.0 - y0) / max(1.0 - uK, _FA_EPS_RATIO);
    m0 = clamp(slope0, 0.0, 3.0 * secantH);
}

float FA_ComposedCurveEx(float u, float gain, float uK, float y0, float m0)
{
    if (u <= 0.0) return 0.0;
    if (u >= 1.0) return 1.0;

    if (u > uK)
        return FA_Hermite(u, uK, 1.0, y0, 1.0, m0, 0.0);
    return FA_BaseCurve(u, gain);
}

float FA_EncodedShoulderMaxSlope(float gain, float uK)
{
    float y0, m0;
    FA_ShoulderTangents(gain, uK, y0, m0);

    float firstCode = clamp(FA_InputEncode1(uK), 1.0 / 255.0, 0.999);
    float previousCode = firstCode;
    float previousOutput = FA_OutputEncode1(
        FA_Hermite(FA_InputDecode1(firstCode), uK, 1.0, y0, 1.0, m0, 0.0));
    float maximumSlope = 0.0;

    for (int i = 1; i <= _FA_SHOULDER_SLOPE_SAMPLES; ++i)
    {
        float inputCode = lerp(firstCode, 1.0, (float)i / (float)_FA_SHOULDER_SLOPE_SAMPLES);
        float inputLinear = FA_InputDecode1(inputCode);
        float outputLinear = FA_Hermite(inputLinear, uK, 1.0, y0, 1.0, m0, 0.0);
        float outputCode = FA_OutputEncode1(outputLinear);
        float slope = (outputCode - previousOutput) / max(inputCode - previousCode, _FA_EPS_RATIO);
        maximumSlope = max(maximumSlope, slope);
        previousCode = inputCode;
        previousOutput = outputCode;
    }
    return maximumSlope;
}

float FA_ChooseKneeJoin(float gain, float knee)
{
    float requestedJoin = min(knee / max(gain, _FA_EPS_LUMA), 0.85);
    float desiredJoin = FA_ResolveKneeJoin(requestedJoin, gain);
    if (FA_EncodedShoulderMaxSlope(gain, desiredJoin) <= _FA_SHOULDER_MAX_CODE_SLOPE)
        return desiredJoin;

    float low = FA_ResolveKneeJoin(min(desiredJoin, _FA_SHOULDER_MIN_JOIN), gain);
    if (low > desiredJoin)
        low = desiredJoin;
    if (FA_EncodedShoulderMaxSlope(gain, low) > _FA_SHOULDER_MAX_CODE_SLOPE)
        return low;

    float high = desiredJoin;
    for (int i = 0; i < _FA_SHOULDER_JOIN_SEARCH_STEPS; ++i)
    {
        float mid = 0.5 * (low + high);
        float candidate = FA_ResolveKneeJoin(mid, gain);
        if (FA_EncodedShoulderMaxSlope(gain, candidate) <= _FA_SHOULDER_MAX_CODE_SLOPE)
            low = candidate;
        else
            high = mid;
    }
    return low;
}

void FA_LutSpan(float x, out int i0, out int i1, out float t)
{
    float fi = clamp(x, 0.0, (float)(_FA_LUT_SIZE - 1));
    i0 = (int)fi;
    i1 = min(i0 + 1, _FA_LUT_SIZE - 1);
    t = fi - (float)i0;
}

float FA_LutSampleShared(float x)
{
    int i0, i1; float t;
    FA_LutSpan(x, i0, i1, t);
    return lerp(FA_LutSh[i0], FA_LutSh[i1], t);
}

float FA_LutSampleNat(float x)
{
    int i0, i1; float t;
    FA_LutSpan(x, i0, i1, t);
    return lerp(FA_LutNat[i0], FA_LutNat[i1], t);
}

float FA_LUTFetch(float x)
{
    int i0, i1; float t;
    FA_LutSpan(x, i0, i1, t);
    float v0 = tex2Dfetch(FA_LUTSampler, int2(i0, 0)).r;
    float v1 = tex2Dfetch(FA_LUTSampler, int2(i1, 0)).r;
    return lerp(v0, v1, t);
}

void FA_FillLutSh(uint lane, float gain, float uK, float y0, float m0)
{
    for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
    {
        float u = _FA_LUT_DOMAIN * (float)i / (float)(_FA_LUT_SIZE - 1);
        FA_LutSh[i] = FA_ComposedCurveEx(u, gain, uK, y0, m0);
    }
}

float FA_SignedCbrt(float c)
{
    return sign(c) * pow(abs(c), 1.0 / 3.0);
}

float3 FA_OklabFromLinear(float3 rgb)
{
    float3 lms;
    lms.x = dot(float3(0.4122214708, 0.5363325363, 0.0514459929), rgb);
    lms.y = dot(float3(0.2119034982, 0.6806995451, 0.1073969566), rgb);
    lms.z = dot(float3(0.0883024619, 0.2817188376, 0.6299787005), rgb);
    float3 lmsP = float3(FA_SignedCbrt(lms.x), FA_SignedCbrt(lms.y), FA_SignedCbrt(lms.z));
    return float3(
        dot(float3(0.2104542553, 0.7936177850, -0.0040720468), lmsP),
        dot(float3(1.9779984951, -2.4285922050, 0.4505937099), lmsP),
        dot(float3(0.0259040371, 0.7827717662, -0.8086757660), lmsP));
}

float3 FA_LinearFromOklab(float3 lab)
{
    float L = lab.x, a = lab.y, b = lab.z;
    float lp = L + 0.3963377774 * a + 0.2158037573 * b;
    float mp = L - 0.1055613458 * a - 0.0638541728 * b;
    float sp = L - 0.0894841775 * a - 1.2914855480 * b;
    float l = lp * lp * lp;
    float m = mp * mp * mp;
    float s = sp * sp * sp;
    return float3(
         4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s);
}

float3 FA_Inset(float3 rgb)
{
    return float3(
        dot(float3(0.842479062253094, 0.0423282422610123, 0.0423756549057051), rgb),
        dot(float3(0.0784335999999992, 0.878468636469772, 0.0784336), rgb),
        dot(float3(0.0792237451477643, 0.0791661274605434, 0.879142973793104), rgb));
}

float3 FA_Outset(float3 rgb)
{
    return float3(
        dot(float3(1.19687900512017, -0.0528968517574562, -0.0529716355144438), rgb),
        dot(float3(-0.0980208811401368, 1.15190312990417, -0.0980434501171241), rgb),
        dot(float3(-0.0990297440797205, -0.0989611768448433, 1.15107367264116), rgb));
}

float FA_WrapAngle(float a)
{
    return a - _FA_TWO_PI * floor((a + _FA_PI) / _FA_TWO_PI);
}

float FA_CompressiveRolloff(float x, float start)
{
    if (x <= start) return x;

    float endValue = 0.5 * (1.0 + start);
    if (x < 1.0)
    {
        float t = (x - start) / (1.0 - start);
        return start + (1.0 - start) * (t - 0.5 * t * t);
    }

    float over = x - 1.0;
    return 1.0 - (1.0 - endValue) / (1.0 + 4.0 * over * over);
}

float3 FA_GamutRowsAt(float u, float kl, float km, float ks)
{
    float l_ = 1.0 + u * kl;
    float m_ = 1.0 + u * km;
    float s_ = 1.0 + u * ks;
    float l = l_ * l_ * l_;
    float m = m_ * m_ * m_;
    float s = s_ * s_ * s_;
    return float3(
         4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s);
}

float FA_MinGamutRow(float u, float kl, float km, float ks)
{
    float3 rows = FA_GamutRowsAt(u, kl, km, ks);
    return min(rows.x, min(rows.y, rows.z));
}

float FA_RowDipCandidate(float A, float B, float C, float D, float uEnd, float best)
{
    float fe = ((A * uEnd + B) * uEnd + C) * uEnd + D;
    if (fe < -1.0e-6 && uEnd < best) best = uEnd;

    float disc = B * B - 3.0 * A * C;
    if (abs(A) > 1.0e-9)
    {
        if (disc > 0.0)
        {
            float sq = sqrt(disc);
            float u1 = (-B - sq) / (3.0 * A);
            float u2 = (-B + sq) / (3.0 * A);
            float f1 = ((A * u1 + B) * u1 + C) * u1 + D;
            if (u1 > 0.0 && u1 < uEnd && f1 < -1.0e-6 && u1 < best) best = u1;
            float f2 = ((A * u2 + B) * u2 + C) * u2 + D;
            if (u2 > 0.0 && u2 < uEnd && f2 < -1.0e-6 && u2 < best) best = u2;
        }
    }
    else if (abs(B) > 1.0e-9)
    {
        float u = -C / (2.0 * B);
        float f = ((A * u + B) * u + C) * u + D;
        if (u > 0.0 && u < uEnd && f < -1.0e-6 && u < best) best = u;
    }
    return best;
}

float FA_FirstDipLocation(float uEnd, float kl, float km, float ks)
{
    float kl2 = kl * kl, km2 = km * km, ks2 = ks * ks;
    float kl3 = kl2 * kl, km3 = km2 * km, ks3 = ks2 * ks;

    float dip = FA_RowDipCandidate(
        +4.0767416621 * kl3 - 3.3077115913 * km3 + 0.2309699292 * ks3,
        3.0 * (+4.0767416621 * kl2 - 3.3077115913 * km2 + 0.2309699292 * ks2),
        3.0 * (+4.0767416621 * kl  - 3.3077115913 * km  + 0.2309699292 * ks),
        +4.0767416621 - 3.3077115913 + 0.2309699292, uEnd, 1.0e30);
    dip = FA_RowDipCandidate(
        -1.2684380046 * kl3 + 2.6097574011 * km3 - 0.3413193965 * ks3,
        3.0 * (-1.2684380046 * kl2 + 2.6097574011 * km2 - 0.3413193965 * ks2),
        3.0 * (-1.2684380046 * kl  + 2.6097574011 * km  - 0.3413193965 * ks),
        -1.2684380046 + 2.6097574011 - 0.3413193965, uEnd, dip);
    dip = FA_RowDipCandidate(
        -0.0041960863 * kl3 - 0.7034186147 * km3 + 1.7076147010 * ks3,
        3.0 * (-0.0041960863 * kl2 - 0.7034186147 * km2 + 1.7076147010 * ks2),
        3.0 * (-0.0041960863 * kl  - 0.7034186147 * km  + 1.7076147010 * ks),
        -0.0041960863 - 0.7034186147 + 1.7076147010, uEnd, dip);
    return (dip < 1.0e29) ? dip : 0.0;
}

float FA_BisectFirstCrossing(float uDip, float kl, float km, float ks)
{
    float lo = 0.0;
    float hi = uDip;
    [loop]
    for (int repair = 0; repair < 30; ++repair)
    {
        float mid = 0.5 * (lo + hi);
        if (FA_MinGamutRow(mid, kl, km, ks) >= 0.0) lo = mid;
        else hi = mid;
    }
    return lo;
}

float FA_FitHalley(float a, float b, float k0, float k1, float k2, float k3, float k4,
                   float wl, float wm, float ws, float kl, float km, float ks)
{
    float S = k0 + k1 * a + k2 * b + k3 * a * a + k4 * a * b;
    [unroll]
    for (int refine = 0; refine < 2; ++refine)
    {
        float l_ = 1.0 + S * kl;
        float m_ = 1.0 + S * km;
        float s_ = 1.0 + S * ks;
        float l = l_ * l_ * l_;
        float m = m_ * m_ * m_;
        float s = s_ * s_ * s_;
        float ldS = 3.0 * kl * l_ * l_;
        float mdS = 3.0 * km * m_ * m_;
        float sdS = 3.0 * ks * s_ * s_;
        float ldS2 = 6.0 * kl * kl * l_;
        float mdS2 = 6.0 * km * km * m_;
        float sdS2 = 6.0 * ks * ks * s_;
        float F  = wl * l + wm * m + ws * s;
        float F1 = wl * ldS + wm * mdS + ws * sdS;
        float F2 = wl * ldS2 + wm * mdS2 + ws * sdS2;
        S -= F * F1 / (F1 * F1 - 0.5 * F * F2);
    }
    return S;
}

bool FA_TryRegion(float a, float b, float kl, float km, float ks,
                  float k0, float k1, float k2, float k3, float k4,
                  float wl, float wm, float ws, int rowIdx, out float S)
{
    S = FA_FitHalley(a, b, k0, k1, k2, k3, k4, wl, wm, ws, kl, km, ks);
    if (!FA_Finite1(S) || S <= 0.0 || S >= 4.0) return false;

    float uDip = FA_FirstDipLocation(S * (1.0 - 1.0e-4), kl, km, ks);
    if (uDip > 0.0)
    {
        S = FA_BisectFirstCrossing(uDip, kl, km, ks);
        return true;
    }

    float3 rows = FA_GamutRowsAt(S, kl, km, ks);
    float F = (rowIdx == 0) ? rows.x : ((rowIdx == 1) ? rows.y : rows.z);
    return abs(F) <= 1.0e-5;
}

float FA_ComputeMaxSaturation(float a, float b)
{
    float kl = +0.3963377774 * a + 0.2158037573 * b;
    float km = -0.1055613458 * a - 0.0638541728 * b;
    float ks = -0.0894841775 * a - 1.2914855480 * b;

    float S;
    bool ok;
    if (-1.88170328 * a - 0.80936493 * b > 1.0)
        ok = FA_TryRegion(a, b, kl, km, ks, +1.19086277, +1.76576728, +0.59662641, +0.75515197, +0.56771245,
                          +4.0767416621, -3.3077115913, +0.2309699292, 0, S);
    else if (1.81444104 * a - 1.19445276 * b > 1.0)
        ok = FA_TryRegion(a, b, kl, km, ks, +0.73956515, -0.45954404, +0.08285427, +0.12541070, +0.14503204,
                          -1.2684380046, +2.6097574011, -0.3413193965, 1, S);
    else
        ok = FA_TryRegion(a, b, kl, km, ks, +1.35733652, -0.00915799, -1.15130210, -0.50559606, +0.00692167,
                          -0.0041960863, -0.7034186147, +1.7076147010, 2, S);

    if (ok) return S;

    float Sa, Sb;
    bool okA = FA_TryRegion(a, b, kl, km, ks, +0.73956515, -0.45954404, +0.08285427, +0.12541070, +0.14503204,
                            -1.2684380046, +2.6097574011, -0.3413193965, 1, Sa);
    bool okB = FA_TryRegion(a, b, kl, km, ks, +1.35733652, -0.00915799, -1.15130210, -0.50559606, +0.00692167,
                            -0.0041960863, -0.7034186147, +1.7076147010, 2, Sb);
    if (okA && okB) return min(Sa, Sb);
    if (okA) return Sa;
    if (okB) return Sb;

    return FA_BisectFirstCrossing(0.85, kl, km, ks);
}

float FA_GamutMaxChroma(float L, float a, float b)
{
    float S = FA_ComputeMaxSaturation(a, b);
    S = clamp(S, 0.0, 4.0);

    float kl = +0.3963377774 * a + 0.2158037573 * b;
    float km = -0.1055613458 * a - 0.0638541728 * b;
    float ks = -0.0894841775 * a - 1.2914855480 * b;

    float3 rgbAtMax = FA_LinearFromOklab(float3(1.0, S * a, S * b));
    float LCusp = pow(max(max(rgbAtMax.r, max(rgbAtMax.g, rgbAtMax.b)), 1.0e-6), -1.0 / 3.0);

    float t;
    if (L <= LCusp)
    {
        t = S * L;
    }
    else
    {
        t = S * LCusp * (L - 1.0) / (LCusp - 1.0);

        float lDt = kl;
        float mDt = km;
        float sDt = ks;

        [unroll]
        for (int refine = 0; refine < 3; ++refine)
        {
            float l_ = L + t * kl;
            float m_ = L + t * km;
            float s_ = L + t * ks;
            float l = l_ * l_ * l_;
            float m = m_ * m_ * m_;
            float s = s_ * s_ * s_;
            float ldt = 3.0 * lDt * l_ * l_;
            float mdt = 3.0 * mDt * m_ * m_;
            float sdt = 3.0 * sDt * s_ * s_;
            float ldt2 = 6.0 * lDt * lDt * l_;
            float mdt2 = 6.0 * mDt * mDt * m_;
            float sdt2 = 6.0 * sDt * sDt * s_;

            float rD = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s - 1.0;
            float r1 = 4.0767416621 * ldt - 3.3077115913 * mdt + 0.2309699292 * sdt;
            float r2 = 4.0767416621 * ldt2 - 3.3077115913 * mdt2 + 0.2309699292 * sdt2;

            float gD = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s - 1.0;
            float g1 = -1.2684380046 * ldt + 2.6097574011 * mdt - 0.3413193965 * sdt;
            float g2 = -1.2684380046 * ldt2 + 2.6097574011 * mdt2 - 0.3413193965 * sdt2;

            float bD = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s - 1.0;
            float b1 = -0.0041960863 * ldt - 0.7034186147 * mdt + 1.7076147010 * sdt;
            float b2 = -0.0041960863 * ldt2 - 0.7034186147 * mdt2 + 1.7076147010 * sdt2;

            float F = rD, F1 = r1, F2 = r2;
            if (gD > F) { F = gD; F1 = g1; F2 = g2; }
            if (bD > F) { F = bD; F1 = b1; F2 = b2; }

            float denom = F1 * F1 - 0.5 * F * F2;
            t -= (abs(denom) > 1.0e-9) ? (F * F1 / denom)
                                       : ((abs(F1) > 1.0e-9) ? (F / F1) : 0.0);
            t = clamp(t, 0.0, S * L);
        }

        t = clamp(t, 0.0, S * L);
    }

    if (!FA_Finite1(t) || t < 0.0) t = 0.0;
    return t;
}

float FA_IGN(float x, float y)
{
    return frac(52.9829189 * frac(0.06711056 * x + 0.00583715 * y));
}

static const float3x3 FA_RGB_TO_LMS = float3x3(
    0.4122214708, 0.5363325363, 0.0514459929,
    0.2119034982, 0.6806995451, 0.1073969566,
    0.0883024619, 0.2817188376, 0.6299787005);

static const float3x3 FA_LMS_TO_RGB = float3x3(
     4.0767416621, -3.3077115913,  0.2309699292,
    -1.2684380046,  2.6097574011, -0.3413193965,
    -0.0041960863, -0.7034186147,  1.7076147010);

static const float3 FA_WB_REFERENCE_LMS = float3(1.0106792805, 1.0017568775, 1.0211812566);

float3 FA_TempWhiteRGB(float tempK)
{
    float u = 1000.0 / tempK;
    float u2 = u * u;
    float u3 = u2 * u;
    float x = (tempK < 4000.0)
        ? -0.2661239 * u3 - 0.2343580 * u2 + 0.8776956 * u + 0.179910
        : -3.0258469 * u3 + 2.1070379 * u2 + 0.2226347 * u + 0.240390;
    float x2 = x * x;
    float x3 = x2 * x;
    float y;
    if (tempK < 2222.0)
        y = -1.1063814 * x3 - 1.34811020 * x2 + 2.18555832 * x - 0.20219683;
    else if (tempK < 4000.0)
        y = -0.9549476 * x3 - 1.37418593 * x2 + 2.09137015 * x - 0.16748867;
    else
        y = 3.0817580 * x3 - 5.87338670 * x2 + 3.75112997 * x - 0.37001483;
    float invY = 1.0 / max(y, 1.0e-4);
    float X = x * invY;
    float Z = (1.0 - x - y) * invY;

    float3 w = float3(
        3.2406255 * X - 1.5372080 - 0.4986286 * Z,
       -0.9689307 * X + 1.8757561 + 0.0415175 * Z,
        0.0557101 * X - 0.2040211 + 1.0569959 * Z);
    w = max(w, 0.0);
    return w / max(dot(w, FA_LUMA), 1.0e-6);
}

float3 FA_ColorTempGain()
{
    float3 white = FA_TempWhiteRGB(clamp(ColorTemp, 1667.0, 25000.0));

    float3 lab = FA_OklabFromLinear(white);
    float C = sqrt(lab.y * lab.y + lab.z * lab.z);
    if (C > _FA_WB_CHROMA_MAX)
    {
        float c2 = _FA_WB_CHROMA_MAX + (C - _FA_WB_CHROMA_MAX) * _FA_WB_CHROMA_EXCESS;
        lab.y *= c2 / C;
        lab.z *= c2 / C;
        white = FA_LinearFromOklab(lab);
        white = max(white, 0.0);
        white /= max(dot(white, FA_LUMA), 1.0e-4);
    }

    float3 lmsW = mul(FA_RGB_TO_LMS, white);
    return lmsW / FA_WB_REFERENCE_LMS;
}

float3 FA_WhiteBalance(float3 rgb, float3 wbGain)
{
    float3 lms = mul(FA_RGB_TO_LMS, rgb) * wbGain;
    return mul(FA_LMS_TO_RGB, lms);
}

float3 FA_AwbNormLuma(float3 e)
{
    return e / max(dot(e, FA_LUMA), 1.0e-6);
}

float FA_AwbPlausibility(float3 e)
{
    float X = dot(e, float3(0.4124564, 0.3575761, 0.1804375));
    float Y = max(dot(e, FA_LUMA), 1.0e-6);
    float Z = dot(e, float3(0.0193339, 0.1191920, 0.9503041));
    float sum = max(X + Y + Z, 1.0e-6);
    float x = X / sum;
    float y = Y / sum;
    float denom = 0.1858 - y;
    denom = (abs(denom) < 1.0e-4) ? ((denom < 0.0) ? -1.0e-4 : 1.0e-4) : denom;
    float n = (x - 0.3320) / denom;
    float cct = 449.0 * n * n * n + 3525.0 * n * n + 6823.3 * n + 5520.33;
    float cctPlaus = smoothstep(1800.0, 3000.0, cct)
                   * (1.0 - smoothstep(9000.0, 18000.0, cct));
    float3 logE = log(max(e, 1.0e-6));
    float chroma = length(logE - dot(logE, FA_LUMA));
    float chromaPlaus = 1.0 - smoothstep(_FA_AWB_PLAUS_CHROMA_LO, _FA_AWB_PLAUS_CHROMA_HI, chroma);
    return saturate(cctPlaus * chromaPlaus);
}

float3 FA_AwbCorrectionLog(float3 e)
{
    float3 corr = 1.0 / max(e, 1.0e-4);
    corr /= max(dot(corr, FA_LUMA), 1.0e-6);
    float3 l = log(max(corr, 1.0e-6));
    l -= dot(l, FA_LUMA);
    return l;
}

float3 FA_AwbCurvedGrey(float3 c)
{
    float3 w = FA_Inset(float3(1.0, 1.0, 1.0));
    float lutScale = (float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN;
    float3 x3 = (FA_Inset(c) / w) * lutScale;
    float3 v = float3(FA_LUTFetch(x3.r), FA_LUTFetch(x3.g), FA_LUTFetch(x3.b));
    return clamp(max(FA_Outset(v * w), 0.0), 0.0, 1.0);
}

void FA_LutPath(float3 rgbIn, out float3 u, out float3 linearOut, out float3 codeOut)
{
    float3 w = FA_Inset(float3(1.0, 1.0, 1.0));
    float lutScale = (float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN;

    u = clamp(FA_Inset(FA_Decode(rgbIn)) / w, 0.0, _FA_LUT_DOMAIN);
    float3 outv = float3(FA_LutSampleShared(u.r * lutScale),
                         FA_LutSampleShared(u.g * lutScale),
                         FA_LutSampleShared(u.b * lutScale));
    linearOut = clamp(max(FA_Outset(outv * w), 0.0), 0.0, 1.0);
    codeOut = 255.0 * FA_Encode(linearOut);
}

bool FA_ValidateLut()
{
    int passed = 1;
    float lutScale = (float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN;
    float inputStep = 255.0 / (float)(_FA_VALIDATION_CODES - 1);

    float3 previousCode = float3(-1.0, -1.0, -1.0);
    float3 previousCodeFloat = float3(-1.0, -1.0, -1.0);
    float previousNativeCode = 0.0;
    [loop]
    for (int i = 0; i < _FA_VALIDATION_CODES; ++i)
    {
        float c = (float)i / (float)(_FA_VALIDATION_CODES - 1);
        float3 u, linearOut, codeOutFloat;
        FA_LutPath(c.xxx, u, linearOut, codeOutFloat);
        float3 codeOut = round(codeOutFloat);
        float nativeCode = 255.0 * FA_OutputEncode1(
            FA_LutSampleNat(FA_InputDecode1(c) * lutScale));
        if (i > 0)
        {
            if (any(codeOut < previousCode)) passed = 0;
            float3 outSlope = (codeOutFloat - previousCodeFloat) / inputStep;
            if (u.x > FA_StateJoin &&
                any(outSlope > _FA_SHOULDER_MAX_CODE_SLOPE + 0.05))
                passed = 0;
            float nativeSlope = (nativeCode - previousNativeCode) / inputStep;
            float stepLimit = max(_FA_SHOULDER_MAX_CODE_SLOPE + 0.05,
                                  _FA_FULLRAMP_GUARD_MULT * nativeSlope);
            if (nativeSlope < _FA_FULLRAMP_MIN_REF ||
                nativeCode < _FA_FULLRAMP_MIN_REF_CODE)
            {
                float cPrev = (float)(i - 1) / (float)(_FA_VALIDATION_CODES - 1);
                float passSlope = 255.0 *
                    (FA_OutputEncode1(FA_InputDecode1(c))
                   - FA_OutputEncode1(FA_InputDecode1(cPrev))) / inputStep;
                stepLimit = max(stepLimit, passSlope);
            }
            if (outSlope.x > stepLimit)
                passed = 0;
        }
        previousCode = codeOut;
        previousCodeFloat = codeOutFloat;
        previousNativeCode = nativeCode;
    }

    for (int greyIndex = 0; greyIndex < 4 && passed != 0; ++greyIndex)
    {
        float grey = 0.25 * (float)greyIndex;
        for (int hueIndex = 0; hueIndex < 6 && passed != 0; ++hueIndex)
        {
            float3 hueMask = float3(1.0, 0.0, 0.0);
            if (hueIndex == 1) hueMask = float3(0.0, 1.0, 0.0);
            else if (hueIndex == 2) hueMask = float3(0.0, 0.0, 1.0);
            else if (hueIndex == 3) hueMask = float3(0.0, 1.0, 1.0);
            else if (hueIndex == 4) hueMask = float3(1.0, 0.0, 1.0);
            else if (hueIndex == 5) hueMask = float3(1.0, 1.0, 0.0);

            float3 previousChromaCode = float3(-1.0, -1.0, -1.0);
            float previousChromaLuma = -1.0;
            const int chromaSteps = 16;
            float chromaInputCodes = max((1.0 - grey) * 255.0 / (float)chromaSteps, _FA_EPS_RATIO);
            [loop]
            for (int s = 0; s <= chromaSteps; ++s)
            {
                float t = (float)s / (float)chromaSteps;
                float3 chromaRampIn = clamp(grey.xxx + hueMask * (t * (1.0 - grey)), 0.0, 1.0);
                float3 chromaU, chromaLinear, chromaCodeOut;
                FA_LutPath(chromaRampIn, chromaU, chromaLinear, chromaCodeOut);
                float chromaLuma = 255.0 * dot(chromaLinear, FA_LUMA);
                if (s > 0)
                {
                    if (any(previousChromaCode - chromaCodeOut > 3.0 * chromaInputCodes))
                        passed = 0;
                    if (max(chromaU.x, max(chromaU.y, chromaU.z)) <= FA_StateJoin &&
                        previousChromaLuma - chromaLuma > 0.0025 * chromaInputCodes)
                        passed = 0;
                }
                previousChromaCode = chromaCodeOut;
                previousChromaLuma = chromaLuma;
            }
        }
    }

    if (!(FA_LutSh[0] >= 0.0 && FA_LutSh[0] <= 1.000001)) passed = 0;
    [loop]
    for (int i = 1; i < _FA_LUT_SIZE; ++i)
    {
        if (!(FA_LutSh[i] >= FA_LutSh[i - 1] - _FA_EPS_RATIO) ||
            !(FA_LutSh[i] >= 0.0) || !(FA_LutSh[i] <= 1.000001))
        {
            passed = 0;
            break;
        }
    }

    return passed != 0;
}

void FA_HistPercentiles(float total, out float e50, out float e90, out float e99)
{
    const float binWidth = _FA_LOG_RANGE / (float)_FA_HIST_BINS;
    const float t50 = 0.50 * total;
    const float t90 = 0.90 * total;
    const float t99 = 0.99 * total;
    bool f50 = false, f90 = false, f99 = false;
    e50 = _FA_LOG_MIN;
    e90 = _FA_LOG_MIN;
    e99 = _FA_LOG_MIN;

    float cumulative = 0.0;
    [loop]
    for (int i = 0; i < _FA_HIST_BINS; ++i)
    {
        float previous = cumulative;
        cumulative += (float)FA_HistSh[i];
        if (!f50 && cumulative >= t50)
        {
            e50 = _FA_LOG_MIN + ((float)i + saturate((t50 - previous) / max((float)FA_HistSh[i], 1.0e-6))) * binWidth;
            f50 = true;
        }
        if (!f90 && cumulative >= t90)
        {
            e90 = _FA_LOG_MIN + ((float)i + saturate((t90 - previous) / max((float)FA_HistSh[i], 1.0e-6))) * binWidth;
            f90 = true;
        }
        if (!f99 && cumulative >= t99)
        {
            e99 = _FA_LOG_MIN + ((float)i + saturate((t99 - previous) / max((float)FA_HistSh[i], 1.0e-6))) * binWidth;
            f99 = true;
        }
    }
}

void FA_HistDistance(out float d, out float drawRaw)
{
    float invT = 1.0 / (float)FA_T;

    [loop]
    for (int i = 0; i < _FA_HIST_BINS; ++i)
        FA_CurSh[i] = (float)FA_HistSh[i] * invT;

    drawRaw = 0.0;
    [loop]
    for (int i = 0; i < _FA_HIST_BINS; ++i)
        drawRaw += abs(FA_CurSh[i] - FA_PrevSh[i]);
    drawRaw *= 0.5;
    d = drawRaw;

    if (drawRaw > SceneChangeSensitivity)
    {
        [loop]
        for (int s = -_FA_HIST_SHIFT; s <= _FA_HIST_SHIFT; ++s)
        {
            if (s == 0) continue;
            float ds = 0.0;
            [loop]
            for (int i = 0; i < _FA_HIST_BINS; ++i)
                ds += abs(FA_CurSh[i] - FA_PrevSh[clamp(i + s, 0, _FA_HIST_BINS - 1)]);
            d = min(d, 0.5 * ds);
        }
    }
}

[numthreads(256, 1, 1)]
void FA_StateCS(uint3 id : SV_DispatchThreadID, uint3 tid : SV_GroupThreadID)
{
    uint lane = tid.x;

    if (OverallStrength <= 0.0)
    {
        if (lane < _FA_HIST_BINS)
        {
            tex2Dstore(FA_HistStorage, int2((int)lane, 0), 0u);
            tex2Dstore(FA_HistPrevStorage, int2((int)lane, 0), float4(0.0, 0.0, 0.0, 0.0));
        }
        if (lane < 3)
            tex2Dstore(FA_HistStorage, int2(_FA_HIST_BINS + (int)lane, 0), 0u);
        if (lane == 0)
            tex2Dstore(FA_HistPrevStorage, int2(_FA_HIST_BINS, 0), float4(0.0, 0.0, 0.0, 0.0));
        if (lane < 2)
            tex2Dstore(FA_StateStorage, int2((int)lane, 0), float4(0.0, 0.0, 0.0, 0.0));
        if (lane == 2)
            tex2Dstore(FA_StateStorage, int2(2, 0), float4(0.0, -1.0, -1.0, -1.0));
        return;
    }

    if (lane < _FA_HIST_BINS)
    {
        FA_HistSh[lane] = tex2Dfetch(FA_HistStorage, int2((int)lane, 0)).x;
        FA_PrevSh[lane] = tex2Dfetch(FA_HistPrevStorage, int2((int)lane, 0)).r;
        if (!FA_Finite1(FA_PrevSh[lane])) FA_PrevSh[lane] = 0.0;
    }
    uint histClip = 0u;
    uint histSamples = 0u;
    if (lane == 0)
    {
        FA_T = tex2Dfetch(FA_HistStorage, int2(_FA_HIST_BINS, 0)).x;
        histClip = tex2Dfetch(FA_HistStorage, int2(_FA_HIST_BINS + 1, 0)).x;
        histSamples = tex2Dfetch(FA_HistStorage, int2(_FA_HIST_BINS + 2, 0)).x;
    }
    barrier();

    if (lane < _FA_HIST_BINS)
        tex2Dstore(FA_HistStorage, int2((int)lane, 0), 0u);
    if (lane < 3)
        tex2Dstore(FA_HistStorage, int2(_FA_HIST_BINS + (int)lane, 0), 0u);

    float excursion = 0.0;
    if (lane == 0)
    {
        FA_StateFail = 0;
        FA_UpdateHistRef = 1;

        excursion = tex2Dfetch(FA_HistPrevStorage, int2(_FA_HIST_BINS, 0)).r;
        if (!FA_Finite1(excursion)) excursion = 0.0;

        float e50 = _FA_LOG_MIN;
        float e90 = _FA_LOG_MIN;
        float e99 = _FA_LOG_MIN;
        if (FA_T > 0u)
            FA_HistPercentiles((float)FA_T, e50, e90, e99);

        float4 old0 = tex2Dfetch(FA_StateStorage, int2(0, 0));
        float4 old1 = tex2Dfetch(FA_StateStorage, int2(1, 0));
        float4 old2 = tex2Dfetch(FA_StateStorage, int2(2, 0));
        float frozenPrev = old2.x;
        if (!FA_Finite1(old0.x) || !FA_Finite1(old0.y) || !FA_Finite1(old0.z) || !FA_Finite1(old0.w) ||
            !FA_Finite1(old1.x) || !FA_Finite1(old1.y) || !FA_Finite1(old1.z) || !FA_Finite1(old1.w) ||
            !FA_Finite1(frozenPrev))
        {
            old0 = float4(0.0, 0.0, 0.50, 0.0);
            old1 = float4(0.0, 0.0, 0.0, 0.0);
            old2 = float4(0.0, -1.0, -1.0, -1.0);
            frozenPrev = 0.0;
        }
        float x = old0.x;
        float v = old0.y;
        float knee = old0.z;
        float cutCount = old0.w;
        float storedLambda = old1.x;
        float initialised = old1.y;
        float appliedAutoEV = clamp(old1.z, -_FA_AUTO_GAIN_LIMIT, _FA_AUTO_GAIN_LIMIT);
        float warmup = old1.w;
        if (initialised < 0.5) appliedAutoEV = 0.0;

        float darkGate = (FA_T >= 64u) ? saturate((e50 + 9.0) / 3.0) * saturate((float)FA_T / max((float)histSamples, 1.0)) : 0.0;
        bool gateOpen = darkGate > 0.0;
        bool adapt = !FreezeExposure && gateOpen;
        bool unfroze = (frozenPrev > 0.5) && !FreezeExposure;
        bool didResync = false;

        float eHi = e90 + clamp(e99 - e90, 0.0, _FA_KNEE_TAIL_MAX_EV);
        float kneeRaw = AutoHighlightKnee
            ? lerp(_FA_KNEE_MIN, _FA_KNEE_MAX, saturate((eHi - _FA_KNEE_E90_LO) / (_FA_KNEE_E90_HI - _FA_KNEE_E90_LO)))
            : HighlightKnee;

        bool coldStart = (FA_T > 0u && initialised < 0.5);

        if (coldStart)
        {
            x = e50;
            v = 0.0;
            knee = kneeRaw;
            warmup = 0.0;
            initialised = gateOpen ? 1.0 : 2.0;
        }
        else if (adapt && (initialised > 1.5 || unfroze))
        {
            x = e50;
            v = 0.0;
            cutCount = 0.0;
            initialised = 1.0;
            didResync = true;
        }

        if (AutoExposureStrength <= 0.0 || !gateOpen)
            storedLambda = 0.0;

        float D = 1.0;
        float drawRaw = 0.0;
        if (FA_T > 0u)
            FA_HistDistance(D, drawRaw);
        if (D > SceneChangeSensitivity) FA_UpdateHistRef = 0;
        if (didResync) FA_UpdateHistRef = 1;
        if (coldStart) FA_UpdateHistRef = 1;

        float totalRaw = frametime / 1000.0;
        bool stalled = totalRaw > 0.5;
        float total = clamp(totalRaw, 0.001, 0.5);
        int steps = (int)ceil(total / 0.0333);
        float dt = total / (float)steps;

        excursion = max(drawRaw, excursion * exp(-total / _FA_EXCURSION_DECAY));

        float cutUrgency = smoothstep(SceneChangeSensitivity, 2.0 * SceneChangeSensitivity, D);
        float adaptSpeed = 1.0 + 2.0 * cutUrgency;
        float rateCap = MaxChangeRate * adaptSpeed;
        float brightenTau = BrightenSpeed / adaptSpeed;
        float darkenTau = DarkenSpeed / adaptSpeed;
        float kneeTau = _FA_KNEE_TAU / adaptSpeed;
        float snapCap = _FA_CUT_SNAP_EV * (1.0 + cutUrgency);

        if (adapt && !stalled)
        {
            float whiteFraction = (histSamples > 0u) ? ((float)histClip / (float)histSamples) : 0.0;
            float f = 1.0 - smoothstep(ClipGuard * 0.01, 5.0 * ClipGuard * 0.01, whiteFraction);
            float baseLambda = (AutoExposureStrength / 100.0) * f * darkGate;

            for (int st = 0; st < steps; ++st)
            {
                float target = e50;
                if (abs(target - x) < _FA_DEADBAND_EV) target = x;

                float tau = (target > x) ? darkenTau : brightenTau;
                float omega = 1.0 / max(tau, 2.0 * dt);
                float acceleration = omega * omega * (target - x) - 2.0 * omega * v;
                v = clamp(v + acceleration * dt, -rateCap, rateCap);
                x += v * dt;

                if (D > SceneChangeSensitivity)
                    cutCount += dt;
                else
                    cutCount = 0.0;

                knee += (1.0 - exp(-dt / kneeTau)) * (kneeRaw - knee);

                warmup = min(warmup + dt, _FA_WARMUP_SECONDS);
                storedLambda = baseLambda * saturate(warmup / _FA_WARMUP_SECONDS);
            }
            if (cutCount >= _FA_SCENE_CUT_SECONDS)
            {
                x += clamp(e50 - x, -snapCap, snapCap);
                v = 0.0;
                cutCount = 0.0;
                FA_UpdateHistRef = 1;
            }
            initialised = 1.0;
        }
        else
        {
            if (!stalled)
                cutCount = 0.0;
            initialised = (initialised < 0.5) ? 0.0 : (gateOpen ? 1.0 : 2.0);
        }

        float eGrey = (OutputEncoding == 0) ? _FA_EGREY_SRGB : _FA_EGREY_GAMMA22;
        float xEff = x;
        float lagGate = 0.5 * SceneChangeSensitivity;
        if (excursion < lagGate)
        {
            float lagCap = _FA_LAG_CAP * (1.0 - excursion / lagGate);
            xEff = clamp(x, e50 - lagCap, e50 + lagCap);
        }
        float targetAutoEV = clamp(storedLambda * (eGrey - xEff), -_FA_AUTO_GAIN_LIMIT, _FA_AUTO_GAIN_LIMIT);

        float maxStepEV = rateCap * dt;
        if (!stalled && (AutoExposureStrength <= 0.0 || !FreezeExposure))
        {
            for (int st2 = 0; st2 < steps; ++st2)
                appliedAutoEV += clamp(targetAutoEV - appliedAutoEV, -maxStepEV, maxStepEV);
        }

        float gainEV = clamp(appliedAutoEV, -_FA_AUTO_GAIN_LIMIT, _FA_AUTO_GAIN_LIMIT)
                     + clamp(ExposureOffset, -_FA_GAIN_LIMIT, _FA_GAIN_LIMIT);
        gainEV = min(gainEV, _FA_LOG_MAX);

        float buildKnee = AutoHighlightKnee ? clamp(knee, _FA_KNEE_MIN, _FA_KNEE_MAX) : HighlightKnee;

        tex2Dstore(FA_StateStorage, int2(0, 0), float4(x, v, knee, cutCount));
        tex2Dstore(FA_StateStorage, int2(1, 0), float4(storedLambda, initialised, appliedAutoEV, warmup));

        float3 wbBaseGain = FA_ColorTempGain();
        if (AutoWhiteBalance) wbBaseGain = float3(1.0, 1.0, 1.0);
        tex2Dstore(FA_WBStorage, int2(0, 0), float4(wbBaseGain, 0.0));

        FA_StateGain = exp2(gainEV);
        FA_StateJoin = FA_ChooseKneeJoin(FA_StateGain, buildKnee);
    }
    barrier();

    if (lane < _FA_HIST_BINS && FA_UpdateHistRef != 0)
    {
        float norm = (FA_T != 0u) ? (float)FA_HistSh[lane] / (float)FA_T : 0.0;
        tex2Dstore(FA_HistPrevStorage, int2((int)lane, 0), float4(norm, 0.0, 0.0, 0.0));
    }
    if (lane == 0)
        tex2Dstore(FA_HistPrevStorage, int2(_FA_HIST_BINS, 0), float4(excursion, 0.0, 0.0, 0.0));

    for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
    {
        float u = _FA_LUT_DOMAIN * (float)i / (float)(_FA_LUT_SIZE - 1);
        FA_LutNat[i] = FA_Dn(FA_StateGain * u);
    }
    barrier();

    for (int attempt = 0; attempt < 4; ++attempt)
    {
        float buildY0, buildM0;
        FA_ShoulderTangents(FA_StateGain, FA_StateJoin, buildY0, buildM0);
        FA_FillLutSh(lane, FA_StateGain, FA_StateJoin, buildY0, buildM0);
        barrier();

        if (lane == 0)
        {
            FA_StateFail = FA_ValidateLut() ? 0 : 1;
            if (FA_StateFail != 0 && attempt < 3)
                FA_StateJoin = FA_ResolveKneeJoin(
                    max(_FA_U_B * 1.25, FA_StateJoin - 0.025), FA_StateGain);
        }
        barrier();
        if (FA_StateFail == 0) break;
    }

    for (int tier = 0; tier < 4 && FA_StateFail != 0; ++tier)
    {
        if (lane == 0)
            FA_StateJoin = 0.85 - 0.20 * (float)tier;
        barrier();
        float flatY0 = FA_BaseCurve(FA_StateJoin, FA_StateGain);
        FA_FillLutSh(lane, FA_StateGain, FA_StateJoin, flatY0, 0.0);
        barrier();
        if (lane == 0)
            FA_StateFail = FA_ValidateLut() ? 0 : 1;
        barrier();
    }

    if (FA_StateFail != 0)
    {
        if (lane == 0)
            FA_StateJoin = 1.0;
        barrier();
        for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
            FA_LutSh[i] = saturate(FA_LutNat[i]);
        barrier();
        if (lane == 0)
            FA_StateFail = FA_ValidateLut() ? 0 : 1;
        barrier();
    }

    if (FA_StateFail != 0)
    {
        if (lane == 0)
            FA_StateJoin = 1.0;
        barrier();
        for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
            FA_LutSh[i] = (float)i / (float)(_FA_LUT_SIZE - 1);
        barrier();
        if (lane == 0)
            FA_StateFail = FA_ValidateLut() ? 0 : 1;
        barrier();
    }

    for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
        tex2Dstore(FA_LUTStorage, int2((int)i, 0), float4(FA_LutSh[i], 0.0, 0.0, 0.0));

    if (lane == 0)
        tex2Dstore(FA_StateStorage, int2(2, 0),
                   float4(FreezeExposure ? 1.0 : 0.0, 0.0, 0.0, 0.0));
}

[numthreads(16, 16, 1)]
void FA_StatsCS(uint3 id : SV_DispatchThreadID, uint3 gid : SV_GroupID, uint3 tid : SV_GroupThreadID)
{
    if (OverallStrength <= 0.0) return;

    const uint lane = tid.y * 16 + tid.x;
    const bool doAwb = AutoWhiteBalance;

    float2 halfSize = 0.5 * float2((float)BUFFER_WIDTH, (float)BUFFER_HEIGHT);
    float invDiag2 = 1.0 / (halfSize.x * halfSize.x + halfSize.y * halfSize.y);
    int2 tileBase = int2(id.x * _FA_AWB_TILE, id.y * _FA_AWB_TILE);

    uint localIndex = lane;
    FA_P1Bins[localIndex] = 0u;
    if (localIndex == 0) { FA_P1Valid = 0u; FA_P1White = 0u; FA_P1Samples = 0u; }
    barrier();

    const float minLin = exp2(_FA_LOG_MIN);
    const int T = _FA_AWB_TILE;

    float4 acc0 = float4(0.0, 0.0, 0.0, 0.0);
    float4 acc1 = float4(0.0, 0.0, 0.0, 0.0);
    float4 acc2 = float4(0.0, 0.0, 0.0, 0.0);
    float4 acc3 = float4(0.0, 0.0, 0.0, 0.0);
    float4 acc4 = float4(0.0, 0.0, 0.0, 0.0);

    float3 rowC[T + 1];
    float  rowW[T + 1];
    bool   rowV[T + 1];
    float3 prevC[T + 1];
    float  prevW[T + 1];
    bool   prevV[T + 1];

    [loop]
    for (int sj = 0; sj <= T; ++sj)
    {
        [loop]
        for (int si = 0; si <= T; ++si)
        {
            int2 samplePos = tileBase + int2(si, sj);
            float3 c = float3(0.0, 0.0, 0.0);
            float w = 0.0;
            bool valid = false;
            if (samplePos.x < BUFFER_WIDTH && samplePos.y < BUFFER_HEIGHT)
            {
                c = FA_Sanitize(FA_Decode(tex2Dfetch(FA_BackBufferSampler, samplePos).rgb));
                float2 offset = float2(samplePos) + 0.5 - halfSize;
                w = saturate(1.0 - _FA_HIST_WEIGHT_FALLOFF * dot(offset, offset) * invDiag2);
                float Y = dot(c, FA_LUMA);
                valid = (Y > _FA_AWB_DARK_MIN) && (max(c.r, max(c.g, c.b)) < _FA_AWB_CLIP_MAX);

                bool interior = (si < T) && (sj < T);
                if (interior)
                {
                    uint sampleWeight = (uint)(w * _FA_HIST_WEIGHT_SCALE + 0.5);
                    atomicAdd(FA_P1Samples, sampleWeight);
                    if (max(c.r, max(c.g, c.b)) > 0.0)
                    {
                        int bin = clamp((int)floor((log2(max(Y, minLin)) - _FA_LOG_MIN) * ((float)_FA_HIST_BINS / _FA_LOG_RANGE)), 0, _FA_HIST_BINS - 1);
                        atomicAdd(FA_P1Bins[bin], sampleWeight);
                        atomicAdd(FA_P1Valid, sampleWeight);
                        if (min(c.r, min(c.g, c.b)) >= _FA_WHITE_THRESHOLD) atomicAdd(FA_P1White, sampleWeight);
                    }

                    if (doAwb)
                    {
                        if (valid)
                        {
                            float3 cc = c;
                            float ccMax = max(cc.r, max(cc.g, cc.b));
                            if (ccMax > _FA_AWB_E1_CAP)
                                cc *= _FA_AWB_E1_CAP / ccMax;
                            float c3r = cc.r * cc.r * cc.r;
                            float c3g = cc.g * cc.g * cc.g;
                            float c3b = cc.b * cc.b * cc.b;
                            float invSum = 1.0 / max(c.r + c.g + c.b, 1.0e-6);
                            float rn = c.r * invSum;
                            float bn = c.b * invSum;

                            acc0 += w * float4(1.0, c3r, c3g, c3b);
                            acc3 += w * float4(0.0, rn, rn * rn, bn);
                            acc4 += w * float4(bn * bn, Y, Y * Y, 0.0);
                            if (Y >= _FA_AWB_BRIGHT_MIN)
                            {
                                float cMaxB = max(c.r, max(c.g, c.b));
                                float nu = min(c.r, min(c.g, c.b)) / max(cMaxB, 1.0e-6);
                                acc1 += w * nu * nu * float4(c.r, c.g, c.b, 1.0);
                            }
                        }
                        acc4.w += w;
                    }
                }
            }
            rowC[si] = c;
            rowW[si] = w;
            rowV[si] = valid;
        }

        if (doAwb)
        {
            if (sj < T)
            {
                [loop]
                for (int ei = 1; ei <= T; ++ei)
                {
                    if (rowV[ei] && rowV[ei - 1])
                    {
                        float3 d = abs(rowC[ei] - rowC[ei - 1]);
                        if (max(d.r, max(d.g, d.b)) >= _FA_AWB_EDGE_MIN)
                        {
                            float ew = 0.5 * (rowW[ei] + rowW[ei - 1]);
                            acc2 += ew * float4(d.r, d.g, d.b, 1.0);
                            acc3.x += ew * abs(dot(d, FA_LUMA));
                        }
                    }
                }
            }
            if (sj > 0)
            {
                [loop]
                for (int vi = 0; vi < T; ++vi)
                {
                    if (rowV[vi] && prevV[vi])
                    {
                        float3 d = abs(rowC[vi] - prevC[vi]);
                        if (max(d.r, max(d.g, d.b)) >= _FA_AWB_EDGE_MIN)
                        {
                            float ew = 0.5 * (rowW[vi] + prevW[vi]);
                            acc2 += ew * float4(d.r, d.g, d.b, 1.0);
                            acc3.x += ew * abs(dot(d, FA_LUMA));
                        }
                    }
                }
            }
        }

        [loop]
        for (int ci = 0; ci <= T; ++ci)
        {
            prevC[ci] = rowC[ci];
            prevW[ci] = rowW[ci];
            prevV[ci] = rowV[ci];
        }
    }

    barrier();

    uint count = FA_P1Bins[localIndex];
    if (count != 0u)
        atomicAdd(FA_HistStorage, int2((int)localIndex, 0), count);
    if (localIndex == 0)
    {
        if (FA_P1Valid != 0u) atomicAdd(FA_HistStorage, int2(_FA_HIST_BINS, 0), FA_P1Valid);
        if (FA_P1White != 0u) atomicAdd(FA_HistStorage, int2(_FA_HIST_BINS + 1, 0), FA_P1White);
        if (FA_P1Samples != 0u) atomicAdd(FA_HistStorage, int2(_FA_HIST_BINS + 2, 0), FA_P1Samples);
    }

    if (doAwb)
    {
        FA_AwbRed[lane] = acc0;
        FA_AwbRed[256 + lane] = acc1;
        FA_AwbRed[512 + lane] = acc2;
        FA_AwbRed[768 + lane] = acc3;
        FA_AwbRed[1024 + lane] = acc4;

        barrier();

        [unroll]
        for (uint s = 128u; s > 0u; s >>= 1)
        {
            if (lane < s)
            {
                FA_AwbRed[lane] += FA_AwbRed[lane + s];
                FA_AwbRed[256 + lane] += FA_AwbRed[256 + lane + s];
                FA_AwbRed[512 + lane] += FA_AwbRed[512 + lane + s];
                FA_AwbRed[768 + lane] += FA_AwbRed[768 + lane + s];
                FA_AwbRed[1024 + lane] += FA_AwbRed[1024 + lane + s];
            }
            barrier();
        }

        if (lane == 0)
        {
            int2 storeBase = int2((int)(gid.x * 5u), (int)gid.y);
            tex2Dstore(FA_AwbGroupsStorage, storeBase + int2(0, 0), FA_AwbRed[0]);
            tex2Dstore(FA_AwbGroupsStorage, storeBase + int2(1, 0), FA_AwbRed[256]);
            tex2Dstore(FA_AwbGroupsStorage, storeBase + int2(2, 0), FA_AwbRed[512]);
            tex2Dstore(FA_AwbGroupsStorage, storeBase + int2(3, 0), FA_AwbRed[768]);
            tex2Dstore(FA_AwbGroupsStorage, storeBase + int2(4, 0), FA_AwbRed[1024]);
        }
    }
}

[numthreads(256, 1, 1)]
void FA_AwbStateCS(uint3 tid : SV_GroupThreadID)
{
    const uint lane = tid.x;

    if (OverallStrength <= 0.0 || !AutoWhiteBalance)
    {
        if (lane < 4)
            tex2Dstore(FA_AwbStateStorage, int2((int)lane, 0), float4(0.0, 0.0, 0.0, 0.0));
        return;
    }

    const uint awbGX = (uint)_FA_AWB_GX;
    const uint awbGY = (uint)_FA_AWB_GY;
    const uint groupCount = awbGX * awbGY;

    float4 a0 = float4(0.0, 0.0, 0.0, 0.0);
    float4 a1 = float4(0.0, 0.0, 0.0, 0.0);
    float4 a2 = float4(0.0, 0.0, 0.0, 0.0);
    float4 a3 = float4(0.0, 0.0, 0.0, 0.0);
    float4 a4 = float4(0.0, 0.0, 0.0, 0.0);
    for (uint g = lane; g < groupCount; g += 256u)
    {
        uint gx = g % awbGX;
        uint gy = g / awbGX;
        int2 base = int2((int)(gx * 5u), (int)gy);
        a0 += tex2Dfetch(FA_AwbGroupsStorage, base);
        a1 += tex2Dfetch(FA_AwbGroupsStorage, base + int2(1, 0));
        a2 += tex2Dfetch(FA_AwbGroupsStorage, base + int2(2, 0));
        a3 += tex2Dfetch(FA_AwbGroupsStorage, base + int2(3, 0));
        a4 += tex2Dfetch(FA_AwbGroupsStorage, base + int2(4, 0));
    }

    FA_AwbRed[lane] = a0;
    FA_AwbRed[256 + lane] = a1;
    FA_AwbRed[512 + lane] = a2;
    FA_AwbRed[768 + lane] = a3;
    FA_AwbRed[1024 + lane] = a4;

    barrier();

    [unroll]
    for (uint s = 128u; s > 0u; s >>= 1)
    {
        if (lane < s)
        {
            FA_AwbRed[lane] += FA_AwbRed[lane + s];
            FA_AwbRed[256 + lane] += FA_AwbRed[256 + lane + s];
            FA_AwbRed[512 + lane] += FA_AwbRed[512 + lane + s];
            FA_AwbRed[768 + lane] += FA_AwbRed[768 + lane + s];
            FA_AwbRed[1024 + lane] += FA_AwbRed[1024 + lane + s];
        }
        barrier();
    }

    if (lane == 0)
    {
        float4 A0 = FA_AwbRed[0];
        float4 A1 = FA_AwbRed[256];
        float4 A2 = FA_AwbRed[512];
        float4 A3 = FA_AwbRed[768];
        float4 A4 = FA_AwbRed[1024];

        float Nw = A0.x;
        float sampledWeight = A4.w;
        float validFraction = Nw / max(sampledWeight, 1.0e-6);
        bool haveScene = (Nw >= 64.0) && (validFraction >= 0.05);

        float meanY = A4.y / max(Nw, 1.0e-6);
        float meanRn = A3.y / max(Nw, 1.0e-6);
        float meanBn = A3.w / max(Nw, 1.0e-6);
        float varRn = max(A3.z / max(Nw, 1.0e-6) - meanRn * meanRn, 0.0);
        float varBn = max(A4.x / max(Nw, 1.0e-6) - meanBn * meanBn, 0.0);
        float stdC = sqrt(varRn + varBn);

        float meanChroma = length(float2(meanRn - (1.0 / 3.0), meanBn - (1.0 / 3.0)));
        float chromaRatio = meanChroma / max(stdC, 0.01);
        float dominancePenalty = 1.0 - 0.65 * smoothstep(2.0, 4.0, chromaRatio);
        float bimodalPenalty = lerp(0.35, 1.0, saturate(chromaRatio / 0.6));

        float countTerm = smoothstep(64.0, 256.0, Nw) * smoothstep(0.10, 0.35, validFraction);
        float exposureTerm = smoothstep(0.004, 0.02, meanY) * (1.0 - smoothstep(0.55, 0.85, meanY));
        float edgePresence = smoothstep(16.0, 64.0, A2.w);
        float diversityTerm = smoothstep(0.008, 0.045, stdC) * edgePresence;

        float3 e1 = float3(0.0, 0.0, 0.0);
        float conf1 = 0.0;
        if (min(A0.y, min(A0.z, A0.w)) > 0.0)
        {
            e1 = FA_AwbNormLuma(pow(max(float3(A0.y, A0.z, A0.w), float3(0.0, 0.0, 0.0)), 1.0 / 3.0));
            conf1 = FA_AwbPlausibility(e1) * countTerm
                  * exposureTerm * lerp(0.15, 1.0, diversityTerm)
                  * dominancePenalty * bimodalPenalty;
        }

        float3 e2 = float3(0.0, 0.0, 0.0);
        float conf2 = 0.0;
        if (A1.w >= 16.0)
        {
            e2 = FA_AwbNormLuma(A1.xyz / A1.w);
            conf2 = FA_AwbPlausibility(e2)
                  * smoothstep(0.01, 0.06, A1.w / max(Nw, 1.0e-6))
                  * smoothstep(16.0, 64.0, A1.w);
        }

        float3 e3 = float3(0.0, 0.0, 0.0);
        float conf3 = 0.0;
        if (A2.w >= 16.0)
        {
            float meanEdge = A3.x / A2.w;
            e3 = FA_AwbNormLuma(A2.xyz / A2.w);
            conf3 = FA_AwbPlausibility(e3)
                  * smoothstep(0.005, 0.04, A2.w / max(Nw, 1.0e-6))
                  * smoothstep(16.0, 64.0, A2.w)
                  * smoothstep(0.002, 0.015, meanEdge)
                  * (1.0 - smoothstep(0.8, 1.6, meanEdge))
                  * exposureTerm;
        }

        float3 fused = float3(0.0, 0.0, 0.0);
        float fusedConf = 0.0;
        float totalBase = conf1 + conf2 + conf3;
        if (totalBase > 1.0e-4)
        {
            float3 c1 = FA_AwbCorrectionLog(e1);
            float3 c2 = FA_AwbCorrectionLog(e2);
            float3 c3 = FA_AwbCorrectionLog(e3);
            fused = (conf1 * c1 + conf2 * c2 + conf3 * c3) / totalBase;

            float spread = (conf1 * dot(c1 - fused, c1 - fused)
                          + conf2 * dot(c2 - fused, c2 - fused)
                          + conf3 * dot(c3 - fused, c3 - fused)) / totalBase;
            float agreement = exp(-spread / (_FA_AWB_AGREEMENT_SIGMA * _FA_AWB_AGREEMENT_SIGMA));

            float top2 = max(min(conf1, conf2), max(min(conf1, conf3), min(conf2, conf3)));

            float plausFused = FA_AwbPlausibility(FA_AwbNormLuma(exp(-fused)));
            float flatGate = smoothstep(0.002, 0.012, stdC) * smoothstep(16.0, 64.0, A2.w);
            fusedConf = saturate(top2 * 2.0) * agreement * plausFused * flatGate;

            fused = clamp(fused, -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);
        }

        float4 s0 = tex2Dfetch(FA_AwbStateStorage, int2(0, 0));
        float4 s1 = tex2Dfetch(FA_AwbStateStorage, int2(1, 0));
        float4 s2 = tex2Dfetch(FA_AwbStateStorage, int2(2, 0));
        float4 s3 = tex2Dfetch(FA_AwbStateStorage, int2(3, 0));
        if (!FA_Finite1(s0.x) || !FA_Finite1(s0.y) || !FA_Finite1(s0.z) || !FA_Finite1(s0.w) ||
            !FA_Finite1(s1.x) || !FA_Finite1(s1.y) || !FA_Finite1(s1.z) || !FA_Finite1(s1.w) ||
            !FA_Finite1(s2.x) || !FA_Finite1(s2.y) || !FA_Finite1(s2.z) ||
            !FA_Finite1(s3.x) || !FA_Finite1(s3.z) || abs(s2.w - 1.0) > 0.01)
        {
            s0 = float4(0.0, 0.0, 0.0, 0.0);
            s1 = float4(0.0, 0.0, 0.0, 0.0);
            s2 = float4(0.0, 0.0, 0.0, 0.0);
            s3 = float4(0.0, 0.0, 0.0, 0.0);
        }

        float total = clamp(frametime * 0.001, 0.001, 0.5);
        int steps = (int)ceil(total / 0.0333);
        float sdt = total / (float)steps;

        float meanYPrev = s1.y;
        float meanRnPrev = s1.z;
        float meanBnPrev = s1.w;
        bool sceneCut = false;
        if (haveScene && s2.w > 0.5)
        {
            float lumaJump = abs(meanY - meanYPrev) / max(max(meanY, meanYPrev), 0.02);
            float chromaJump = abs(meanRn - meanRnPrev) + abs(meanBn - meanBnPrev);
            sceneCut = (lumaJump > 0.45) || (chromaJump > _FA_AWB_CUT_CHROMA);
        }

        float3 cur = s0.xyz;
        float smoothedConf = s0.w;
        float uncertain = s1.x;
        float3 tgt = s2.xyz;
        float recentCut = sceneCut ? 1.0 : s3.x * exp(-total / 0.5);
        bool wasConfident = s3.y > 0.5;

        smoothedConf = lerp(smoothedConf, fusedConf, 1.0 - exp(-total / 0.4));
        float confGate = wasConfident ? _FA_AWB_CONF_EXIT : _FA_AWB_CONF_ENTER;
        bool confident = haveScene && (fusedConf > 0.0) && (smoothedConf >= confGate);

        if (confident)
        {
            tgt = lerp(tgt, fused, 1.0 - exp(-total / _FA_AWB_TARGET_TAU));
            uncertain = 0.0;
        }
        else
        {
            uncertain += total;
            if (sceneCut)
                uncertain = max(uncertain, _FA_AWB_UNCERTAIN_HOLD + 1.0e-3);
        }

        tgt -= dot(tgt, FA_LUMA);
        tgt = clamp(tgt, -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);
        tgt -= dot(tgt, FA_LUMA);
        tgt = clamp(tgt, -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);

        float cutBoost = confident ? recentCut : 0.0;
        float tau = lerp(_FA_AWB_TAU, _FA_AWB_CUT_TAU, cutBoost);
        float cap = lerp(_FA_AWB_MAX_RATE, _FA_AWB_CUT_RATE, cutBoost);
        if (s2.w < 0.5) cur = float3(0.0, 0.0, 0.0);

        [loop]
        for (int st = 0; st < steps; ++st)
        {
            if (uncertain > _FA_AWB_UNCERTAIN_HOLD)
                tgt *= exp(-sdt * _FA_AWB_RELAX_RATE);
            float3 delta = tgt - cur;
            float maxStep = cap * sdt;
            cur += clamp(delta * (sdt / max(tau, sdt)), -maxStep, maxStep);
            cur -= dot(cur, FA_LUMA);
        }
        cur = clamp(cur, -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);
        cur -= dot(cur, FA_LUMA);
        cur = clamp(cur, -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);

        float strengthSm = s3.z;
        float strengthTarget = AutoWhiteBalanceStrength / 100.0;
        strengthSm += (strengthTarget - strengthSm) * (1.0 - exp(-total / _FA_AWB_STRENGTH_TAU));

        float3 applied = clamp(cur * strengthSm,
                               -_FA_AWB_GAIN_LIMIT_LOG, _FA_AWB_GAIN_LIMIT_LOG);
        float3 targetWhite = exp(-applied);

        float u0 = clamp((haveScene ? meanY : 0.18), 0.01, 0.95);
        float3 greyPost = FA_AwbCurvedGrey(targetWhite * u0);
        float greyPostLuma = dot(greyPost, FA_LUMA);
        float3 baseWhite = (FA_Finite1(greyPostLuma) && greyPostLuma > 1.0e-7)
                         ? (greyPost / greyPostLuma)
                         : targetWhite;
        float3 lmsEstimate = mul(FA_RGB_TO_LMS, baseWhite);
        float3 awbGain = clamp(1.0 / max(lmsEstimate, float3(1.0e-4, 1.0e-4, 1.0e-4)),
                               0.5, 2.0);

        tex2Dstore(FA_WBStorage, int2(0, 0), float4(awbGain, 0.0));
        tex2Dstore(FA_AwbStateStorage, int2(0, 0), float4(cur, smoothedConf));
        tex2Dstore(FA_AwbStateStorage, int2(1, 0),
                   float4(uncertain,
                          haveScene ? meanY : meanYPrev,
                          haveScene ? meanRn : meanRnPrev,
                          haveScene ? meanBn : meanBnPrev));
        tex2Dstore(FA_AwbStateStorage, int2(2, 0), float4(tgt, 1.0));
        tex2Dstore(FA_AwbStateStorage, int2(3, 0),
                   float4(recentCut, confident ? 1.0 : 0.0, strengthSm, 0.0));
    }
}

[numthreads(8, 8, 1)]
void FA_HueCS(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= BUFFER_WIDTH || id.y >= BUFFER_HEIGHT)
        return;

    if (OverallStrength <= 0.0)
    {
        tex2Dstore(FA_BStorage, int2(id.xy), float4(0.0, 0.0, 0.0, 0.0));
        return;
    }

    float4 source = tex2Dfetch(FA_BackBufferSampler, int2(id.xy));
    float3 src = FA_Sanitize(FA_Decode(source.rgb));

    float3 w = FA_Inset(float3(1.0, 1.0, 1.0));
    float3 x3 = (FA_Inset(src) / w) * ((float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN);
    float3 curved = clamp(max(FA_Outset(float3(FA_LUTFetch(x3.r), FA_LUTFetch(x3.g), FA_LUTFetch(x3.b)) * w), 0.0), 0.0, 1.0);

    float3 inLab = FA_OklabFromLinear(src);
    float3 lab = FA_OklabFromLinear(curved);

    float inputChroma = length(inLab.yz);
    float hIn = (inputChroma < _FA_EPS_LUMA) ? 0.0 : atan2(inLab.z, inLab.y);

    float theta = 0.0;
    float2 ab = 0.0;
    if (inputChroma >= _FA_EPS_LUMA)
    {
        float curvedChroma = length(lab.yz);
        float inputRelativeChroma = inputChroma / max(inLab.x, _FA_EPS_LUMA);
        float curvedRelativeChroma = curvedChroma / max(lab.x, _FA_EPS_LUMA);
        float saturationRatio = curvedRelativeChroma / max(inputRelativeChroma, _FA_EPS_LUMA);
        float chromaScale = min(1.0, min(saturationRatio, 1.0) / max(saturationRatio, _FA_EPS_RATIO));

        lab.yz *= chromaScale;
        curvedChroma *= chromaScale;

        float h = (curvedChroma < _FA_EPS_LUMA) ? 0.0 : atan2(lab.z, lab.y);
        float delta = FA_WrapAngle(hIn - h);
        float hueWeight = smoothstep(0.0, 0.01, inputChroma)
                        * smoothstep(0.002, 0.012, inputRelativeChroma);
        theta = delta * (HueRestoration / 100.0) * hueWeight;
        ab = lab.yz;
    }

    float cs = cos(theta), sn = sin(theta);
    float3 restored = FA_LinearFromOklab(float3(lab.x, ab.x * cs - ab.y * sn, ab.x * sn + ab.y * cs));

    float3 wbGain = tex2Dfetch(FA_WBSampler, int2(0, 0)).rgb;
    float3 balanced = FA_WhiteBalance(restored, wbGain);
    if (AutoWhiteBalance)
    {
        float3 rollUp = 1.0 - smoothstep(0.80, 0.97, balanced);
        float3 rollDown = smoothstep(0.0, 0.02, restored);
        float3 roll = lerp(rollDown, rollUp, step(restored, balanced));
        balanced = restored + (balanced - restored) * roll;
    }
    tex2Dstore(FA_BStorage, int2(id.xy), float4(balanced, source.a));
}

float FA_Fp16QuantStep(float c)
{
    c = clamp(c, 0.0, 1.0);
    float e = floor(log2(max(c, 1.0e-8)));
    return clamp(exp2(e - 10.0), 5.9604645e-8, 9.765625e-4);
}

float4 FA_OutputPS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    float4 originalEncoded = tex2D(FA_BackBufferSampler, texcoord);
    if (OverallStrength <= 0.0)
        return originalEncoded;

    float3 orig = FA_Sanitize(FA_Decode(originalEncoded.rgb));
    float3 curved = tex2D(FA_BSampler, texcoord).rgb;
    float3 lab = FA_OklabFromLinear(curved);

    float L = clamp(lab.x, 0.0, 1.0);
    float C = length(lab.yz);

    float3 outLinear;
    if (C > _FA_EPS_RATIO)
    {
        float h = atan2(lab.z, lab.y);
        float ch = cos(h), sh = sin(h);
        float Cmax = FA_GamutMaxChroma(L, ch, sh);
        float x = C / max(Cmax, _FA_EPS_RATIO);
        float Cp = FA_CompressiveRolloff(x, GamutRolloffStart) * Cmax;

        outLinear = clamp(FA_LinearFromOklab(float3(L, Cp * ch, Cp * sh)), 0.0, 1.0);
    }
    else
    {
        float grey = L * L * L;
        outLinear = float3(grey, grey, grey);
    }

    float3 finalLinear = lerp(orig, outLinear, OverallStrength / 100.0);

    float3 encoded = FA_Encode(clamp(finalLinear, 0.0, 1.0));
    if (Dithering)
    {
        float2 pixel = floor(position.xy);
        float noise = FA_IGN(pixel.x, pixel.y)
                    + FA_IGN(pixel.x + 5.588238, pixel.y + 3.117432) - 1.0;
#if BUFFER_COLOR_BIT_DEPTH == 10
        float3 ditherAmp = float3(1.0 / 1023.0, 1.0 / 1023.0, 1.0 / 1023.0);
#elif BUFFER_COLOR_BIT_DEPTH == 16
        float3 ditherAmp = float3(FA_Fp16QuantStep(encoded.r),
                                  FA_Fp16QuantStep(encoded.g),
                                  FA_Fp16QuantStep(encoded.b));
#else
        float3 ditherAmp = float3(1.0 / 255.0, 1.0 / 255.0, 1.0 / 255.0);
#endif
        float3 taperLo = smoothstep(float3(0.0, 0.0, 0.0), ditherAmp, encoded);
        float3 taperHi = float3(1.0, 1.0, 1.0)
                       - smoothstep(float3(1.0, 1.0, 1.0) - ditherAmp, float3(1.0, 1.0, 1.0), encoded);
        encoded += noise.xxx * ditherAmp * taperLo * taperHi;
    }
    encoded = clamp(encoded, 0.0, 1.0);
    return float4(encoded, originalEncoded.a);
}

technique FlexAgX
{
    pass FlexAgX_StatsPass
    {
        ComputeShader = FA_StatsCS;
        DispatchSizeX = (BUFFER_WIDTH + 127) / 128;
        DispatchSizeY = (BUFFER_HEIGHT + 127) / 128;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_StatePass
    {
        ComputeShader = FA_StateCS;
        DispatchSizeX = 1;
        DispatchSizeY = 1;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_AwbStatePass
    {
        ComputeShader = FA_AwbStateCS;
        DispatchSizeX = 1;
        DispatchSizeY = 1;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_HuePass
    {
        ComputeShader = FA_HueCS;
        DispatchSizeX = (BUFFER_WIDTH + 7) / 8;
        DispatchSizeY = (BUFFER_HEIGHT + 7) / 8;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_OutputPass
    {
        VertexShader = FA_FullscreenVS;
        PixelShader = FA_OutputPS;
        VertexCount = 3;
    }
}

#endif
