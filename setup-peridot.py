#!/usr/bin/env python3
import os
import sys
import re

def create_peridot_config():
    """Create PERIDOT machine configuration for xnu-10063"""
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(base)
    
    # Create PERIDOT machine config header
    peridot_h = """/* Peridot (SM8635) machine config */
#ifndef _PEXPERT_ARM64_PERIDOT_H
#define _PEXPERT_ARM64_PERIDOT_H

#define PERIDOT
#define PERIDOT_BRINGUP
#define ARM_ARCH_TIMER

#define __ARM_ARCH__              8
#define __ARM_VMSA__              8
#define __ARM_VFP__               4
#define __ARM_COHERENT_CACHE__    1
#define __ARM_DEBUG__             7
#define __ARM64_PMAP_SUBPAGE_L1__ 1

/*
 * arm64e on a non-Apple ARMv8.3 CPU: pointer authentication uses the
 * architectural key registers (see HAS_NATIVE_PAC in arm64/pac_asm.h).
 */
#if defined(__arm64e__)
#define HAS_APPLE_PAC             1
#define HAS_NATIVE_PAC            1
#endif

#ifndef ASSEMBLER
#define PLATFORM_PANIC_LOG_DISABLED
#endif /* ! ASSEMBLER */

#endif /* _PEXPERT_ARM64_PERIDOT_H */
"""
    
    peridot_h_path = "pexpert/pexpert/arm64/PERIDOT.h"
    os.makedirs(os.path.dirname(peridot_h_path), exist_ok=True)
    with open(peridot_h_path, "w") as f:
        f.write(peridot_h)
    print(f"Created {peridot_h_path}")

    # Update board_config.h
    board_config_path = "pexpert/pexpert/arm64/board_config.h"
    with open(board_config_path, "r") as f:
        content = f.read()

    if "ARM64_BOARD_CONFIG_PERIDOT" not in content:
        content = content.replace(
            "#endif  /* ARM64_BOARD_CONFIG_BCM2837 */",
            "#endif  /* ARM64_BOARD_CONFIG_BCM2837 */\n\n#ifdef ARM64_BOARD_CONFIG_PERIDOT\n#include <pexpert/arm64/PERIDOT.h>\n\n#define MAX_L2_CLINE                   6\n#define MAX_CPUS                       8 /* SM8635: 1+3+4 cores */\n#define MAX_CPU_CLUSTERS               2\n\n#define PMAP_CS                        1\n#define PMAP_CS_ENABLE                 1\n#define XNU_MONITOR                    1\n#define __ARM_42BIT_PA_SPACE__         1\n#define USE_APPLEARMSMP                1\n#if DEVELOPMENT || DEBUG\n#define XNU_ENABLE_PROCESSOR_EXIT      1\n#endif\n#define XNU_HANDLE_MCC                 1\n#endif  /* ARM64_BOARD_CONFIG_PERIDOT */"
        )
        with open(board_config_path, "w") as f:
            f.write(content)
        print("Updated board_config.h")

    # Update MakeInc.def - brute force approach
    makeinc_path = "makedefs/MakeInc.def"
    with open(makeinc_path, "r") as f:
        content = f.read()

    # Add PERIDOT to SUPPORTED_ARM64_MACHINE_CONFIGS - find any line with SUPPORTED_ARM64_MACHINE_CONFIGS
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        # Add PERIDOT to SUPPORTED_ARM64_MACHINE_CONFIGS
        if 'SUPPORTED_ARM64_MACHINE_CONFIGS' in line and 'PERIDOT' not in line:
            # Replace the line to add PERIDOT
            if 'SUPPORTED_ARM64_MACHINE_CONFIGS' in line:
                line = line.replace('VMAPPLE', 'VMAPPLE PERIDOT')
        new_lines.append(line) if False else None  # placeholder
    
    # Better approach: rebuild the content
    content = '\n'.join([line for line in content.split('\n')])
    content = content.replace(
        'SUPPORTED_ARM64_MACHINE_CONFIGS = BCM2837 T6000 T8101 T8103 VMAPPLE',
        'SUPPORTED_ARM64_MACHINE_CONFIGS = BCM2837 T6000 T8101 T8103 VMAPPLE PERIDOT'
    )
    
    # If exact match not found, try with different spacing
    if 'PERIDOT' not in content:
        content = re.sub(
            r'SUPPORTED_ARM64_MACHINE_CONFIGS\s*=\s*BCM2837\s+T6000\s+T8101\s+T8103\s+VMAPPLE',
            'SUPPORTED_ARM64_MACHINE_CONFIGS = BCM2837 T6000 T8101 T8103 VMAPPLE PERIDOT',
            content
        )
    
    # Add MACHINE_FLAGS for PERIDOT
    if 'MACHINE_FLAGS_ARM64_PERIDOT' not in content:
        content = content.replace(
            'MACHINE_FLAGS_ARM64_VMAPPLE = -DARM64_BOARD_CONFIG_VMAPPLE',
            'MACHINE_FLAGS_ARM64_VMAPPLE = -DARM64_BOARD_CONFIG_VMAPPLE\nMACHINE_FLAGS_ARM64_PERIDOT = -DARM64_BOARD_CONFIG_PERIDOT'
        )
    
    with open("makedefs/MakeInc.def", "w") as f:
        f.write(content)
    print("Updated MakeInc.def")

    # Verify
    with open("makedefs/MakeInc.def", "r") as f:
        verify = f.read()
        if 'PERIDOT' in verify:
            print("VERIFIED: PERIDOT found in MakeInc.def")
        else:
            print("WARNING: PERIDOT NOT FOUND in MakeInc.def!")
            for i, line in enumerate(verify.split('\n'), 1):
                if 'SUPPORTED_ARM64_MACHINE_CONFIGS' in line or 'PERIDOT' in line or 'MACHINE_FLAGS_ARM64' in line:
                    print(f"  Line {i}: {line[:120]}")

if __name__ == "__main__":
    import sys
    import os
    os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
    create_peridot_config()
    print("Peridot machine config added successfully")
