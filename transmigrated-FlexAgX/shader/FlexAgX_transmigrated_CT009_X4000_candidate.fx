#if __RESHADE__ < 50900
#error FlexAgX requires ReShade 5.9.0 or newer (storage images with tex2Dfetch reads).
#endif

// Renderer guard: rejects D3D9 (0x9000+), D3D10 (0xA000+) and OpenGL < 4.3.
// OpenGL renderer codes are 0x10000 + major * 0x1000 + minor * 0x100, so
// OpenGL 4.3 is 0x14300 and the GL 4.3 minimum is enforced here. Vulkan is
// 0x20000+, D3D11 0xB000+, D3D12 0xC000+.
#if __RENDERER__ < 0xb000 || (__RENDERER__ >= 0x10000 && __RENDERER__ < 0x14300)
#error FlexAgX requires D3D11, D3D12, OpenGL 4.3 or Vulkan.
#endif

// -----------------------------------------------------------------------------
// User interface. Declaration order defines category/control order in ReShade.
// -----------------------------------------------------------------------------

uniform float OverallStrength <
    ui_category = "Main";
    ui_label = "Overall Strength";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_tooltip = "How strongly FlexAgX changes the image. 0% turns it off.";
> = 100.0;

uniform int DebugView <
    ui_category = "Main";
    ui_label = "Debug View";
    ui_type = "combo";
    ui_items = "Off\0Clipping Warning\0Exposure Gain\0";
    ui_tooltip = "Shows where the game's own output is already blown out white before FlexAgX runs, or how much brightness FlexAgX is adding. Keep Off for normal play.";
> = 0;

uniform float AutoExposureStrength <
    ui_category = "Brightness";
    ui_label = "Auto Exposure Strength";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_tooltip = "How much automatic exposure adapts to the scene. 0% disables the automatic exposure contribution; manual Exposure Offset still applies.";
> = 30.0;

uniform float ExposureOffset <
    ui_category = "Brightness";
    ui_label = "Exposure Offset";
    ui_type = "slider";
    ui_min = -2.0; ui_max = 2.0; ui_step = 0.1;
    ui_tooltip = "Brightens or darkens everything, like a camera's exposure dial. One step doubles the light. Applied on top of auto exposure at every strength.";
> = 0.0;

uniform bool FreezeExposure <
    ui_category = "Brightness";
    ui_label = "Freeze Exposure";
    ui_tooltip = "Locks the automatic brightness adaptation. Exposure Offset always applies; Highlight Knee applies only while Auto Highlight Knee is off.";
> = false;

uniform float BrightenSpeed <
    ui_category = "Adaptation";
    ui_category_closed = true;
    ui_label = "Brighten Speed";
    ui_type = "slider";
    ui_min = 0.10; ui_max = 3.00; ui_step = 0.05;
    ui_tooltip = "How quickly the image gets brighter. Lower is faster.";
> = 0.60;

uniform float DarkenSpeed <
    ui_category = "Adaptation";
    ui_label = "Darken Speed";
    ui_type = "slider";
    ui_min = 0.10; ui_max = 5.00; ui_step = 0.05;
    ui_tooltip = "How quickly the image gets darker. Lower is faster.";
> = 1.20;

uniform float MaxChangeRate <
    ui_category = "Adaptation";
    ui_label = "Max Change Rate";
    ui_type = "slider";
    ui_min = 0.5; ui_max = 6.0; ui_step = 0.1;
    ui_tooltip = "Limits how quickly automatic exposure changes in EV per second. Manual Exposure Offset remains immediate.";
> = 3.0;

uniform float SceneChangeSensitivity <
    ui_category = "Adaptation";
    ui_label = "Scene Change Sensitivity";
    ui_type = "slider";
    ui_min = 0.10; ui_max = 0.60; ui_step = 0.01;
    ui_tooltip = "How different a new scene must look before brightness resets quickly. Higher means fewer resets.";
> = 0.35;

uniform float Deadband <
    ui_category = "Adaptation";
    ui_label = "Deadband";
    ui_type = "slider";
    ui_min = 0.00; ui_max = 0.10; ui_step = 0.01;
    ui_tooltip = "Ignores tiny brightness wobbles so the image does not shimmer.";
> = 0.04;

uniform float ClipGuard <
    ui_category = "Adaptation";
    ui_label = "Clip Guard";
    ui_type = "slider";
    ui_min = 0.5; ui_max = 5.0; ui_step = 0.1;
    ui_tooltip = "Percent of all in-bounds sampled pixels classified as white above which auto exposure ramps down to zero.";
> = 2.0;

uniform bool AutoHighlightKnee <
    ui_category = "Highlights and Shadows";
    ui_label = "Auto Highlight Knee";
    ui_tooltip = "Automatically picks where bright areas begin to be lifted.";
> = true;

uniform float HighlightKnee <
    ui_category = "Highlights and Shadows";
    ui_label = "Highlight Knee";
    ui_type = "slider";
    ui_min = 0.40; ui_max = 0.55; ui_step = 0.01;
    ui_tooltip = "Where bright areas start to be lifted. Lower affects more of the image. Used only when Auto is off.";
> = 0.50;

uniform float ShadowPreservation <
    ui_category = "Highlights and Shadows";
    ui_label = "Shadow Preservation";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_tooltip = "Keeps dark areas from turning muddy black. 0% gives the plain AgX look.";
> = 50.0;

uniform float HueRestoration <
    ui_category = "Color";
    ui_label = "Hue Restoration";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 100.0; ui_step = 1.0;
    ui_tooltip = "Keeps colors from drifting in hue when they get bright.";
> = 100.0;

uniform float GamutRolloffStart <
    ui_category = "Color";
    ui_label = "Gamut Roll-off Start";
    ui_type = "slider";
    ui_min = 0.60; ui_max = 0.95; ui_step = 0.01;
    ui_tooltip = "How early very vivid colors start softening to fit the screen. Lower softens more.";
> = 0.80;

uniform float ColorTemp <
    ui_category = "Color";
    ui_label = "Color Temperature";
    ui_type = "slider";
    ui_min = 2000.0; ui_max = 12000.0; ui_step = 50.0;
    ui_tooltip = "Shifts the white point along the blackbody curve using von Kries adaptation in Oklab's LMS space. 6500 K is exactly neutral; lower is warmer, higher is cooler.";
> = 6500.0;

uniform float LocalDetail <
    ui_category = "Detail";
    ui_label = "Local Detail";
    ui_type = "slider";
    ui_min = 0.0; ui_max = 50.0; ui_step = 1.0;
    ui_tooltip = "Adds back fine contrast that brightness changes can flatten. Too much looks crunchy.";
> = 20.0;

uniform int InputEncoding <
    ui_category = "Input and Output";
    ui_label = "Input Encoding";
    ui_type = "combo";
    ui_items = "sRGB\0Gamma 2.2\0";
    ui_tooltip = "The brightness curve the game uses to store its colors. Most games use sRGB.";
> = 0;

uniform int OutputEncoding <
    ui_category = "Input and Output";
    ui_label = "Output Encoding";
    ui_type = "combo";
    ui_items = "sRGB\0Gamma 2.2\0";
    ui_tooltip = "The brightness curve your monitor expects. Keep sRGB unless you know yours differs.";
> = 0;

