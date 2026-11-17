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

    print("=== Original MakeInc.def (first 50 lines) ===")
    for i, line in enumerate(content.split('\n')[:50]):
        if 'SUPPORTED_ARM64' in line or 'PERIDOT' in line or 'MACHINE_FLAGS' in line or 'SUPPORTED_ARM64' in line:
            print(f"  Line: {line}")

    # Force add PERIDOT to SUPPORTED_ARM64_MACHINE_CONFIGS
    # Find the line with SUPPORTED_ARM64_MACHINE_CONFIGS
    lines = content.split('\n')
    new_lines = []
    found = False
    for line in lines:
        new_lines.append(line)
        if 'SUPPORTED_ARM64_MACHINE_CONFIGS' in line and 'PERIDOT' not in line:
            # Modify this line
            new_lines[-1] = line.replace('VMAPPLE', 'VMAPPLE PERIDOT')
            print(f"Modified SUPPORTED line: {new_lines[-1]}")
            found = True

    content = '\n'.join(new_lines)
    
    # If not found, try regex
    if 'PERIDOT' not in '\n'.join(new_lines):
        content = re.sub(
            r'SUPPORTED_ARM64_MACHINE_CONFIGS\s*=\s*BCM2837\s+T6000\s+T8101\s+T8103\s+VMAPPLE',
            'SUPPORTED_ARM64_MACHINE_CONFIGS = BCM2837 T6000 T8101 T8103 VMAPPLE PERIDOT',
            content
        )
    
    # Add MACHINE_FLAGS for PERIDOT
    if 'MACHINE_FLAGS_ARM64_PERIDOT' not in '\n'.join(new_lines):
        content = re.sub(
            r'(MACHINE_FLAGS_ARM64_VMAPPLE\s*=\s*-DARM64_BOARD_CONFIG_VMAPPLE)',
            r'\1\nMACHINE_FLAGS_ARM64_PERIDOT = -DARM64_BOARD_CONFIG_PERIDOT',
            '\n'.join(new_lines)
        )

    with open(makeinc_path, "w") as f:
        f.write(content)
    print("Updated MakeInc.def")

    # Verify
    with open(makeinc_path, "r") as f:
        verify = f.read()
        if 'PERIDOT' in verify:
            print("VERIFIED: PERIDOT found in MakeInc.def")
        else:
            print("WARNING: PERIDOT NOT FOUND in MakeInc.def!")
            for i, line in enumerate(verify.split('\n'), 1):
                if 'SUPPORTED_ARM64' in line or 'PERIDOT' in line or 'MACHINE_FLAGS' in line:
                    print(f"  Line {i}: {line[:150]}")

if __name__ == "__main__":
    import sys
    import os
    os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
    create_peridot_config()
    print("Peridot machine config added successfully")
