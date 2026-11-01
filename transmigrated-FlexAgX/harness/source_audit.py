"""Pure FX source validator and negative mutation test helpers, not a compiler."""
import re

def pass_names(code):
    return re.findall(r'\bpass (FlexAgX_\w+)\s*\{',code)

def check_corrections(source,reference):
    errors=[]
    old=pass_names(reference);new=pass_names(source)
    if len(old)!=8 or len(new)!=9 or new[0]!='FlexAgX_ClearHistogramPass' or new[1:]!=old:
        errors.append('PASS_ORDER_OR_CARDINALITY')
    try:
        clear=source[source.index('[numthreads(128, 1, 1)]'):source.index('// P1: sampled')]
        if not ('if (id.x < 67u)' in clear and 'tex2Dstore(FA_HistStorage, int2((int)id.x, 0), 0u);' in clear):
            errors.append('CLEAR_COVERAGE')
    except ValueError:errors.append('CLEAR_MISSING')
    try:
        hue=source[source.index('float4 FlexAgX_HuePS'):source.index('// P5:')]
        out=source[source.index('float4 FlexAgX_OutputPS'):source.index('technique FlexAgX')]
        if not ('if (inputChroma >= 1.0e-4)' in hue and hue.index('if (inputChroma >= 1.0e-4)') < hue.index('hIn = atan2(inLab.z, inLab.y)')):
            errors.append('SOURCE_HUE_GUARD')
        if not ('if (curvedChroma > 1.0e-6)' in hue and hue.index('if (curvedChroma > 1.0e-6)')<hue.index('h = atan2(lab.z, lab.y)')):
            errors.append('CURVED_HUE_GUARD')
        if not ('if (C > 1.0e-6)' in out and out.index('if (C > 1.0e-6)')<out.index('h = atan2(b, a)')):
            errors.append('OUTPUT_HUE_GUARD')
    except ValueError:errors.append('HUE_SECTION_MISSING')
    return errors