uniform bool Dithering <
    ui_category = "Input and Output";
    ui_label = "Dithering";
    ui_tooltip = "Adds invisible noise so smooth gradients do not show color bands.";
> = true;

// ReShade-provided inputs. frametime is milliseconds; framecount is frame index.
uniform float frametime < source = "frametime"; >;
uniform int framecount < source = "framecount"; >;

// -----------------------------------------------------------------------------
// Constants and resources. No texture uses pooled=true.
// -----------------------------------------------------------------------------
#define _FA_LOG_MIN (-12.47393)
#define _FA_LOG_MAX (4.026069)
#define _FA_LOG_RANGE (16.499999)
#define _FA_DISPLAY_GAMMA (2.4)
#define _FA_GREY (0.18)
#define _FA_KNEE_MIN (0.40)
#define _FA_KNEE_MAX (0.55)
#define _FA_KNEE_TAU (0.6)
#define _FA_U_B (0.05126)
#define _FA_LUT_SIZE (1024)
#define _FA_LUT_DOMAIN (1.1)
#define _FA_GAIN_LIMIT (2.0)
#define _FA_SCENE_CUT_SECONDS (0.10)
#define _FA_WHITE_THRESHOLD (0.98)
#define _FA_GAMUT_P (1.2)
#define _FA_DETAIL_EPS (0.001)
#define _FA_DETAIL_RATIO_MAX (4.0)
#define _FA_WARMUP_SECONDS (0.5)
#define _FA_PI (3.14159265358979323846)
#define _FA_TWO_PI (6.28318530717958647692)

static const float3 FA_LUMA = float3(0.2126, 0.7152, 0.0722);

texture2D FA_BackBuffer : COLOR;
sampler2D FA_BackBufferSampler
{
    Texture = FA_BackBuffer;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
    SRGBTexture = false;
};

// NOTE: A component type specification (<uint>) is only valid on sampler/storage
// objects, not on texture declarations. The type is implied by Format = R32U and
// carried by the typed storage2D<uint> below. Reading storage objects via
// tex2Dfetch requires a recent ReShade runtime (5.9+); all storage reads here
// use R32-family formats, which are core D3D11 UAV-load formats. The version
// guard at the top of this file enforces the ReShade 5.9+ requirement.
texture2D FA_Hist
{
    Width = 67; Height = 1; Format = R32U;
};
storage2D<uint> FA_HistStorage { Texture = FA_Hist; };

texture2D FA_HistPrev
{
    Width = 64; Height = 1; Format = R32F;
};
storage2D FA_HistPrevStorage { Texture = FA_HistPrev; };
texture2D FA_State
{
    Width = 2; Height = 1; Format = RGBA32F;
};
storage2D FA_StateStorage { Texture = FA_State; };

