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
    # Cold start F18/F32: boot validation must precede any retained histogram
    # use; rejects absent/stale markers and corrupted prior state.
    try:
        state=source[source.index('void FlexAgX_State('):source.index('// P3:')]
        read_prev='tex2Dfetch(FA_HistPrevStorage, int2((int)lane, 0)).r'
        read_state='old0 = tex2Dfetch(FA_StateStorage, int2(0, 0));'
        if not ('Format = RGBA32F' in source[source.index('texture2D FA_TemporalBoot'):source.index('storage2D FA_TemporalBootStorage')]
                and 'float4 stamp = tex2Dfetch(FA_TemporalBootStorage, int2(0, 0));' in state
                and 'FA_ColdStart = valid ? 0 : 1;' in state
                and 'stamp.z == (float)(previous & 65535u)' in state
                and 'stamp.w == (float)(previous >> 16u)' in state):
            errors.append('COLD_MARKER_MISSING')
        if not (state.index('FA_ColdStart = valid ? 0 : 1;') < state.index(read_prev)
                and state.index('if (FA_ColdStart != 0)') < state.index(read_prev)
                and 'FA_PrevSh[lane] = currentNorm;' in state):
            errors.append('HISTPREV_BOOT_GUARD_MISSING')
        if not (state.index('float4 old0 = float4(e50, 0.0, firstKnee, 0.0);') < state.index(read_state)
                and state.index('if (FA_ColdStart == 0)') < state.index(read_state)
                and 'all(prior0 == prior0)' in state and 'all(prior1 == prior1)' in state):
            errors.append('STATE_BOOT_GUARD_MISSING')
        if not ('tex2Dstore(FA_TemporalBootStorage, int2(0, 0),' in state and
                state.index('tex2Dstore(FA_StateStorage, int2(1, 0)') < state.index('tex2Dstore(FA_TemporalBootStorage, int2(0, 0)')
                and state.index('tex2Dstore(FA_HistPrevStorage, int2((int)lane, 0)') < state.index('tex2Dstore(FA_TemporalBootStorage, int2(0, 0)')):
            errors.append('BOOT_COMMIT_ORDER_INVALID')
    except ValueError:
        errors.append('TEMPORAL_BOOT_SECTION_MISSING')
    return errors