// Cold-start/reload discriminator for FA_State and FA_HistPrev.
// This marker is checked BEFORE state is used for exposure calculations.
// A pair of exactly represented float sentinels plus two uint16 framecount
// words avoids precision loss from storing a 32-bit frame counter as float.
// Contents of a newly allocated GPU texture are NOT assumed to be zero.
// Runtime clearing/reload semantics remain subject to native GPU acceptance.
#define _FA_BOOT_MAGIC_A (17231.0)
#define _FA_BOOT_MAGIC_B (28531.0)
texture2D FA_TemporalBoot
{
    Width = 1; Height = 1; Format = RGBA32F;
};
storage2D FA_TemporalBootStorage { Texture = FA_TemporalBoot; };
sampler2D FA_StateSampler
{
    Texture = FA_State;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_LUT
{
    Width = _FA_LUT_SIZE; Height = 1; Format = R32F;   // single source of truth: _FA_LUT_SIZE
};
storage2D FA_LUTStorage { Texture = FA_LUT; };
// The LUT is read through manual interpolation (FA_LUTFetch): float32 texture
// filtering is optional on D3D11/Vulkan, point sampling is not.
sampler2D FA_LUTSampler
{
    Texture = FA_LUT;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_A
{
    Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RGBA16F;
};
sampler2D FA_ASampler
{
    Texture = FA_A;
    MinFilter = LINEAR; MagFilter = LINEAR; MipFilter = LINEAR;
    AddressU = CLAMP; AddressV = CLAMP;
};

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

// FA_M and FA_Q keep the RG16F format but are written as RENDER TARGETS by
// pixel-shader passes (P5/P6), not via typed UAV stores. Typed UAV stores to
// 16-bit formats do not exist on D3D11 FL11_0 (only R32-family stores are
// core there), while RG16F render targets and sampling are.
texture2D FA_M
{
    Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RG16F;
};
sampler2D FA_MSampler
{
    Texture = FA_M;
    MinFilter = POINT; MagFilter = POINT; MipFilter = POINT;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_Q
{
    Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RG16F;
};
sampler2D FA_QSampler
{
    Texture = FA_Q;
    MinFilter = LINEAR; MagFilter = LINEAR; MipFilter = LINEAR;
    AddressU = CLAMP; AddressV = CLAMP;
};

texture2D FA_D
{
    Width = BUFFER_WIDTH; Height = BUFFER_HEIGHT; Format = RGBA16F;
};
sampler2D FA_DSampler
{
    Texture = FA_D;
    MinFilter = LINEAR; MagFilter = LINEAR; MipFilter = LINEAR;
    AddressU = CLAMP; AddressV = CLAMP;
};

// Shared per-group state used by P2.
groupshared uint FA_HistSh[64];
groupshared float FA_PrevSh[64];
groupshared uint FA_T;
groupshared uint FA_C;
groupshared uint FA_SAMPLES;
groupshared float FA_LutSh[_FA_LUT_SIZE];
groupshared int FA_StateFail;
groupshared int FA_StateNative;
groupshared int FA_ColdStart;
groupshared float FA_StateKnee;
groupshared float FA_StateGain;

// -----------------------------------------------------------------------------
// Colour transfer functions and AgX curve.
// -----------------------------------------------------------------------------
float FA_SRGBDecode1(float c)
{
    // saturate() guards the pow() against NaN for negative inputs (float
    // backbuffers / upstream effects can emit negative encoded values).
    return (c <= 0.04045) ? (c / 12.92) : pow(saturate((c + 0.055) / 1.055), 2.4);
}
float FA_SRGBEncode1(float l)
{
    return (l <= 0.0031308) ? (12.92 * l) : (1.055 * pow(max(l, 0.0), 1.0 / 2.4) - 0.055);
}
float FA_GammaDecode1(float c) { return pow(max(c, 0.0), 2.2); }
float FA_GammaEncode1(float l) { return pow(max(l, 0.0), 1.0 / 2.2); }
float3 FA_Decode(float3 c)
{
    float3 decoded = float3(0.0, 0.0, 0.0);
    if (InputEncoding == 0)
        decoded = float3(FA_SRGBDecode1(c.r), FA_SRGBDecode1(c.g), FA_SRGBDecode1(c.b));
    else
        decoded = float3(FA_GammaDecode1(c.r), FA_GammaDecode1(c.g), FA_GammaDecode1(c.b));
    return decoded;
}
float3 FA_Encode(float3 c)
{
    float3 encoded = float3(0.0, 0.0, 0.0);
    if (OutputEncoding == 0)
        encoded = float3(FA_SRGBEncode1(c.r), FA_SRGBEncode1(c.g), FA_SRGBEncode1(c.b));
    else
        encoded = float3(FA_GammaEncode1(c.r), FA_GammaEncode1(c.g), FA_GammaEncode1(c.b));
    return encoded;
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
float FA_NW()
{
    return pow(max(FA_AgxPolynomial(1.0), 0.0), _FA_DISPLAY_GAMMA);
}
float FA_Dn(float s)
{
    float result = 0.0;
    if (s <= 0.0)
        result = 0.0;
    else
    {
        float xs = clamp((log2(s) - _FA_LOG_MIN) / _FA_LOG_RANGE, 0.0, 1.0);
        result = pow(max(FA_AgxPolynomial(xs), 0.0), _FA_DISPLAY_GAMMA) / FA_NW();
    }
    return result;
}
float FA_Native(float u, float gain)
{
    float result = 0.0;
    if (u <= 0.0)
        result = 0.0;
    else
        result = FA_Dn(gain * u);
    return result;
}
float FA_NativeSlope(float u, float gain)
{
    const float h = 1.0e-5;
    return (FA_Native(max(u + h, 0.0), gain) - FA_Native(max(u - h, 0.0), gain)) / (2.0 * h);
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
float FA_ComposedCurve(float u, float gain, float knee)
{
    float result = 0.0;
    if (u <= 0.0)
        result = 0.0;
    else if (u >= 1.0)
        result = 1.0;
    else
    {
        float nativeU = FA_Native(u, gain);
        if (u < _FA_U_B)
        {
            float nb = FA_Native(_FA_U_B, gain);
            float secant = nb / _FA_U_B;
            float db = FA_NativeSlope(_FA_U_B, gain);
            // Preserve the Fritsch-Carlson toe tangent bound.
            float m0 = min(1.0, 3.0 * secant);
            float m1 = min(db, 3.0 * secant);
            float toe = FA_Hermite(u, 0.0, _FA_U_B, 0.0, nb, m0, m1);
            result = lerp(nativeU, toe, ShadowPreservation / 100.0);
        }
        else if (u <= knee)
            result = nativeU;
        else
        {
            float nk = FA_Native(knee, gain);
            float secantH = (1.0 - nk) / max(1.0 - knee, 1.0e-6);
            float dk = min(FA_NativeSlope(knee, gain), 3.0 * secantH);
            result = FA_Hermite(u, knee, 1.0, nk, 1.0, dk, 0.0);
        }
    }
    return result;
}

// Manual LUT sampling. Float32 textures are only guaranteed to support POINT
// sampling on D3D11/Vulkan, so linear interpolation between neighbouring
// texels is done explicitly instead of relying on a LINEAR sampler state.
float FA_LutSampleShared(float x)
{
    // Interpolates this frame's LUT copy in shared memory (used by P2).
    float fi = clamp(x, 0.0, (float)(_FA_LUT_SIZE - 1));
    int i0 = (int)fi;
    int i1 = min(i0 + 1, _FA_LUT_SIZE - 1);
    return lerp(FA_LutSh[i0], FA_LutSh[i1], fi - (float)i0);
}
float FA_LUTFetch(float x)
{
    // Interpolates the stored LUT texture (used by pixel-shader passes).
    float fi = clamp(x, 0.0, (float)(_FA_LUT_SIZE - 1));
    int i0 = (int)fi;
    int i1 = min(i0 + 1, _FA_LUT_SIZE - 1);
    float t = fi - (float)i0;
    float v0 = tex2Dfetch(FA_LUTSampler, int2(i0, 0)).r;
    float v1 = tex2Dfetch(FA_LUTSampler, int2(i1, 0)).r;
    return lerp(v0, v1, t);
}

// -----------------------------------------------------------------------------
// Oklab conversion, matrix transforms, helper utilities.
// -----------------------------------------------------------------------------
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
bool FA_InGamut(float3 rgb)
{
    return all(rgb >= float3(-1.0e-4, -1.0e-4, -1.0e-4)) && all(rgb <= float3(1.0001, 1.0001, 1.0001));
}
float FA_IGN(float x, float y)
{
    return frac(52.9829189 * frac(0.06711056 * x + 0.00583715 * y));
}

// -----------------------------------------------------------------------------
// Color temperature: von Kries chromatic adaptation in the Oklab LMS space.
// -----------------------------------------------------------------------------
// Row-major copy of the M1 matrix inside FA_OklabFromLinear (keep the two in
// sync). Adapting in this LMS space is the colorimetrically correct von Kries
// model; a naive per-channel RGB gain would distort hue relations.
static const float3x3 FA_RGB_TO_LMS = float3x3(
    0.4122214708, 0.5363325363, 0.0514459929,
    0.2119034982, 0.6806995451, 0.1073969566,
    0.0883024619, 0.2817188376, 0.6299787005);
// Exact inverse of FA_RGB_TO_LMS (the same LMS-cube matrix FA_LinearFromOklab
// already uses, up to rounding), precomputed in double precision.
static const float3x3 FA_LMS_TO_RGB = float3x3(
     4.0767416613, -3.3077115904,  0.2309699287,
    -1.2684380041,  2.6097574007, -0.3413193963,
    -0.0041960865, -0.7034186145,  1.7076147009);
// LMS of the luminance-normalised 6500 K locus white. Gains are measured
// against this point, not against D65, so the 6500 K default is neutral.
static const float3 FA_WB_REFERENCE_LMS = float3(1.0106792805, 1.0017568775, 1.0211812566);

// Chromaticity of the Planckian locus (Kang et al. 2002 polynomial
// approximation, valid 1667 K to 25000 K) as luminance-normalised linear
// sRGB. Locus points outside the sRGB gamut at the extreme warm end are
// clamped per channel, so the result is always finite and in gamut.
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
    // XYZ (Y = 1) to linear sRGB with the Y term folded into the constants.
    float3 w = float3(
        3.2406255 * X - 1.5372080 - 0.4986286 * Z,
       -0.9689307 * X + 1.8757561 + 0.0415175 * Z,
        0.0557101 * X - 0.2040211 + 1.0569959 * Z);
    w = max(w, 0.0);
    return w / max(dot(w, FA_LUMA), 1.0e-6);
}

// Per-channel von Kries gain that maps the image white onto the target
// temperature, measured relative to the 6500 K locus point.
float3 FA_ColorTempGain()
{
    float3 lmsW = mul(FA_RGB_TO_LMS, FA_TempWhiteRGB(clamp(ColorTemp, 1667.0, 25000.0)));
    return lmsW / FA_WB_REFERENCE_LMS;
}

// Applies Color Temperature to linear sRGB. The input white (sRGB D65, which
// this Oklab implementation maps to exactly a = b = 0) takes on the target
// tint; every other color adapts proportionally in LMS, preserving hue
// relations. Grays stay finite and monotone for every slider value.
float3 FA_WhiteBalance(float3 rgb)
{
    float3 balanced = rgb;
    if (ColorTemp == 6500.0)
        balanced = rgb;
    else
    {
        float3 lms = mul(FA_RGB_TO_LMS, rgb) * FA_ColorTempGain();
        balanced = mul(FA_LMS_TO_RGB, lms);
    }
    return balanced;
}

// -----------------------------------------------------------------------------
// P0 (correction F41): explicit histogram clear before atomic accumulation.
// This extra pass runs every frame, even when visual processing is bypassed.
// GPU/FX compiler and synchronization behavior still require backend testing.
// -----------------------------------------------------------------------------
[numthreads(128, 1, 1)]
void FlexAgX_ClearHistogram(uint3 id : SV_DispatchThreadID)
{
    if (id.x < 67u)
        tex2Dstore(FA_HistStorage, int2((int)id.x, 0), 0u);
}

// -----------------------------------------------------------------------------
// P1: sampled log-luminance histogram plus all-sample/white counters (half-resolution).
// -----------------------------------------------------------------------------
groupshared uint FA_P1Bins[64];
groupshared uint FA_P1Valid;
groupshared uint FA_P1White;
groupshared uint FA_P1Samples;
groupshared int FA_UpdateHistRef;

[numthreads(16, 16, 1)]
void FlexAgX_Histogram(uint3 id : SV_DispatchThreadID, uint3 tid : SV_GroupThreadID)
{
    // The output pass is an exact pass-through in this mode. Avoid sampling the
    // back buffer and building a histogram when the effect is not visible.
    if (OverallStrength <= 0.0 && DebugView == 0) return;

    uint localIndex = tid.y * 16 + tid.x;
    if (localIndex < 64) FA_P1Bins[localIndex] = 0u;
    if (localIndex == 0) { FA_P1Valid = 0u; FA_P1White = 0u; FA_P1Samples = 0u; }
    barrier();

    // Two-phase dither from an exact integer LCG. Unlike framecount times an
    // irrational constant in float32, this never degenerates at large frame
    // counts (integer wraparound is the intended behaviour here).
    uint fc = (uint)framecount;
    uint hsh = fc * 747796405u + 2891336453u;
    int ox = (int)((hsh >> 13) & 1u);
    int oy = (int)((hsh >> 26) & 1u);
    int2 samplePos = int2((int)(id.x * 2) + ox, (int)(id.y * 2) + oy);
    if (samplePos.x < BUFFER_WIDTH && samplePos.y < BUFFER_HEIGHT)
    {
        // Count every in-bounds sample for Clip Guard. The luminance histogram
        // itself intentionally excludes pure-black samples.
        atomicAdd(FA_P1Samples, 1u);
        // Implicit-LOD tex2D sampling is not allowed in compute shaders,
        // so fetch the exact pixel instead (the sampler is POINT anyway).
        float3 rgb = FA_Decode(tex2Dfetch(FA_BackBufferSampler, samplePos).rgb);
        if (max(rgb.r, max(rgb.g, rgb.b)) > 0.0)
        {
            float Y = dot(rgb, FA_LUMA);
            // Bins aligned to the curve's log domain [LOG_MIN, LOG_MIN + RANGE].
            int bin = clamp((int)floor((log2(max(Y, exp2(_FA_LOG_MIN))) - _FA_LOG_MIN) * (64.0 / _FA_LOG_RANGE)), 0, 63);
            atomicAdd(FA_P1Bins[bin], 1u);
            atomicAdd(FA_P1Valid, 1u);
            if (Y >= _FA_WHITE_THRESHOLD) atomicAdd(FA_P1White, 1u);
        }
    }
    barrier();

    if (localIndex < 64)
    {
        uint count = FA_P1Bins[localIndex];
        if (count != 0u)
            atomicAdd(FA_HistStorage, int2((int)localIndex, 0), count);
    }
    if (localIndex == 0)
    {
        if (FA_P1Valid != 0u) atomicAdd(FA_HistStorage, int2(64, 0), FA_P1Valid);
        if (FA_P1White != 0u) atomicAdd(FA_HistStorage, int2(65, 0), FA_P1White);
        if (FA_P1Samples != 0u) atomicAdd(FA_HistStorage, int2(66, 0), FA_P1Samples);
    }
}

// -----------------------------------------------------------------------------
// P2: state adaptation, histogram comparison, composed 1024-entry curve LUT.
// The LUT is rebuilt while the effect is active. While bypassed, the state pass
// clears the histogram and skips adaptation/LUT work.
// -----------------------------------------------------------------------------
[numthreads(256, 1, 1)]
void FlexAgX_State(uint3 id : SV_DispatchThreadID, uint3 tid : SV_GroupThreadID)
{
    uint lane = tid.x;

    // Keep the histogram clean while bypassed, so re-enabling cannot consume
    // stale atomic counts. No LUT/state work is needed for exact pass-through.
    if (OverallStrength <= 0.0 && DebugView == 0)
    {
        if (lane < 67) tex2Dstore(FA_HistStorage, int2((int)lane, 0), 0u);
        return;
    }

    // Load CURRENT histogram first. Do not fetch the previous histogram
    // until the temporal validity marker and retained controller state have
    // been checked. An uninitialized previous-scene texture has no contract.
    if (lane < 64)
        FA_HistSh[lane] = tex2Dfetch(FA_HistStorage, int2((int)lane, 0)).x;
    if (lane == 64)
    {
        FA_T = tex2Dfetch(FA_HistStorage, int2(64, 0)).x;
        FA_C = tex2Dfetch(FA_HistStorage, int2(65, 0)).x;
        FA_SAMPLES = tex2Dfetch(FA_HistStorage, int2(66, 0)).x;
    }
    barrier();

    // One workgroup owns this state pass. Source-visible validation rejects
    // first use, stale resources, effect-disable frame gaps and counter resets.
    // A texture's contents are inspected ONLY as a validity tag until accepted.
    if (lane == 0)
    {
        float4 stamp = tex2Dfetch(FA_TemporalBootStorage, int2(0, 0));
        uint previous = (uint)framecount - 1u;
        bool markerOK = (stamp.x == _FA_BOOT_MAGIC_A) &&
                        (stamp.y == _FA_BOOT_MAGIC_B) &&
                        (stamp.z == (float)(previous & 65535u)) &&
                        (stamp.w == (float)(previous >> 16u));
        bool valid = false;
        if (markerOK)
        {
            float4 prior0 = tex2Dfetch(FA_StateStorage, int2(0, 0));
            float4 prior1 = tex2Dfetch(FA_StateStorage, int2(1, 0));
            valid = all(prior0 == prior0) && all(prior1 == prior1) &&
                    all(abs(prior0) <= float4(32.0, 8.0, 1.0, 1.0)) &&
                    all(abs(prior1) <= float4(1.0, 1.0, _FA_GAIN_LIMIT, 1.0)) &&
                    (prior1.y == 0.0 || prior1.y == 1.0);
        }
        FA_ColdStart = valid ? 0 : 1;
    }
    barrier();

    if (lane < 64)
    {
        float currentNorm = (FA_T > 0u) ? ((float)FA_HistSh[lane] / (float)FA_T) : 0.0;
        if (FA_ColdStart != 0)
            FA_PrevSh[lane] = currentNorm; // first scene compares to itself
        else
        {
            float oldNorm = tex2Dfetch(FA_HistPrevStorage, int2((int)lane, 0)).r;
            FA_PrevSh[lane] = (oldNorm >= 0.0 && oldNorm <= 1.0) ? oldNorm : currentNorm;
        }
    }
    barrier();

    // S1: clear all histogram bins and counters for the next frame (parallel).
    if (lane < 67)
        tex2Dstore(FA_HistStorage, int2((int)lane, 0), 0u);

    if (lane == 0)
    {
        FA_StateFail = 0;
        FA_StateNative = 0;
        FA_UpdateHistRef = 1;

        // Percentiles over the sampled (non-pure-black) pixels; bins are
        // aligned to the curve's log domain.
        float e50 = _FA_LOG_MIN;
        float e90 = _FA_LOG_MIN;
        if (FA_T > 0u)
        {
            float targets[2];
            targets[0] = 0.50 * (float)FA_T;
            targets[1] = 0.90 * (float)FA_T;
            float values[2];
            values[0] = _FA_LOG_MIN; values[1] = _FA_LOG_MIN;
            for (int which = 0; which < 2; ++which)
            {
                float cumulative = 0.0;
                for (int i = 0; i < 64; ++i)
                {
                    float previous = cumulative;
                    cumulative += (float)FA_HistSh[i];
                    if (cumulative >= targets[which])
                    {
                        float fractionInBin = saturate((targets[which] - previous) / max((float)FA_HistSh[i], 1.0));
                        values[which] = _FA_LOG_MIN + ((float)i + fractionInBin) * (_FA_LOG_RANGE / 64.0);
                        break;
                    }
                }
            }
            e50 = values[0];
            e90 = values[1];
        }

        // Cold start has a complete finite default for every state component.
        // Read old resources only after the temporal validity check succeeds.
        float firstKnee = AutoHighlightKnee ?
            clamp(exp2(e90), _FA_KNEE_MIN, _FA_KNEE_MAX) : HighlightKnee;
        float4 old0 = float4(e50, 0.0, firstKnee, 0.0);
        float4 old1 = float4(0.0, 0.0, 0.0, 0.0);
        if (FA_ColdStart == 0)
        {
            old0 = tex2Dfetch(FA_StateStorage, int2(0, 0));
            old1 = tex2Dfetch(FA_StateStorage, int2(1, 0));
        }
        float x = old0.x;             // adapted scene key (log2)
        float v = old0.y;             // key velocity (EV/s)
        float knee = old0.z;          // smoothed auto highlight knee
        float cutCount = old0.w;      // scene-cut persistence timer (seconds)
        float storedLambda = old1.x;  // persisted auto strength (for freezing)
        float initialised = old1.y;
        float appliedAutoEV = clamp(old1.z, -_FA_GAIN_LIMIT, _FA_GAIN_LIMIT);
        float warmup = old1.w;        // exposure ramp-in after the first valid frame
        if (initialised < 0.5) appliedAutoEV = 0.0;

        float dt = clamp(frametime / 1000.0, 0.001, 0.25);
        // Smooth dark gate over [-9, -6] EV: below -9 EV the automatic
        // contribution is zero; it fades in gradually above that threshold.
        float darkGate = (FA_T >= 64u) ? saturate((e50 + 9.0) / 3.0) : 0.0;
        bool adapt = !FreezeExposure && darkGate > 0.0;

        // Explicit 0% always disables automatic exposure, even while frozen.
        // Otherwise, do not retain stale strength when the dark gate closes or
        // too few valid samples remain. FreezeExposure preserves other state.
        if (AutoExposureStrength <= 0.0)
            storedLambda = 0.0;
        else if (!FreezeExposure && darkGate <= 0.0)
            storedLambda = 0.0;

        if (adapt)
        {
            float kneeRaw = AutoHighlightKnee ? clamp(exp2(e90), _FA_KNEE_MIN, _FA_KNEE_MAX) : HighlightKnee;

            // S3: initialise from the median key on the first valid frame.
            if (initialised < 0.5)
            {
                x = e50;
                v = 0.0;
                knee = kneeRaw;
                initialised = 1.0;
                warmup = 0.0;
            }

            // S4: Clip Guard uses all in-bounds samples, including pure black.
            float whiteFraction = (FA_SAMPLES > 0u) ? ((float)FA_C / (float)FA_SAMPLES) : 0.0;
            float f = saturate(1.0 - (whiteFraction / max(ClipGuard / 100.0, 1.0e-6)));

            // S5: critically damped key adaptation with a bounded rate.
            // The w clamp (w*dt <= 0.5) makes the integrator unconditionally
            // stable at every frametime the clamp allows.
            float target = e50;
            // CT-004 / F23-F24: the user-facing deadband means the adapted
            // key must remain stationary when the error is within tolerance.
            // Clearing residual velocity also makes an exactly neutral target
            // independent of the BrightenSpeed/DarkenSpeed branch.
            if (abs(target - x) <= Deadband)
            {
                v = 0.0;
            }
            else
            {
                float tau = (target > x) ? BrightenSpeed : DarkenSpeed;
                float w = 1.0 / max(tau, 2.0 * dt);
                float acceleration = w * w * (target - x) - 2.0 * w * v;
                v = clamp(v + acceleration * dt, -MaxChangeRate, MaxChangeRate);
                x += v * dt;
            }

            // S6: compare against a retained scene baseline. If a substantial
            // difference persists for 0.10 s, accept the new histogram as the
            // baseline. This detects a hard cut even after the next frame is
            // visually stable; one-frame differences must not trigger a reset, even at low FPS.
            float D = 0.0;
            for (int i = 0; i < 64; ++i)
            {
                float p = (float)FA_HistSh[i] / (float)FA_T;
                D += abs(p - FA_PrevSh[i]);
            }
            D *= 0.5;
            // CT-005 / F29: require a previously observed discrepant frame.
            // One stalled/slow frame can have dt >= _FA_SCENE_CUT_SECONDS;
            // elapsed time alone is not evidence that the difference persisted.
            bool hadCutCandidate = (cutCount > 0.0);
            if (D > SceneChangeSensitivity)
            {
                cutCount += dt;
                FA_UpdateHistRef = 0; // hold the pre-cut baseline until confirmed
            }
            else
            {
                cutCount = 0.0;
                FA_UpdateHistRef = 1; // stable scene: keep tracking its histogram
            }
            if (hadCutCandidate && cutCount >= _FA_SCENE_CUT_SECONDS)
            {
                // Keep the scene-key correction bounded; the applied exposure
                // itself is separately rate-limited below.
                x += clamp(e50 - x, -0.5 * MaxChangeRate, 0.5 * MaxChangeRate);
                v = 0.0;
                cutCount = 0.0;
                FA_UpdateHistRef = 1; // accept the newly confirmed scene
            }

            // S7: smoothed highlight knee.
            knee += (1.0 - exp(-dt / _FA_KNEE_TAU)) * (kneeRaw - knee);

            // Auto strength for this frame, ramped in after the first valid
            // frame so nothing pops, gated by the dark gate and clip guard.
            warmup = min(warmup + dt, 1.0);
            storedLambda = (AutoExposureStrength / 100.0) * f * darkGate * saturate(warmup / _FA_WARMUP_SECONDS);
        }
        else
        {
            // Freeze or a closed dark gate must not leave a half-completed cut
            // timer waiting to fire later. Track the current histogram baseline.
            cutCount = 0.0;
            FA_UpdateHistRef = 1;
        }

        // S8: exposure gain. The auto component pulls the scene key toward
        // display grey in log space and is EXACTLY zero at zero strength.
        // The manual ExposureOffset is additive and always live.
        float eGrey = 0.0;
        {
            float lo = -14.0;
            float hi = 6.0;
            for (int b = 0; b < 30; ++b)
            {
                float mid = 0.5 * (lo + hi);
                if (FA_Dn(exp2(mid)) < _FA_GREY) lo = mid; else hi = mid;
            }
            eGrey = 0.5 * (lo + hi);
        }
        float targetAutoEV = clamp(storedLambda * (eGrey - x), -_FA_GAIN_LIMIT, _FA_GAIN_LIMIT);
        if (AutoExposureStrength <= 0.0)
        {
            // Honor the explicit 0% setting as exactly neutral immediately.
            appliedAutoEV = 0.0;
        }
        else if (!FreezeExposure)
        {
            // Rate-limit the actual automatic exposure contribution, including
            // changes caused by scene cuts and Clip Guard. Manual offset remains
            // immediate and additive; FreezeExposure holds this applied value.
            float maxStepEV = MaxChangeRate * dt;
            appliedAutoEV += clamp(targetAutoEV - appliedAutoEV, -maxStepEV, maxStepEV);
        }
        float gainEV = clamp(appliedAutoEV + ExposureOffset, -_FA_GAIN_LIMIT, _FA_GAIN_LIMIT);

        // S9: knee used for this frame's LUT. Manual knee stays live while
        // frozen; the smoothed auto knee is persisted separately.
        float buildKnee = AutoHighlightKnee ? clamp(knee, _FA_KNEE_MIN, _FA_KNEE_MAX) : HighlightKnee;

        // Persist state (the retry below never corrupts the stored knee).
        tex2Dstore(FA_StateStorage, int2(0, 0), float4(x, v, knee, cutCount));
        tex2Dstore(FA_StateStorage, int2(1, 0), float4(storedLambda, initialised, appliedAutoEV, warmup));

        FA_StateKnee = buildKnee;
        FA_StateGain = exp2(gainEV);
    }
    barrier();

    // Update the scene reference after the decision above. During a sustained
    // candidate cut it remains unchanged; after confirmation it advances.
    if (lane < 64 && FA_UpdateHistRef != 0)
    {
        float norm = (FA_T != 0u) ? (float)FA_HistSh[lane] / (float)FA_T : 0.0;
        tex2Dstore(FA_HistPrevStorage, int2((int)lane, 0), float4(norm, 0.0, 0.0, 0.0));
    }

    // Finalize the temporal marker after the state and previous-scene writes.
    // The signed framecount source is handled as a 32-bit uint, split into two
    // uint16 limbs that are exactly representable by the RGBA32F marker.
    barrier();
    if (lane == 0)
    {
        uint now = (uint)framecount;
        tex2Dstore(FA_TemporalBootStorage, int2(0, 0),
            float4(_FA_BOOT_MAGIC_A, _FA_BOOT_MAGIC_B,
                   (float)(now & 65535u), (float)(now >> 16u)));
    }
    barrier();

    // S10/S11: build a monotone 1D curve LUT. A failed validation lowers the
    // knee and retries; the final fallback is normalized to preserve white.
    for (int attempt = 0; attempt < 4; ++attempt)
    {
        for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
        {
            float u = _FA_LUT_DOMAIN * (float)i / (float)(_FA_LUT_SIZE - 1);
            FA_LutSh[i] = FA_ComposedCurve(u, FA_StateGain, FA_StateKnee);
        }
        barrier();

        if (lane == 0)
        {
            // Check the actual scalar LUT and a neutral 8-bit end-to-end ramp.
            // The LUT sampler takes texel indices, not normalized values. Do not
            // constrain upward step size: a steep but monotone tone curve may
            // legitimately skip output codes, and RGB cross-terms make per-
            // channel monotonicity invalid for saturated ramps.
            int passed = 1;
            float3 w = FA_Inset(float3(1.0, 1.0, 1.0));
            float3 previousCode = float3(-1.0, -1.0, -1.0);
            float lutScale = (float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN;
            for (int code = 0; code <= 255; ++code)
            {
                float3 rampIn = ((float)code / 255.0).xxx;
                float3 u = clamp(FA_Inset(FA_Decode(rampIn)) / w, 0.0, _FA_LUT_DOMAIN);
                float3 lutIndex = u * lutScale;
                float3 outv = float3(FA_LutSampleShared(lutIndex.r),
                                     FA_LutSampleShared(lutIndex.g),
                                     FA_LutSampleShared(lutIndex.b));
                float3 linearOut = clamp(max(FA_Outset(outv * w), 0.0), 0.0, 1.0);
                float3 codeOut = round(255.0 * FA_Encode(linearOut));
                if (code > 0 && any(codeOut < previousCode)) passed = 0;
                previousCode = codeOut;
            }

            // Reject decreasing, negative, above-white, or non-finite values
            // over the entire stored domain, including the constant region.
            if (!(FA_LutSh[0] >= 0.0 && FA_LutSh[0] <= 1.000001)) passed = 0;
            for (int i = 1; i < _FA_LUT_SIZE; ++i)
            {
                if (!(FA_LutSh[i] >= FA_LutSh[i - 1] - 1.0e-6) ||
                    !(FA_LutSh[i] >= 0.0) || !(FA_LutSh[i] <= 1.000001))
                {
                    passed = 0;
                    break;
                }
            }

            if (passed == 0 && attempt < 3)
            {
                FA_StateFail = 1;
                FA_StateKnee = max(_FA_KNEE_MIN, FA_StateKnee - 0.05);
            }
            else if (passed == 0)
            {
                FA_StateNative = 1;
            }
            else
            {
                // Clear the flag so a passing attempt after an earlier failure
                // exits the retry loop immediately; left sticky, it would
                // force all four LUT rebuilds to run every time.
                FA_StateFail = 0;
            }
        }
        barrier();
        if (FA_StateFail == 0 || FA_StateNative != 0) break;
    }

    if (FA_StateNative != 0)
    {
        for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
        {
            float u = _FA_LUT_DOMAIN * (float)i / (float)(_FA_LUT_SIZE - 1);
            float nativeWhite = max(FA_Dn(FA_StateGain), 1.0e-6);
            FA_LutSh[i] = saturate(FA_Dn(FA_StateGain * u) / nativeWhite);
        }
        barrier();
    }

    for (uint i = lane; i < _FA_LUT_SIZE; i += 256)
        tex2Dstore(FA_LUTStorage, int2((int)i, 0), float4(FA_LutSh[i], 0.0, 0.0, 0.0));
}

// -----------------------------------------------------------------------------
// Full-screen triangle vertex shader used by all pixel passes.
// -----------------------------------------------------------------------------
void FlexAgX_FullscreenVS(uint id : SV_VertexID, out float4 position : SV_Position, out float2 texcoord : TEXCOORD0)
{
    texcoord.x = (id == 2) ? 2.0 : 0.0;
    texcoord.y = (id == 1) ? 2.0 : 0.0;
    position = float4(texcoord * float2(2.0, -2.0) + float2(-1.0, 1.0), 0.0, 1.0);
}
// -----------------------------------------------------------------------------
// P3: inset -> normalised LUT -> outset AgX curve.
// -----------------------------------------------------------------------------
float4 FlexAgX_CurvePS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    if (OverallStrength <= 0.0 && DebugView == 0) return float4(0.0, 0.0, 0.0, 0.0);
    float4 source = tex2D(FA_BackBufferSampler, texcoord);
    float3 rgb = FA_Decode(source.rgb);
    float3 a = FA_Inset(rgb);
    // White point derived from the inset matrix itself (single source of truth,
    // cannot desync from the matrix constants).
    float3 w = FA_Inset(float3(1.0, 1.0, 1.0));
    float3 n = a / w;
    // Manual LUT interpolation over [0, _FA_LUT_DOMAIN]; no float32 hardware
    // filtering involved.
    float3 x3 = clamp(n, 0.0, _FA_LUT_DOMAIN) * ((float)(_FA_LUT_SIZE - 1) / _FA_LUT_DOMAIN);
    float3 outv = float3(FA_LUTFetch(x3.r), FA_LUTFetch(x3.g), FA_LUTFetch(x3.b));
    float3 q = outv * w;
    float3 r = max(FA_Outset(q), 0.0);
    return float4(r, source.a);
}

// -----------------------------------------------------------------------------
// P4: restore source hue in Oklab while retaining the curve's lightness/chroma.
// -----------------------------------------------------------------------------
float4 FlexAgX_HuePS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    if (OverallStrength <= 0.0 && DebugView == 0) return float4(0.0, 0.0, 0.0, 0.0);
    float4 source = tex2D(FA_BackBufferSampler, texcoord);
    float3 src = FA_Decode(source.rgb);
    float3 inLab = FA_OklabFromLinear(src);
    float inputChroma = length(inLab.yz);
    float hIn = 0.0;
    if (inputChroma >= 1.0e-4)
        hIn = atan2(inLab.z, inLab.y);

    float3 curved = max(tex2D(FA_ASampler, texcoord).rgb, 0.0);
    float3 lab = FA_OklabFromLinear(curved);
    float curvedChroma = length(lab.yz);
    float h = 0.0;
    // F38: guard the polar origin before invoking atan2, not afterwards.
    if (curvedChroma > 1.0e-6)
        h = atan2(lab.z, lab.y);
    float delta = FA_WrapAngle(hIn - h);
    // Weight by the SOURCE chroma: AgX desaturates the shoulder, so weighting
    // by the curved chroma faded the restoration out exactly where hue drift
    // is strongest. Source chroma does not collapse and the magnitude of the
    // rotated vector is preserved, so this is safe for near-neutral pixels too.
    float theta = delta * (HueRestoration / 100.0) * smoothstep(0.0, 0.03, inputChroma);
    if (inputChroma < 1.0e-4) theta = 0.0;
    float cs = cos(theta), sn = sin(theta);
    float a = lab.y * cs - lab.z * sn;
    float b = lab.y * sn + lab.z * cs;
    float3 outv = FA_LinearFromOklab(float3(lab.x, a, b));
    return float4(outv, source.a);
}

// -----------------------------------------------------------------------------
// P5: mean and variance of luminance in a clamped 5 x 5 neighbourhood.
// Runs as a pixel shader writing to an RG16F render target: typed UAV stores
// to 16-bit formats are not available on D3D11 FL11_0, while render target
// writes to RG16F are core everywhere.
// -----------------------------------------------------------------------------
float4 FlexAgX_DetailMeanPS(float4 position : SV_Position) : SV_Target
{
    if ((OverallStrength <= 0.0 && DebugView == 0) || LocalDetail <= 0.0) return float4(0.0, 0.0, 0.0, 0.0);
    int2 px = (int2)position.xy;   // SV_Position is pixel-centre aligned (x.5)
    float sumY = 0.0;
    float sumY2 = 0.0;
    for (int oy = -2; oy <= 2; ++oy)
    {
        for (int ox = -2; ox <= 2; ++ox)
        {
            int2 p = int2(clamp(px.x + ox, 0, BUFFER_WIDTH - 1), clamp(px.y + oy, 0, BUFFER_HEIGHT - 1));
            float3 rgb = tex2Dfetch(FA_BSampler, p).rgb;
            float Y = dot(rgb, FA_LUMA);
            sumY += Y;
            sumY2 += Y * Y;
        }
    }
    float mean = sumY / 25.0;
    float variance = max(sumY2 / 25.0 - mean * mean, 0.0);
    return float4(mean, variance, 0.0, 0.0);
}

// -----------------------------------------------------------------------------
// P6: guided-filter coefficients, averaged over a clamped 5 x 5 neighbourhood.
// Reads the RG16F mean/variance buffer through a POINT sampler and writes the
// coefficients to an RG16F render target (no typed UAV access involved).
// -----------------------------------------------------------------------------
float4 FlexAgX_DetailBasePS(float4 position : SV_Position) : SV_Target
{
    if ((OverallStrength <= 0.0 && DebugView == 0) || LocalDetail <= 0.0) return float4(0.0, 0.0, 0.0, 0.0);
    int2 px = (int2)position.xy;   // SV_Position is pixel-centre aligned (x.5)
    float sumA = 0.0;
    float sumB = 0.0;
    for (int oy = -2; oy <= 2; ++oy)
    {
        for (int ox = -2; ox <= 2; ++ox)
        {
            int2 p = int2(clamp(px.x + ox, 0, BUFFER_WIDTH - 1), clamp(px.y + oy, 0, BUFFER_HEIGHT - 1));
            float2 mv = tex2Dfetch(FA_MSampler, p).rg;
            float aq = mv.y / (mv.y + _FA_DETAIL_EPS);
            float bq = (1.0 - aq) * mv.x;
            sumA += aq;
            sumB += bq;
        }
    }
    return float4(sumA / 25.0, sumB / 25.0, 0.0, 0.0);
}

// -----------------------------------------------------------------------------
// P7: self-guided local detail restoration.
// -----------------------------------------------------------------------------
float4 FlexAgX_DetailApplyPS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    if (OverallStrength <= 0.0 && DebugView == 0) return float4(0.0, 0.0, 0.0, 0.0);
    float4 b = tex2D(FA_BSampler, texcoord);
    if (LocalDetail <= 0.0) return b;
    float3 rgb = b.rgb;
    float Y = dot(rgb, FA_LUMA);
    float2 maMb = tex2D(FA_QSampler, texcoord).rg;
    float base = maMb.x * Y + maMb.y;
    float ratio = (Y <= 1.0e-6) ? 1.0 : pow(max(Y / max(base, 1.0e-4), 0.0), LocalDetail / 100.0);
    // Bounded local contrast: prevents unbounded noise sparkle in near-black
    // areas where the guided base can approach zero.
    ratio = clamp(ratio, 1.0 / _FA_DETAIL_RATIO_MAX, _FA_DETAIL_RATIO_MAX);
    return float4(rgb * ratio, b.a);
}

// CT-006 / F39: the original branch is white-balanced before blending and can
// lie outside the display gamut even when the processed branch is mapped.
// Re-constrain ONLY out-of-gamut composites; leave in-gamut results bit-identical
// through this helper. This is a 12-step constant-lightness chroma reduction,
// not RGB channel clipping (except final floating-point safety saturation).
// CPU numerical probes are not a substitute for an actual FX/GPU compiler run.
float3 FA_ConstrainGamutAfterMix(float3 composite)
{
    float3 constrained = composite;
    bool withinGamut = all(composite >= float3(0.0, 0.0, 0.0)) &&
                       all(composite <= float3(1.0, 1.0, 1.0));
    if (!withinGamut)
    {
        float3 lab = FA_OklabFromLinear(composite);
        float L = clamp(lab.x, 0.0, 1.0);
        float lo = 0.0;
        float hi = 1.0;
        for (int i = 0; i < 12; ++i)
        {
            float mid = 0.5 * (lo + hi);
            float3 trial = FA_LinearFromOklab(float3(L, lab.y * mid, lab.z * mid));
            if (all(trial >= float3(0.0, 0.0, 0.0)) &&
                all(trial <= float3(1.0, 1.0, 1.0)))
                lo = mid;
            else
                hi = mid;
        }
        constrained = clamp(FA_LinearFromOklab(float3(L, lab.y * lo, lab.z * lo)), 0.0, 1.0);
    }
    return constrained;
}

// -----------------------------------------------------------------------------
// P8: Oklab chroma roll-off, strength mix, debug, output encoding and dither.
// -----------------------------------------------------------------------------
float4 FlexAgX_OutputPS(float4 position : SV_Position, float2 texcoord : TEXCOORD0) : SV_Target
{
    float4 originalEncoded = tex2D(FA_BackBufferSampler, texcoord);
    // F40 contract (unchanged): exact encoded pass-through at 0% strength.
    // If InputEncoding != OutputEncoding, ANY nonzero strength requests output
    // conversion and therefore may visibly jump relative to the exact bypass.
    // Choosing a continuous cross-encoding transition is a separate UI policy.
    // No decode/encode round-trip or dither in this zero-strength path.
    // Debug views remain available as explicit diagnostics even at 0%.
    if (OverallStrength <= 0.0 && DebugView == 0)
        return originalEncoded;
    // Color temperature is applied before the Oklab chroma roll-off so the
    // rare out-of-gamut colors produced by strong shifts are gamut-mapped by
    // the existing compression instead of hard-clipping at the end.
    float3 orig = FA_WhiteBalance(FA_Decode(originalEncoded.rgb));
    float3 rgb = FA_WhiteBalance(max(tex2D(FA_DSampler, texcoord).rgb, 0.0));
    float3 lab = FA_OklabFromLinear(rgb);
    // Clamp lightness to the display range: above L = 1 no chroma is in gamut,
    // which previously collapsed such pixels to pure white (Cmax = 0).
    float L = min(lab.x, 1.0);
    float a = lab.y;
    float b = lab.z;
    float C = sqrt(a * a + b * b);
    float h = 0.0;
    float ch = 1.0, sh = 0.0;
    // F38: the achromatic angle is not defined on all target languages.
    if (C > 1.0e-6)
    {
        h = atan2(b, a);
        ch = cos(h);
        sh = sin(h);
    }

    // 10 bisection iterations give ~4e-4 chroma precision; skipped entirely
    // for achromatic pixels.
    float Cmax = 0.0;
    if (C > 1.0e-6)
    {
        float lo = 0.0;
        float hi = 0.4;
        for (int i = 0; i < 10; ++i)
        {
            float mid = 0.5 * (lo + hi);
            float3 trial = FA_LinearFromOklab(float3(L, mid * ch, mid * sh));
            if (FA_InGamut(trial)) lo = mid;
            else hi = mid;
        }
        Cmax = lo;
    }
    float x = C / max(Cmax, 1.0e-6);
    float k = GamutRolloffStart;
    float y = x;
    if (x > k)
    {
        // CT-008: the branch mathematically guarantees t >= 0 for the UI
        // bounds, but clamp the pow operand explicitly for HLSL analysis.
        // This retains the exact expression for all legal positive t.
        float t = (x - k) / (1.0 - k);
        y = k + (1.0 - k) * t / pow(1.0 + pow(max(t, 0.0), _FA_GAMUT_P), 1.0 / _FA_GAMUT_P);
    }
    float Cp = y * Cmax;
    float3 outLinear = clamp(FA_LinearFromOklab(float3(L, Cp * ch, Cp * sh)), 0.0, 1.0);
    float3 finalLinear = lerp(orig, outLinear, OverallStrength / 100.0);
    // F39: the white-balanced original branch may exceed gamut after mixing.
    // Run the safety mapper after (not before) lerp to avoid channel clipping.
    finalLinear = FA_ConstrainGamutAfterMix(finalLinear);

    if (DebugView == 1)
    {
        if (dot(orig, FA_LUMA) >= _FA_WHITE_THRESHOLD)
            finalLinear = float3(1.0, 0.0, 1.0);
    }
    else if (DebugView == 2)
    {
        // Texel 1 = (auto strength, initialised, applied auto EV, warmup).
        float4 state1 = tex2D(FA_StateSampler, float2((1.0 + 0.5) / 2.0, 0.5));
        float totalGainEV = clamp(state1.z + ExposureOffset, -_FA_GAIN_LIMIT, _FA_GAIN_LIMIT);
        float gain = saturate((totalGainEV + _FA_GAIN_LIMIT) / (2.0 * _FA_GAIN_LIMIT));
        finalLinear = gain.xxx;
    }

    float3 encoded = FA_Encode(clamp(finalLinear, 0.0, 1.0));
    if (Dithering)
    {
        float2 pixel = floor(position.xy);
        float noise = FA_IGN(pixel.x, pixel.y) - 0.5;
        if (BUFFER_COLOR_BIT_DEPTH == 10)
            encoded += noise / 1023.0;
        else if (BUFFER_COLOR_BIT_DEPTH != 16)
            encoded += noise / 255.0;
    }
    encoded = clamp(encoded, 0.0, 1.0);
    return float4(encoded, originalEncoded.a);
}

// -----------------------------------------------------------------------------
// Pass chain. The histogram pass dispatches ceil-half-resolution groups; the
// detail mean/base stages run as full-screen pixel-shader passes.
// -----------------------------------------------------------------------------
technique FlexAgX
{
    // F41: a separate GPU pass provides a source-visible clear-before-add stage.
    pass FlexAgX_ClearHistogramPass
    {
        ComputeShader = FlexAgX_ClearHistogram;
        DispatchSizeX = 1;
        DispatchSizeY = 1;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_HistogramPass
    {
        ComputeShader = FlexAgX_Histogram;
        DispatchSizeX = (BUFFER_WIDTH + 31) / 32;
        DispatchSizeY = (BUFFER_HEIGHT + 31) / 32;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_StatePass
    {
        ComputeShader = FlexAgX_State;
        DispatchSizeX = 1;
        DispatchSizeY = 1;
        DispatchSizeZ = 1;
    }
    pass FlexAgX_CurvePass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_CurvePS;
        VertexCount = 3;
        RenderTarget = FA_A;
    }
    pass FlexAgX_HuePass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_HuePS;
        VertexCount = 3;
        RenderTarget = FA_B;
    }
    pass FlexAgX_DetailMeanPass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_DetailMeanPS;
        VertexCount = 3;
        RenderTarget = FA_M;
    }
    pass FlexAgX_DetailBasePass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_DetailBasePS;
        VertexCount = 3;
        RenderTarget = FA_Q;
    }
    pass FlexAgX_DetailApplyPass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_DetailApplyPS;
        VertexCount = 3;
        RenderTarget = FA_D;
    }
    pass FlexAgX_OutputPass
    {
        VertexShader = FlexAgX_FullscreenVS;
        PixelShader = FlexAgX_OutputPS;
        VertexCount = 3;
    }
}